"""Weather data generator and API integration."""

import random
from datetime import datetime, timedelta
from typing import Any

import httpx

from data_generation.config import GenerationConfig, MAJOR_CITIES


class WeatherGenerator:
    """Generate or fetch weather data for locations."""

    # Weather conditions and their impact on delivery
    WEATHER_CONDITIONS = [
        {"condition": "clear", "delay_probability": 0.02, "delay_hours": 0},
        {"condition": "partly_cloudy", "delay_probability": 0.03, "delay_hours": 0},
        {"condition": "cloudy", "delay_probability": 0.05, "delay_hours": 0},
        {"condition": "light_rain", "delay_probability": 0.10, "delay_hours": 1},
        {"condition": "rain", "delay_probability": 0.20, "delay_hours": 2},
        {"condition": "heavy_rain", "delay_probability": 0.35, "delay_hours": 4},
        {"condition": "thunderstorm", "delay_probability": 0.50, "delay_hours": 6},
        {"condition": "snow", "delay_probability": 0.40, "delay_hours": 4},
        {"condition": "heavy_snow", "delay_probability": 0.70, "delay_hours": 12},
        {"condition": "ice", "delay_probability": 0.80, "delay_hours": 24},
        {"condition": "fog", "delay_probability": 0.15, "delay_hours": 2},
        {"condition": "extreme_heat", "delay_probability": 0.10, "delay_hours": 1},
        {"condition": "extreme_cold", "delay_probability": 0.25, "delay_hours": 3},
    ]

    # Seasonal weather patterns by region
    SEASONAL_PATTERNS = {
        "northeast": {
            "winter": ["snow", "heavy_snow", "ice", "cloudy", "clear"],
            "spring": ["rain", "light_rain", "cloudy", "partly_cloudy", "clear"],
            "summer": ["clear", "partly_cloudy", "thunderstorm", "extreme_heat"],
            "fall": ["cloudy", "rain", "light_rain", "clear", "partly_cloudy"],
        },
        "southeast": {
            "winter": ["clear", "partly_cloudy", "rain", "light_rain"],
            "spring": ["thunderstorm", "rain", "partly_cloudy", "clear"],
            "summer": ["extreme_heat", "thunderstorm", "partly_cloudy", "clear"],
            "fall": ["clear", "partly_cloudy", "light_rain", "rain"],
        },
        "midwest": {
            "winter": ["snow", "heavy_snow", "extreme_cold", "cloudy", "clear"],
            "spring": ["thunderstorm", "rain", "cloudy", "partly_cloudy"],
            "summer": ["clear", "thunderstorm", "extreme_heat", "partly_cloudy"],
            "fall": ["cloudy", "rain", "clear", "partly_cloudy"],
        },
        "south": {
            "winter": ["clear", "partly_cloudy", "light_rain", "cloudy"],
            "spring": ["thunderstorm", "rain", "clear", "partly_cloudy"],
            "summer": ["extreme_heat", "thunderstorm", "clear", "partly_cloudy"],
            "fall": ["clear", "partly_cloudy", "light_rain"],
        },
        "west": {
            "winter": ["rain", "snow", "cloudy", "fog", "clear"],
            "spring": ["rain", "light_rain", "cloudy", "clear", "partly_cloudy"],
            "summer": ["clear", "extreme_heat", "partly_cloudy"],
            "fall": ["clear", "fog", "partly_cloudy", "light_rain"],
        },
    }

    def __init__(self, config: GenerationConfig):
        self.config = config
        random.seed(config.random_seed)

    def generate(self, locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate synthetic weather data for locations over the date range."""
        weather_records = []

        # Generate daily weather for each location
        current_date = self.config.start_date.date()
        end_date = self.config.end_date.date()

        while current_date <= end_date:
            for location in locations:
                # Only generate for hubs/distribution centers
                if location["location_type"] not in ["hub", "distribution_center"]:
                    continue

                weather = self._generate_weather_for_location(location, current_date)
                weather_records.append(weather)

            current_date += timedelta(days=1)

        return weather_records

    def _generate_weather_for_location(
        self, location: dict[str, Any], date: datetime.date
    ) -> dict[str, Any]:
        """Generate weather for a specific location and date."""
        region = location.get("region", "midwest")
        season = self._get_season(date)

        # Get possible conditions for this region and season
        possible_conditions = self.SEASONAL_PATTERNS.get(region, {}).get(
            season, ["clear", "partly_cloudy", "cloudy"]
        )

        # Select condition with bias toward clear/normal weather
        condition = random.choice(possible_conditions)

        # Get condition details
        condition_info = next(
            (c for c in self.WEATHER_CONDITIONS if c["condition"] == condition),
            self.WEATHER_CONDITIONS[0],
        )

        # Generate temperature based on season and region
        temp_ranges = {
            ("northeast", "winter"): (15, 35),
            ("northeast", "spring"): (40, 65),
            ("northeast", "summer"): (70, 90),
            ("northeast", "fall"): (45, 65),
            ("southeast", "winter"): (35, 55),
            ("southeast", "spring"): (55, 75),
            ("southeast", "summer"): (80, 100),
            ("southeast", "fall"): (55, 75),
            ("midwest", "winter"): (5, 30),
            ("midwest", "spring"): (40, 65),
            ("midwest", "summer"): (70, 95),
            ("midwest", "fall"): (40, 60),
            ("south", "winter"): (40, 60),
            ("south", "spring"): (60, 80),
            ("south", "summer"): (85, 105),
            ("south", "fall"): (60, 80),
            ("west", "winter"): (40, 60),
            ("west", "spring"): (55, 75),
            ("west", "summer"): (75, 100),
            ("west", "fall"): (55, 75),
        }

        temp_min, temp_max = temp_ranges.get((region, season), (50, 70))
        temperature = random.uniform(temp_min, temp_max)

        # Adjust for condition
        if "snow" in condition or "ice" in condition:
            temperature = min(temperature, 32)
        elif "extreme_cold" in condition:
            temperature = random.uniform(-10, 20)
        elif "extreme_heat" in condition:
            temperature = max(temperature, 95)

        return {
            "location_id": location["location_id"],
            "date": date.isoformat(),
            "condition": condition,
            "temperature_f": round(temperature, 1),
            "humidity_pct": random.randint(20, 95),
            "wind_speed_mph": random.uniform(0, 35),
            "precipitation_in": self._get_precipitation(condition),
            "visibility_miles": self._get_visibility(condition),
            "delay_probability": condition_info["delay_probability"],
            "expected_delay_hours": condition_info["delay_hours"],
        }

    def _get_season(self, date: datetime.date) -> str:
        """Determine season from date."""
        month = date.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"

    def _get_precipitation(self, condition: str) -> float:
        """Get precipitation amount based on condition."""
        precip_map = {
            "clear": 0,
            "partly_cloudy": 0,
            "cloudy": 0,
            "fog": 0,
            "light_rain": random.uniform(0.01, 0.25),
            "rain": random.uniform(0.25, 1.0),
            "heavy_rain": random.uniform(1.0, 3.0),
            "thunderstorm": random.uniform(0.5, 2.0),
            "snow": random.uniform(0.5, 4.0),
            "heavy_snow": random.uniform(4.0, 12.0),
            "ice": random.uniform(0.1, 0.5),
            "extreme_heat": 0,
            "extreme_cold": 0,
        }
        return round(precip_map.get(condition, 0), 2)

    def _get_visibility(self, condition: str) -> float:
        """Get visibility in miles based on condition."""
        visibility_map = {
            "clear": 10.0,
            "partly_cloudy": 10.0,
            "cloudy": 8.0,
            "fog": random.uniform(0.1, 1.0),
            "light_rain": random.uniform(5.0, 8.0),
            "rain": random.uniform(3.0, 6.0),
            "heavy_rain": random.uniform(1.0, 3.0),
            "thunderstorm": random.uniform(2.0, 5.0),
            "snow": random.uniform(1.0, 4.0),
            "heavy_snow": random.uniform(0.25, 1.0),
            "ice": random.uniform(2.0, 5.0),
            "extreme_heat": 8.0,
            "extreme_cold": 10.0,
        }
        return round(visibility_map.get(condition, 10.0), 1)

    async def fetch_real_weather(
        self, latitude: float, longitude: float, date: datetime.date
    ) -> dict[str, Any] | None:
        """Fetch real weather data from Open-Meteo API (free, no API key required)."""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "auto",
            "start_date": date.isoformat(),
            "end_date": date.isoformat(),
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                daily = data.get("daily", {})
                if daily:
                    weather_code = daily.get("weathercode", [0])[0]
                    return {
                        "date": date.isoformat(),
                        "temperature_max_f": self._celsius_to_fahrenheit(
                            daily.get("temperature_2m_max", [70])[0]
                        ),
                        "temperature_min_f": self._celsius_to_fahrenheit(
                            daily.get("temperature_2m_min", [50])[0]
                        ),
                        "precipitation_in": round(
                            daily.get("precipitation_sum", [0])[0] / 25.4, 2
                        ),
                        "condition": self._weather_code_to_condition(weather_code),
                    }
        except Exception:
            return None

        return None

    def _celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return round(celsius * 9 / 5 + 32, 1)

    def _weather_code_to_condition(self, code: int) -> str:
        """Convert WMO weather code to condition string."""
        # WMO Weather interpretation codes
        code_map = {
            0: "clear",
            1: "partly_cloudy",
            2: "partly_cloudy",
            3: "cloudy",
            45: "fog",
            48: "fog",
            51: "light_rain",
            53: "rain",
            55: "heavy_rain",
            61: "light_rain",
            63: "rain",
            65: "heavy_rain",
            71: "snow",
            73: "snow",
            75: "heavy_snow",
            77: "snow",
            80: "rain",
            81: "heavy_rain",
            82: "heavy_rain",
            85: "snow",
            86: "heavy_snow",
            95: "thunderstorm",
            96: "thunderstorm",
            99: "thunderstorm",
        }
        return code_map.get(code, "clear")
