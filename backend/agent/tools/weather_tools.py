"""
Weather Tools — Fetch real-time weather data using wttr.in free API.
No API key required.
"""

import requests
from typing import Optional


def get_weather(city: str = "auto") -> str:
    """
    Fetch current weather for a city using wttr.in API.
    Pass 'auto' or empty to auto-detect location via IP geolocation.
    """
    if not city or city.strip().lower() in ("auto", "current", "here", "my location"):
        city = ""  # wttr.in auto-detects from IP

    city_clean = city.strip()

    try:
        # Use wttr.in format=j1 for JSON weather data
        url = f"https://wttr.in/{city_clean}?format=j1"
        headers = {'User-Agent': 'ChaitanyaKarya/1.0'}
        resp = requests.get(url, headers=headers, timeout=8)

        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current_condition", [{}])[0]
            area = data.get("nearest_area", [{}])[0]

            location = area.get("areaName", [{}])[0].get("value", "Unknown")
            region = area.get("region", [{}])[0].get("value", "")
            country = area.get("country", [{}])[0].get("value", "")
            temp_c = current.get("temp_C", "N/A")
            temp_f = current.get("temp_F", "N/A")
            feels_like_c = current.get("FeelsLikeC", "N/A")
            humidity = current.get("humidity", "N/A")
            desc = current.get("weatherDesc", [{}])[0].get("value", "N/A")
            wind_speed = current.get("windspeedKmph", "N/A")
            wind_dir = current.get("winddir16Point", "")
            uv_index = current.get("uvIndex", "N/A")
            visibility = current.get("visibility", "N/A")
            pressure = current.get("pressure", "N/A")
            cloud_cover = current.get("cloudcover", "N/A")
            precip = current.get("precipMM", "0")

            # Tomorrow forecast
            forecast_section = ""
            weather_list = data.get("weather", [])
            if len(weather_list) >= 2:
                tomorrow = weather_list[1]
                t_max = tomorrow.get("maxtempC", "N/A")
                t_min = tomorrow.get("mintempC", "N/A")
                t_desc = tomorrow.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "N/A") if tomorrow.get("hourly") else "N/A"
                forecast_section = f"\n\n🔮 **Tomorrow's Forecast**: {t_desc}, {t_min}°C – {t_max}°C"

            location_str = f"{location}"
            if region:
                location_str += f", {region}"
            if country:
                location_str += f", {country}"

            result = (
                f"🌤️ **Current Weather for {location_str}**:\n"
                f"• Condition: {desc}\n"
                f"• Temperature: {temp_c}°C / {temp_f}°F (Feels like {feels_like_c}°C)\n"
                f"• Humidity: {humidity}%\n"
                f"• Wind: {wind_speed} km/h {wind_dir}\n"
                f"• UV Index: {uv_index}\n"
                f"• Visibility: {visibility} km\n"
                f"• Pressure: {pressure} hPa\n"
                f"• Cloud Cover: {cloud_cover}%\n"
                f"• Precipitation: {precip} mm"
                f"{forecast_section}"
            )
            return result

        return f"Weather service returned status {resp.status_code} for '{city_clean}'."

    except requests.Timeout:
        return f"Weather request timed out for '{city_clean}'. Please try again."
    except requests.ConnectionError:
        return f"No internet connection — cannot fetch weather for '{city_clean}'."
    except Exception as e:
        return f"Weather fetch error for '{city_clean}': {str(e)}"
