"""Forecast calendar dates and instants must survive DST transitions."""
from datetime import datetime, time, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from custom_components.open_meteo_custom.coordinator import (
    OpenMeteoCustomDataUpdateCoordinator,
)


async def parse_times(hass, config_entry, zone_name, start_date, offset, hourly_start=None):
    """Use the real coordinator with the API's fixed-step daily time encoding."""
    fixed_zone = timezone(timedelta(hours=offset))
    start = datetime.combine(start_date, time.min, tzinfo=fixed_zone)
    response = MagicMock()
    response.UtcOffsetSeconds.return_value = int(offset * 3600)
    response.Timezone.return_value = zone_name.encode() if zone_name else None
    response.Current.return_value = None
    daily = response.Daily.return_value
    daily.Time.return_value = int(start.timestamp())
    daily.TimeEnd.return_value = int(start.timestamp()) + 7 * 86400
    daily.Interval.return_value = 86400
    daily.VariablesLength.return_value = 0
    hourly = response.Hourly.return_value
    first_hour = hourly_start or start
    hourly.Time.return_value = int(first_hour.timestamp())
    hourly.TimeEnd.return_value = int(first_hour.timestamp()) + 8 * 3600
    hourly.Interval.return_value = 3600
    hourly.VariablesLength.return_value = 0
    http = MagicMock()
    http.read = AsyncMock(return_value=(4).to_bytes(4, 'little') + b'test')
    session = MagicMock()
    session.get.return_value.__aenter__.return_value = http
    coordinator = OpenMeteoCustomDataUpdateCoordinator(hass, config_entry)
    with (
        patch('custom_components.open_meteo_custom.coordinator.async_get_clientsession', return_value=session),
        patch('custom_components.open_meteo_custom.coordinator.WeatherApiResponse.GetRootAs', return_value=response),
    ):
        return await coordinator._async_update_data()


@pytest.mark.parametrize(('start', 'offset'), [('2026-10-28', -7), ('2026-03-05', -8)])
async def test_daily_calendar_dates_across_dst(hass, mock_config_entry, mock_zone, start, offset):
    """Daily values stay on consecutive local midnights, not 23:00 or 01:00."""
    first = datetime.fromisoformat(start).date()
    data = await parse_times(hass, mock_config_entry, 'America/Los_Angeles', first, offset)
    expected = [datetime.combine(first + timedelta(days=i), time.min,
                                 tzinfo=ZoneInfo('America/Los_Angeles')).isoformat()
                for i in range(7)]
    assert [row['datetime'] for row in data.daily_forecast] == expected


@pytest.mark.parametrize(('start', 'offset'), [('2026-11-01T00:00:00-07:00', -7),
                                              ('2026-03-08T00:00:00-08:00', -8)])
async def test_hourly_dst_preserves_instants(hass, mock_config_entry, mock_zone, start, offset):
    """Fall repeats 01:00 with different offsets; spring skips 02:00."""
    first = datetime.fromisoformat(start)
    data = await parse_times(hass, mock_config_entry, 'America/Los_Angeles', first.date(), offset, first)
    expected = [datetime.fromtimestamp(first.timestamp() + i * 3600,
                                      tz=ZoneInfo('America/Los_Angeles')).isoformat()
                for i in range(8)]
    assert [row['datetime'] for row in data.hourly_forecast] == expected
    assert [datetime.fromisoformat(row['datetime']).timestamp()
            for row in data.hourly_forecast] == [first.timestamp() + i * 3600 for i in range(8)]


@pytest.mark.parametrize(('zone', 'offset'), [('UTC', 0), ('Asia/Kolkata', 5.5), (None, 5.5), ('', 5.5)])
async def test_response_timezone_and_missing_name(hass, mock_config_entry, mock_zone, zone, offset):
    """Use the response's location timezone, with offset fallback if absent."""
    first = datetime.fromisoformat('2026-10-28').date()
    data = await parse_times(hass, mock_config_entry, zone, first, offset)
    tz = ZoneInfo(zone) if zone else timezone(timedelta(hours=offset))
    assert data.daily_forecast[0]['datetime'] == datetime.combine(first, time.min, tzinfo=tz).isoformat()
    assert len(data.daily_forecast) == 7
    assert len(data.hourly_forecast) == 8


async def test_invalid_timezone_keeps_offset_fallback(hass, mock_config_entry, mock_zone):
    first = datetime.fromisoformat('2026-10-28').date()
    data = await parse_times(hass, mock_config_entry, 'Not/A_Timezone', first, 5.5)
    assert data.daily_forecast[0]['datetime'] == '2026-10-28T00:00:00+05:30'


async def test_daily_midnight_transition_keeps_calendar_date(hass, mock_config_entry, mock_zone):
    """A midnight clock change must not shift a daily value to the prior date."""
    first = datetime.fromisoformat('2026-04-02').date()
    data = await parse_times(hass, mock_config_entry, 'America/Santiago', first, -3)
    for i, row in enumerate(data.daily_forecast):
        value = datetime.fromisoformat(row['datetime'])
        assert value.date() == first + timedelta(days=i)
        assert value.time() == time.min
        assert value.utcoffset() == datetime.combine(value.date(), time.min,
                                                    tzinfo=ZoneInfo('America/Santiago')).utcoffset()
