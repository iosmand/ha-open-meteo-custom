import asyncio
import sys
from datetime import datetime, timezone, timedelta
from yarl import URL
from aiohttp import ClientSession
from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse

TEST_LOCATIONS = [
    {
        "name": "Izmir, Turkey",
        "latitude": 38.5163,
        "longitude": 27.0475,
        "model": "dwd_icon_eu",
        "should_succeed": True
    },
    {
        "name": "New York, USA",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "model": "gfs_global",
        "should_succeed": True
    },
    {
        "name": "Tokyo, Japan",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "model": "best_match",
        "should_succeed": True
    },
    {
        "name": "London, UK",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "model": "ukmo_seamless",
        "should_succeed": True
    },
    {
        "name": "Sydney, Australia",
        "latitude": -33.8688,
        "longitude": 151.2093,
        "model": "best_match",
        "should_succeed": True
    },
    # Negative test case (ICON Europe model requested in USA - should fail gracefully)
    {
        "name": "New York, USA (Invalid Model Test)",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "model": "dwd_icon_eu",
        "should_succeed": False
    }
]

_CURRENT_MAP = [
    "weather_code", "is_day", "cloud_cover", "relative_humidity_2m", 
    "apparent_temperature", "dew_point_2m", "pressure_msl", 
    "temperature_2m", "visibility", "wind_gusts_10m", 
    "wind_speed_10m", "uv_index", "wind_direction_10m"
]

_DAILY_MAP = [
    "weather_code", "cloud_cover_mean", "relative_humidity_2m_mean", 
    "apparent_temperature_mean", "dew_point_2m_mean", "precipitation_sum", 
    "pressure_msl_mean", "temperature_2m_max", "temperature_2m_min", 
    "wind_gusts_10m_max", "wind_speed_10m_max", "precipitation_probability_max", 
    "uv_index_max", "wind_direction_10m_dominant"
]

_HOURLY_MAP = [
    "weather_code", "is_day", "cloud_cover", "relative_humidity_2m", 
    "apparent_temperature", "dew_point_2m", "precipitation", 
    "pressure_msl", "temperature_2m", "wind_gusts_10m", 
    "wind_speed_10m", "precipitation_probability", "uv_index", 
    "wind_direction_10m"
]

async def run_test_for_location(session, loc):
    print(f"\n--- Testing location: {loc['name']} ({loc['latitude']}, {loc['longitude']}) ---")
    print(f"Model: {loc['model']}")
    
    params = {
        "latitude": str(loc["latitude"]),
        "longitude": str(loc["longitude"]),
        "current": ",".join(_CURRENT_MAP),
        "daily": ",".join(_DAILY_MAP),
        "hourly": ",".join(_HOURLY_MAP),
        "forecast_hours": "168",
        "format": "flatbuffers",
        "precipitation_unit": "mm",
        "temperature_unit": "celsius",
        "timezone": "UTC",
        "wind_speed_unit": "kmh",
    }
    
    if loc["model"] != "best_match":
        params["models"] = loc["model"]
        
    url = URL("https://api.open-meteo.com/v1/forecast").with_query(params)
    
    try:
        async with session.get(url) as response:
            if not loc["should_succeed"]:
                # If we expect it to fail, checking status code
                if response.status >= 400:
                    print(f"✅ Expected Failure: API returned status {response.status}")
                    return True
                else:
                    print(f"❌ Error: Expected failure but request succeeded with status {response.status}")
                    return False
            
            response.raise_for_status()
            data = await response.read()
            
        print("✅ API Request: Successful")
        
        # Parse the FlatBuffers data
        total = len(data)
        assert total >= 4, "Malformed response header"
        length = int.from_bytes(data[:4], byteorder="little")
        assert length > 0 and length <= total - 4, "Malformed frame length"
        
        api_response = WeatherApiResponse.GetRootAs(data, 4)
        
        # Verify current weather
        current = api_response.Current()
        assert current is not None, "Current weather data is missing"
        
        # index 3 is relative_humidity_2m in current map
        h_humidity = current.Variables(3).Value()
        # index 6 is pressure_msl
        h_pressure = current.Variables(6).Value()
        # index 7 is temperature_2m
        h_temp = current.Variables(7).Value()
        # index 4 is apparent_temperature
        h_apparent = current.Variables(4).Value()
        
        print(f"📊 Sample Current Values:")
        print(f"   - Temp: {h_temp} °C")
        print(f"   - Apparent Temp (Feels Like): {h_apparent} °C")
        print(f"   - Humidity: {h_humidity} %")
        print(f"   - Pressure: {h_pressure} hPa")
        
        assert h_humidity is not None, "Humidity value is None"
        assert h_pressure is not None, "Pressure value is None"
        assert h_temp is not None, "Temperature value is None"
        assert h_apparent is not None, "Apparent temperature value is None"
        
        # Verify daily forecast exists
        daily = api_response.Daily()
        assert daily is not None, "Daily forecast is missing"
        assert daily.VariablesLength() > 0, "Daily variables are empty"
        
        # Verify hourly forecast exists
        hourly = api_response.Hourly()
        assert hourly is not None, "Hourly forecast is missing"
        assert hourly.VariablesLength() > 0, "Hourly variables are empty"
        
        print(f"✅ Data Verification: All checks passed successfully!")
        return True
        
    except Exception as e:
        if not loc["should_succeed"]:
            print(f"✅ Expected Failure: Caught expected exception: '{e}'")
            return True
        else:
            print(f"❌ Error: Unexpected error: {e}")
            return False

async def main():
    async with ClientSession() as session:
        success_count = 0
        for loc in TEST_LOCATIONS:
            success = await run_test_for_location(session, loc)
            if success:
                success_count += 1
        
        print(f"\n======================================")
        print(f"Test Summary: {success_count}/{len(TEST_LOCATIONS)} tests passed.")
        print(f"======================================")
        
        if success_count == len(TEST_LOCATIONS):
            print("🎉 All integration tests passed successfully!")
            sys.exit(0)
        else:
            print("❌ Some integration tests failed.")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
