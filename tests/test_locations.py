import asyncio
import sys
from yarl import URL
from aiohttp import ClientSession
from open_meteo import Forecast, OpenMeteo, OpenMeteoError

# List of 5 target locations across the world with specific models
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
        "model": "ukmo_global",
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

async def run_test_for_location(session, client, loc):
    print(f"\n--- Testing location: {loc['name']} ({loc['latitude']}, {loc['longitude']}) ---")
    print(f"Model: {loc['model']}")
    
    # Replicate the query parameters construction inside our coordinator.py
    query_params = {
        "latitude": str(loc["latitude"]),
        "longitude": str(loc["longitude"]),
        "current_weather": "true",
        "hourly": ",".join([
            "relativehumidity_2m",
            "apparent_temperature",
            "pressure_msl",
            "dewpoint_2m",
            "windgusts_10m",
            "cloudcover",
            "temperature_2m",
            "weathercode",
            "precipitation",
        ]),
        "daily": ",".join([
            "weathercode",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "winddirection_10m_dominant",
            "windspeed_10m_max",
        ]),
        "precipitation_unit": "mm",
        "temperature_unit": "celsius",
        "timezone": "UTC",
        "windspeed_unit": "kmh",
    }
    
    if loc["model"] != "best_match":
        query_params["models"] = loc["model"]
        
    url = URL("https://api.open-meteo.com/v1/forecast").with_query(query_params)
    
    try:
        data = await client._request(url=url)
        forecast = Forecast.from_json(data)
        
        # Verify success case
        if not loc["should_succeed"]:
            print(f"❌ Error: Expected failure but request succeeded for {loc['name']}.")
            return False
            
        # Verify required variables are in the response and contain data
        print("✅ API Request: Successful")
        
        # Verify hourly data structures
        assert forecast.hourly is not None, "Hourly data is missing"
        assert forecast.hourly.relative_humidity_2m is not None, "relative_humidity_2m is missing"
        assert forecast.hourly.pressure_msl is not None, "pressure_msl is missing"
        assert forecast.hourly.apparent_temperature is not None, "apparent_temperature is missing"
        assert forecast.hourly.dew_point_2m is not None, "dew_point_2m is missing"
        assert forecast.hourly.wind_gusts_10m is not None, "wind_gusts_10m is missing"
        assert forecast.hourly.cloud_cover is not None, "cloud_cover is missing"
        
        # Check first hourly indices contain numeric values
        h_humidity = forecast.hourly.relative_humidity_2m[0]
        h_pressure = forecast.hourly.pressure_msl[0]
        h_temp = forecast.hourly.temperature_2m[0]
        h_apparent = forecast.hourly.apparent_temperature[0]
        
        print(f"📊 Sample Current Hourly Values:")
        print(f"   - Temp: {h_temp} °C")
        print(f"   - Apparent Temp (Feels Like): {h_apparent} °C")
        print(f"   - Humidity: {h_humidity} %")
        print(f"   - Pressure: {h_pressure} hPa")
        
        # Assertions to ensure non-null data
        assert h_humidity is not None, "Humidity value is None"
        assert h_pressure is not None, "Pressure value is None"
        assert h_temp is not None, "Temperature value is None"
        assert h_apparent is not None, "Apparent temperature value is None"
        
        print(f"✅ Data Verification: All checks passed successfully!")
        return True
        
    except OpenMeteoError as err:
        if not loc["should_succeed"]:
            print(f"✅ Expected Failure: Caught expected OpenMeteoError: '{err}'")
            return True
        else:
            print(f"❌ Error: Failed unexpected with OpenMeteoError: {err}")
            return False
    except Exception as e:
        print(f"❌ Error: Unexpected error: {e}")
        return False

async def main():
    async with ClientSession() as session:
        async with OpenMeteo(session=session) as client:
            success_count = 0
            for loc in TEST_LOCATIONS:
                success = await run_test_for_location(session, client, loc)
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
