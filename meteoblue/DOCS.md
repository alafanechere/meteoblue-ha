# Meteoblue Weather Add-on

This add-on integrates Meteoblue weather data into Home Assistant, providing current conditions and detailed forecasts.

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Meteoblue Weather" add-on
3. Get your API key from [Meteoblue](https://www.meteoblue.com/en/api)
4. Configure the add-on with your API key
5. Start the add-on

## Configuration

### Minimum Configuration

```yaml
api_key: "YOUR_METEOBLUE_API_KEY"
```

### Full Configuration Example

```yaml
api_key: "YOUR_METEOBLUE_API_KEY"
latitude: 47.5584
longitude: 7.57327
elevation: 279
update_interval: 30
forecast_days: 7
units:
  temperature: "C"
  windspeed: "ms-1"
  precipitation: "mm"
packages:
  - "current"
  - "basic-1h"
  - "basic-day"
  - "sunmoon"
```

## Configuration Options

### Required

- **api_key** (string): Your Meteoblue API key. Get one at https://www.meteoblue.com/en/api

### Optional

- **latitude** (float): Latitude coordinate. Default: Home Assistant location
- **longitude** (float): Longitude coordinate. Default: Home Assistant location
- **elevation** (integer): Elevation in meters above sea level. Default: Auto-detected
- **update_interval** (integer): Minutes between updates. Default: 30, Range: 5-1440
- **forecast_days** (integer): Number of forecast days to retrieve. Default: 7, Range: 1-7

### Units

- **temperature**: `C` (Celsius) or `F` (Fahrenheit). Default: C
- **windspeed**: `ms-1` (m/s), `kmh` (km/h), `mph` (mph), `kn` (knots), or `bft` (Beaufort). Default: ms-1
- **precipitation**: `mm` (millimeters) or `inch` (inches). Default: mm

### Packages

Select which weather data packages to fetch:

- **current**: Current weather conditions (temperature, wind, humidity)
- **basic-1h**: Hourly forecast for temperature, precipitation, wind
- **basic-day**: Daily forecast with min/max temperatures and totals
- **sunmoon**: Sunrise, sunset, moonrise, moonset, and moon phase
- **agro-1h**: Agricultural data (soil moisture, evapotranspiration)
- **wind**: Detailed wind information including gusts
- **clouds**: Cloud cover information
- **solar**: Solar radiation data

## Sensors Created

The add-on automatically creates the following sensors:

### Current Weather
- `sensor.meteoblue_temperature` - Current temperature
- `sensor.meteoblue_wind_speed` - Current wind speed
- `sensor.meteoblue_wind_direction` - Wind direction in degrees
- `sensor.meteoblue_humidity` - Relative humidity
- `sensor.meteoblue_pictocode` - Weather condition code
- `sensor.meteoblue_is_daylight` - Whether it's currently daytime (0 or 1)

### Daily Forecast (for each day 0-6)
- `sensor.meteoblue_forecast_day_X_temp_max` - Maximum temperature
- `sensor.meteoblue_forecast_day_X_temp_min` - Minimum temperature
- `sensor.meteoblue_forecast_day_X_precipitation` - Total precipitation
- `sensor.meteoblue_forecast_day_X_pictocode` - Weather condition code

### Sun & Moon
- `sensor.meteoblue_sunrise` - Today's sunrise time
- `sensor.meteoblue_sunset` - Today's sunset time
- `sensor.meteoblue_moonrise` - Today's moonrise time
- `sensor.meteoblue_moonset` - Today's moonset time
- `sensor.meteoblue_moon_phase` - Moon phase name (e.g., "full moon")

## Weather Pictocodes

The pictocode values represent different weather conditions:

- 1: Clear sky
- 2: Partly cloudy
- 3: Mostly cloudy
- 4: Overcast
- 5: Fog
- 6: Light rain
- 7: Rain
- 8: Heavy rain
- 9: Thunderstorms
- 10: Light snow
- 11: Snow
- 12: Heavy snow
- 13: Sleet
- 14: Drizzle
- 15: Hail

## Usage Examples

### Display Current Temperature

```yaml
type: entity
entity: sensor.meteoblue_temperature
```

### Create Weather Card

```yaml
type: entities
title: Current Weather
entities:
  - entity: sensor.meteoblue_temperature
    name: Temperature
  - entity: sensor.meteoblue_wind_speed
    name: Wind Speed
  - entity: sensor.meteoblue_humidity
    name: Humidity
```

### Automation: Rain Alert

```yaml
automation:
  - alias: "Rain Alert Tomorrow"
    trigger:
      - platform: numeric_state
        entity_id: sensor.meteoblue_forecast_day_1_precipitation
        above: 5
    action:
      - service: notify.mobile_app
        data:
          message: "Heavy rain expected tomorrow (>5mm)"
          title: "Weather Alert"
```

### Automation: Frost Warning

```yaml
automation:
  - alias: "Frost Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.meteoblue_forecast_day_0_temp_min
        below: 0
    action:
      - service: notify.mobile_app
        data:
          message: "Frost expected tonight - protect your plants!"
```

## API Rate Limits

Meteoblue has the following API limits:

- **Rate limit**: 500 calls per minute (default)
- **Daily quota**: Based on your API plan
- **Recommendation**: Update 2 times per day (morning before work is optimal)

The add-on respects these limits and won't exceed your configured update interval.

## Troubleshooting

### Add-on Won't Start

1. Check the add-on logs (Supervisor → Meteoblue Weather → Log)
2. Verify your API key is correct
3. Ensure your coordinates are valid (latitude: -90 to 90, longitude: -180 to 180)

### No Sensors Appearing

1. Ensure MQTT integration is installed and working
2. Check if Mosquitto broker add-on is running
3. Restart Home Assistant after installing the add-on
4. Check add-on logs for errors

### API Errors

If you see errors like "API returned status 401":
- Your API key is invalid or expired
- Check your API key at https://www.meteoblue.com

If you see "API returned status 429":
- You've exceeded your API rate limit
- Increase the `update_interval` value
- Check your API quota usage

### Incorrect Weather Data

1. Verify your latitude/longitude coordinates are correct
2. Check if elevation is accurate (affects temperature calculations)
3. Ensure the correct timezone is being used

## Getting Your API Key

1. Go to https://www.meteoblue.com/en/api
2. Sign up for an account or log in
3. Choose an API plan (free tier available)
4. Generate an API key
5. Copy the API key into the add-on configuration

## Support

For issues, questions, or feature requests:

- GitHub Issues: https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/issues
- Home Assistant Community: https://community.home-assistant.io/

## Credits

- Weather data provided by [Meteoblue](https://www.meteoblue.com/)
- Add-on created for Home Assistant community

## License

MIT License