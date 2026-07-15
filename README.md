# Open-Meteo Custom Integration for Home Assistant

This custom integration removes the data limits of the default Home Assistant Open-Meteo integration. It fetches the most detailed weather data supported by the Open-Meteo API and allows users to manually select their preferred weather forecast models (e.g., DWD ICON Europe, ECMWF, GFS) directly from the configuration UI.

---

## ✨ Features

1. **Extended Weather Entity:** In addition to the standard weather card properties, it exposes the following real-time data as state attributes:
   * Relative Humidity (`humidity`)
   * Atmospheric Pressure (`native_pressure`)
   * Apparent Temperature (Feels Like) (`native_apparent_temperature`)
   * Dew Point (`native_dew_point`)
   * Cloud Coverage (`cloud_coverage`)
   * Wind Gust Speed (`native_wind_gust_speed`)
   * *Hourly and daily forecast data structures have been expanded to include all of these new attributes as well.*

2. **Standalone Sensors (Platform: Sensor):** For easy charting (history graphs) and automations, independent sensor entities are created for each variable:
   * `sensor.[zone]_humidity` (Humidity - %)
   * `sensor.[zone]_pressure` (Pressure - hPa)
   * `sensor.[zone]_apparent_temperature` (Apparent Temperature - °C)
   * `sensor.[zone]_dew_point` (Dew Point - °C)
   * `sensor.[zone]_cloud_cover` (Cloud Cover - %)
   * `sensor.[zone]_wind_gust` (Wind Gust - km/h)

3. **Advanced Forecast Model Selection:** During configuration, you can choose from the following forecast models instead of relying on the default blended `best_match` logic:
   * **DWD ICON Europe** (7 km resolution - Highly recommended for Europe/Turkey)
   * **DWD ICON Global** (13 km resolution)
   * **ECMWF IFS** (Global 25/9 km resolution)
   * **GFS Global** (28/13 km resolution)
   * **Météo-France Seamless** (2 km resolution)
   * **GEM Seamless** (Canada 25/10/2.5 km resolution)
   * **UKMO Seamless** (UK / Global 10/2 km resolution)

4. **Multi-Model Setup Support:** You can set up multiple integration instances for the same Home Assistant Zone using different forecast models. This allows you to compare different weather models side-by-side on your dashboards!

5. **Dynamic Day/Night Icons:** Correctly maps clear sky conditions to `sunny` during the day and `clear-night` (moon icon) at night for both current conditions and hourly forecasts, matching the API's astronomical day/night calculations.

---

## 🛠️ Installation Guide

Choose one of the following methods to install the custom integration on your Home Assistant server.

### Method A: Installation via HACS (Easiest & Recommended)

If you have the Home Assistant Community Store (HACS) installed, follow these steps to manage and update the integration automatically:

1. Open **HACS** from the Home Assistant sidebar.
2. Click the **three dots** in the top-right corner and select **Custom repositories**.
3. In the dialog box:
   * **Repository:** `https://github.com/iosmand/ha-open-meteo-custom`
   * **Category:** Select `Integration`.
   * Click **Add**.
4. Find the **Open-Meteo Custom** integration in the HACS list and click **Download** in the bottom-right corner.
5. Restart Home Assistant (**Developer Tools > YAML > Restart**).

---

### Method B: Manual Installation (Standard HA Systems)

If you have SSH/Terminal access or a file manager (like File Editor or Samba share) configured on your server:

1. Download the `custom_components/open_meteo_custom` folder from this repository.
2. Navigate to your Home Assistant `/config/` directory.
3. If it does not exist, create a folder named `custom_components`.
4. Copy the `open_meteo_custom` folder inside `custom_components`. The file structure must look like this:
   ```text
   config/
   └── custom_components/
       └── open_meteo_custom/
           ├── __init__.py
           ├── const.py
           ├── config_flow.py
           ├── coordinator.py
           ├── weather.py
           ├── sensor.py
           ├── manifest.json
           └── translations/
               ├── en.json
               └── tr.json
   ```
5. Restart Home Assistant.

---

### Method C: Installation on Docker Container

If you are running Home Assistant inside a Docker container (e.g., on a Synology NAS, Unraid, or standalone Linux VPS):

#### Option 1: Copy via Volume Map (Recommended)
You have likely bound a directory on your host machine to `/config` in the container (e.g., `-v /home/user/homeassistant:/config`).
1. Go to `/home/user/homeassistant/` on your host machine.
2. Locate the `custom_components` directory (create it if missing) and paste the `open_meteo_custom` folder inside.
3. Restart the container:
   ```bash
   docker restart <container_name_or_id>
   ```

#### Option 2: Copy via `docker cp` Command
If you don't have access to the host's volume directory, you can copy the files directly into the running container:
1. Download the repository to your host machine and open a terminal inside it.
2. Run the copy command (replace `<container_name>` with your actual container name or ID):
   ```bash
   docker cp custom_components/open_meteo_custom <container_name>:/config/custom_components/
   ```
3. Restart the container to apply changes:
   ```bash
   docker restart <container_name>
   ```

---

## ⚙️ Activating the Integration

Once the files are installed and Home Assistant is restarted:

1. Go to **Settings > Devices & Services** in the Home Assistant UI.
2. Click **Add Integration** in the bottom-right corner.
3. Search for **"Open-Meteo Custom"** and select it.
4. In the configuration dialog:
   * **Zone:** Choose the location you want to retrieve weather data for (e.g., Home).
   * **Forecast Model:** Choose your preferred model (e.g., **DWD ICON Europe** for highly accurate European forecasts).
5. Click **Submit** to complete the setup. The weather entity and sensor entities will appear in your Home Assistant within seconds.
