import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from custom_components.open_meteo_custom.const import DOMAIN, CONF_MODEL, CONF_UPDATE_INTERVAL, CONF_USE_HA_TIMEZONE
from homeassistant.const import CONF_ZONE

async def test_flow_user_init(hass: HomeAssistant) -> None:
    """Test user step shows schema and correct options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

async def test_flow_user_create_entry(hass: HomeAssistant) -> None:
    """Test creating entry with valid input."""
    # Mock zone search
    hass.states.async_set("zone.home", "zoning", {"friendly_name": "Home"})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.open_meteo_custom.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ZONE: "zone.home",
                CONF_MODEL: "best_match",
                CONF_UPDATE_INTERVAL: "30",
                CONF_USE_HA_TIMEZONE: True,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Home (Best Match (Auto))"
    assert result2["data"] == {
        CONF_ZONE: "zone.home",
        CONF_MODEL: "best_match",
        CONF_UPDATE_INTERVAL: 30,
        CONF_USE_HA_TIMEZONE: True,
    }
    assert len(mock_setup_entry.mock_calls) == 1

async def test_flow_user_duplicate_aborts(hass: HomeAssistant) -> None:
    """Test creating duplicate configuration entry aborts."""
    hass.states.async_set("zone.home", "zoning", {"friendly_name": "Home"})

    # Setup an existing config entry
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="zone.home_best_match",
        data={
            CONF_ZONE: "zone.home",
            CONF_MODEL: "best_match",
            CONF_UPDATE_INTERVAL: 30,
            CONF_USE_HA_TIMEZONE: True,
        },
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ZONE: "zone.home",
            CONF_MODEL: "best_match",
            CONF_UPDATE_INTERVAL: "30",
            CONF_USE_HA_TIMEZONE: True,
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"
