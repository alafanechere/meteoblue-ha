#!/usr/bin/env python3
"""Meteoblue Weather Add-on for Home Assistant."""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import paho.mqtt.client as mqtt
from dateutil import parser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CONFIG_PATH = "/data/options.json"
HASSIO_API = "http://supervisor/core/api"
SUPERVISOR_API = "http://supervisor"
METEOBLUE_API = "https://my.meteoblue.com/packages"


async def get_mqtt_config() -> Dict[str, Any]:
    """Get MQTT configuration from Supervisor."""
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise ValueError("SUPERVISOR_TOKEN not found")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SUPERVISOR_API}/services/mqtt", headers=headers) as resp:
            if resp.status != 200:
                raise ValueError(f"Failed to get MQTT config: {resp.status}")
            data = await resp.json()
            mqtt_data = data.get("data", {})
            return {
                "host": mqtt_data.get("host", "core-mosquitto"),
                "port": mqtt_data.get("port", 1883),
                "username": mqtt_data.get("username"),
                "password": mqtt_data.get("password")
            }


class MeteoblueClient:
    """Client for Meteoblue API."""

    def __init__(self, api_key: str, config: Dict[str, Any]):
        """Initialize the client."""
        self.api_key = api_key
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def setup(self):
        """Set up the client."""
        self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the client."""
        if self.session:
            await self.session.close()

    async def get_coordinates(self) -> tuple[float, float, Optional[int]]:
        """Get coordinates from config or Home Assistant."""
        lat = self.config.get("latitude")
        lon = self.config.get("longitude")
        elevation = self.config.get("elevation")

        if lat is None or lon is None:
            # Get from Home Assistant
            token = os.environ.get("SUPERVISOR_TOKEN")
            if not token:
                raise ValueError("Cannot get Home Assistant token")

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            async with self.session.get(f"{HASSIO_API}/config", headers=headers) as resp:
                if resp.status != 200:
                    raise ValueError(f"Failed to get HA config: {resp.status}")
                data = await resp.json()
                lat = data.get("latitude", 0)
                lon = data.get("longitude", 0)
                if not elevation:
                    elevation = data.get("elevation")

        return lat, lon, elevation

    def build_url(self, packages: List[str], lat: float, lon: float, elevation: Optional[int] = None) -> str:
        """Build Meteoblue API URL."""
        package_str = "_".join(packages)
        
        units = self.config.get("units", {})
        temp_unit = units.get("temperature", "C")
        wind_unit = units.get("windspeed", "ms-1")
        precip_unit = units.get("precipitation", "mm")
        
        forecast_days = self.config.get("forecast_days", 7)

        params = [
            f"lat={lat}",
            f"lon={lon}",
            f"apikey={self.api_key}",
            f"format=json",
            f"temperature={temp_unit}",
            f"windspeed={wind_unit}",
            f"precipitationamount={precip_unit}",
            f"forecast_days={forecast_days}",
            f"tz=UTC",
        ]

        if elevation is not None:
            params.append(f"asl={elevation}")

        url = f"{METEOBLUE_API}/{package_str}?{'&'.join(params)}"
        return url

    async def fetch_weather(self) -> Dict[str, Any]:
        """Fetch weather data from Meteoblue."""
        try:
            lat, lon, elevation = await self.get_coordinates()
            packages = self.config.get("packages", ["current", "basic-1h", "basic-day", "sunmoon"])
            
            url = self.build_url(packages, lat, lon, elevation)
            
            logger.info(f"Fetching weather for coordinates: {lat}, {lon}")
            
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"API error {resp.status}: {error_text}")
                    raise ValueError(f"API returned status {resp.status}")
                
                data = await resp.json()
                return data

        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            raise


class HomeAssistantPublisher:
    """Publisher for Home Assistant MQTT discovery."""

    def __init__(self, mqtt_client: mqtt.Client):
        """Initialize the publisher."""
        self.mqtt_client = mqtt_client
        self.device_info = {
            "identifiers": ["meteoblue_weather"],
            "name": "Meteoblue Weather",
            "model": "Weather Station",
            "manufacturer": "Meteoblue",
        }

    def publish_discovery(self, sensor_type: str, name: str, unit: Optional[str] = None,
                         device_class: Optional[str] = None, state_class: Optional[str] = None,
                         icon: Optional[str] = None):
        """Publish MQTT discovery message for a sensor."""
        entity_id = name.lower().replace(" ", "_")
        topic = f"homeassistant/sensor/meteoblue/{entity_id}/config"
        
        config = {
            "name": name,
            "unique_id": f"meteoblue_{entity_id}",
            "state_topic": f"meteoblue/{entity_id}/state",
            "device": self.device_info,
        }
        
        if unit:
            config["unit_of_measurement"] = unit
        if device_class:
            config["device_class"] = device_class
        if state_class:
            config["state_class"] = state_class
        if icon:
            config["icon"] = icon

        self.mqtt_client.publish(topic, json.dumps(config), retain=True)
        logger.debug(f"Published discovery for {name}")

    def publish_state(self, entity_id: str, state: Any):
        """Publish state to MQTT."""
        topic = f"meteoblue/{entity_id}/state"
        self.mqtt_client.publish(topic, str(state))

    def setup_current_sensors(self):
        """Set up current weather sensors."""
        self.publish_discovery("sensor", "Temperature", "°C", "temperature", "measurement", "mdi:thermometer")
        self.publish_discovery("sensor", "Wind Speed", "m/s", None, "measurement", "mdi:weather-windy")
        self.publish_discovery("sensor", "Wind Direction", "°", None, "measurement", "mdi:compass")
        self.publish_discovery("sensor", "Humidity", "%", "humidity", "measurement", "mdi:water-percent")
        self.publish_discovery("sensor", "Pictocode", None, None, None, "mdi:weather-partly-cloudy")
        self.publish_discovery("sensor", "Is Daylight", None, None, None, "mdi:weather-sunny")

    def setup_forecast_sensors(self, days: int):
        """Set up forecast sensors."""
        for day in range(days):
            self.publish_discovery("sensor", f"Forecast Day {day} Temp Max", "°C", "temperature", None, "mdi:thermometer-high")
            self.publish_discovery("sensor", f"Forecast Day {day} Temp Min", "°C", "temperature", None, "mdi:thermometer-low")
            self.publish_discovery("sensor", f"Forecast Day {day} Precipitation", "mm", None, None, "mdi:weather-rainy")
            self.publish_discovery("sensor", f"Forecast Day {day} Pictocode", None, None, None, "mdi:weather-partly-cloudy")

    def setup_sunmoon_sensors(self):
        """Set up sun and moon sensors."""
        self.publish_discovery("sensor", "Sunrise", None, "timestamp", None, "mdi:weather-sunset-up")
        self.publish_discovery("sensor", "Sunset", None, "timestamp", None, "mdi:weather-sunset-down")
        self.publish_discovery("sensor", "Moonrise", None, "timestamp", None, "mdi:moon-waxing-crescent")
        self.publish_discovery("sensor", "Moonset", None, "timestamp", None, "mdi:moon-waning-crescent")
        self.publish_discovery("sensor", "Moon Phase", None, None, None, "mdi:moon-full")

    def publish_current_weather(self, data: Dict[str, Any]):
        """Publish current weather data."""
        current = data.get("data_current", {})
        
        if "temperature" in current:
            self.publish_state("temperature", current["temperature"])
        if "windspeed" in current:
            self.publish_state("wind_speed", current["windspeed"])
        if "winddirection" in current:
            self.publish_state("wind_direction", current["winddirection"])
        if "relativehumidity" in current:
            self.publish_state("humidity", current["relativehumidity"])
        if "pictocode" in current:
            self.publish_state("pictocode", current["pictocode"])
        if "isdaylight" in current:
            self.publish_state("is_daylight", current["isdaylight"])

    def publish_forecast(self, data: Dict[str, Any]):
        """Publish forecast data."""
        forecast = data.get("data_day", {})
        
        if not forecast:
            return

        times = forecast.get("time", [])
        for i, time in enumerate(times):
            if "temperature_max" in forecast and i < len(forecast["temperature_max"]):
                self.publish_state(f"forecast_day_{i}_temp_max", forecast["temperature_max"][i])
            if "temperature_min" in forecast and i < len(forecast["temperature_min"]):
                self.publish_state(f"forecast_day_{i}_temp_min", forecast["temperature_min"][i])
            if "precipitation" in forecast and i < len(forecast["precipitation"]):
                self.publish_state(f"forecast_day_{i}_precipitation", forecast["precipitation"][i])
            if "pictocode" in forecast and i < len(forecast["pictocode"]):
                self.publish_state(f"forecast_day_{i}_pictocode", forecast["pictocode"][i])

    def publish_sunmoon(self, data: Dict[str, Any]):
        """Publish sun and moon data."""
        sunmoon = data.get("data_day", {})
        
        if not sunmoon or not sunmoon.get("time"):
            return

        # Get today's data (first element)
        if "sunrise" in sunmoon and sunmoon["sunrise"]:
            self.publish_state("sunrise", sunmoon["sunrise"][0])
        if "sunset" in sunmoon and sunmoon["sunset"]:
            self.publish_state("sunset", sunmoon["sunset"][0])
        if "moonrise" in sunmoon and sunmoon["moonrise"]:
            self.publish_state("moonrise", sunmoon["moonrise"][0])
        if "moonset" in sunmoon and sunmoon["moonset"]:
            self.publish_state("moonset", sunmoon["moonset"][0])
        if "moonphasename" in sunmoon and sunmoon["moonphasename"]:
            self.publish_state("moon_phase", sunmoon["moonphasename"][0])


async def main():
    """Main function."""
    logger.info("Starting Meteoblue Weather Add-on")

    # Load configuration
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    api_key = config.get("api_key")
    if not api_key:
        logger.error("API key not configured")
        sys.exit(1)

    update_interval = config.get("update_interval", 30) * 60  # Convert to seconds

    # Get MQTT configuration from Supervisor
    try:
        mqtt_config = await get_mqtt_config()
        logger.info(f"Got MQTT config: host={mqtt_config['host']}, port={mqtt_config['port']}")
    except Exception as e:
        logger.error(f"Failed to get MQTT configuration: {e}")
        sys.exit(1)

    # Set up MQTT with callback API v2
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if mqtt_config.get("username"):
        mqtt_client.username_pw_set(mqtt_config["username"], mqtt_config.get("password"))
    
    try:
        mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
        mqtt_client.loop_start()
        logger.info("Connected to MQTT broker")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT: {e}")
        sys.exit(1)

    # Set up publisher
    publisher = HomeAssistantPublisher(mqtt_client)
    
    # Set up Meteoblue client
    client = MeteoblueClient(api_key, config)
    await client.setup()

    # Set up sensors
    publisher.setup_current_sensors()
    publisher.setup_forecast_sensors(config.get("forecast_days", 7))
    publisher.setup_sunmoon_sensors()

    logger.info("Sensors configured")

    # Main loop
    try:
        while True:
            try:
                logger.info("Fetching weather data...")
                weather_data = await client.fetch_weather()
                
                # Publish data
                if "data_current" in weather_data:
                    publisher.publish_current_weather(weather_data)
                
                if "data_day" in weather_data:
                    publisher.publish_forecast(weather_data)
                    publisher.publish_sunmoon(weather_data)
                
                logger.info("Weather data updated successfully")
                
            except Exception as e:
                logger.error(f"Error updating weather: {e}")

            # Wait for next update
            await asyncio.sleep(update_interval)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await client.close()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())