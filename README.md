# Meteoblue Weather Add-on for Home Assistant

This add-on integrates Meteoblue weather data into Home Assistant, providing current conditions and detailed forecasts.

## Features

- Current weather conditions
- 7-day hourly forecast
- Daily forecast with min/max values
- Configurable update intervals
- Multiple unit systems (metric/imperial)
- Sun and moon information
- Weather pictograms
- Automatic coordinate detection from Home Assistant

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Meteoblue Weather" add-on
3. Configure the add-on (see Configuration section)
4. Start the add-on

## Configuration

### Basic Configuration

```yaml
api_key: "YOUR_METEOBLUE_API_KEY"
latitude: 47.5584  # Optional, defaults to Home Assistant location
longitude: 7.57327  # Optional, defaults to Home Assistant location
elevation: 279  # Optional, auto-detected if not provided
update_interval: 30  # Minutes between updates (default: 30)
units:
  temperature: "C"  # C or F
  windspeed: "ms-1"  # ms-1, kmh, mph, kn, bft
  precipitation: "mm"  # mm or inch
packages:
  - "basic-1h"  # Hourly basic weather
  - "basic-day"  # Daily aggregates
  - "current"  # Current conditions
  - "sunmoon"  # Sun and moon data
```

### Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `api_key` | Yes | - | Your Meteoblue API key |
| `latitude` | No | HA location | Latitude coordinate |
| `longitude` | No | HA location | Longitude coordinate |
| `elevation` | No | Auto | Elevation in meters |
| `update_interval` | No | 30 | Update frequency in minutes |
| `forecast_days` | No | 7 | Number of forecast days (max 7) |
| `units.temperature` | No | C | Temperature unit (C/F) |
| `units.windspeed` | No | ms-1 | Wind speed unit |
| `units.precipitation` | No | mm | Precipitation unit |
| `packages` | No | See above | Weather data packages to fetch |

### Available Packages

- `current` - Current weather conditions
- `basic-1h` - Hourly forecast (temperature, wind, precipitation)
- `basic-day` - Daily forecast with min/max values
- `sunmoon` - Sunrise, sunset, moonrise, moonset
- `agro-1h` - Agricultural data (soil moisture, evapotranspiration)
- `wind` - Detailed wind data including gusts
- `clouds` - Cloud cover data
- `solar` - Solar radiation data

## Sensors Created

The add-on creates the following sensors in Home Assistant:

### Current Weather
- `sensor.meteoblue_temperature`
- `sensor.meteoblue_wind_speed`
- `sensor.meteoblue_wind_direction`
- `sensor.meteoblue_humidity`
- `sensor.meteoblue_pictocode`
- `sensor.meteoblue_is_daylight`

### Daily Forecast
- `sensor.meteoblue_forecast_day_X_temp_max`
- `sensor.meteoblue_forecast_day_X_temp_min`
- `sensor.meteoblue_forecast_day_X_precipitation`
- `sensor.meteoblue_forecast_day_X_pictocode`

### Sun & Moon
- `sensor.meteoblue_sunrise`
- `sensor.meteoblue_sunset`
- `sensor.meteoblue_moonrise`
- `sensor.meteoblue_moonset`
- `sensor.meteoblue_moon_phase`

## Usage Examples

### Display Current Temperature
```yaml
type: entity
entity: sensor.meteoblue_temperature
```

### Forecast Card
```yaml
type: weather-forecast
entity: weather.meteoblue
show_forecast: true
```

### Automation Example
```yaml
automation:
  - alias: "Rain Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.meteoblue_forecast_day_0_precipitation
        above: 5
    action:
      - service: notify.mobile_app
        data:
          message: "Rain expected today (>5mm)"
```

## API Rate Limits

- Default rate limit: 500 calls per minute
- Recommended: 2 updates per day (morning before work)
- For complex decisions: Check multimodel diagram for optimal timing

## Troubleshooting

### Add-on won't start
- Verify your API key is correct
- Check Home Assistant logs for errors
- Ensure coordinates are valid WGS-84 format

### No sensor updates
- Check update interval setting
- Verify internet connectivity
- Review API quota usage

### Invalid coordinates
- Latitude: -90 to 90
- Longitude: -180 to 180
- Format: Decimal degrees (e.g., 47.5584)

## Support

For issues and feature requests, please visit:
https://github.com/your-repo/meteoblue-ha-addon

## License

MIT License - See LICENSE file for details