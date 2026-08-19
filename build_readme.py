import os
import re
import requests

USERNAME = "VTongTV"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
WEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
README_PATH = "README.md"

def fetch_pune_weather():
    if not WEATHER_API_KEY:
        return None
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": "Pune,IN", "appid": WEATHER_API_KEY, "units": "metric"},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        humidity = data["main"]["humidity"]
        desc = data["weather"][0]["main"].lower()
        icon_map = {
            "clear": "sun", "clouds": "cloud", "rain": "rain",
            "drizzle": "rain", "thunderstorm": "storm", "mist": "fog",
            "fog": "fog", "haze": "fog", "smoke": "fog",
        }
        icon = icon_map.get(desc.split()[0] if " " in desc else desc, "cloud")
        return {"temp": temp, "feels": feels, "humidity": humidity, "desc": desc, "icon": icon}
    except Exception:
        return None

def fetch_pune_aqi():
    if not WEATHER_API_KEY:
        return None
    try:
        r = requests.get(
            "http://api.openweathermap.org/data/2.5/air_pollution",
            params={"lat": 18.5204, "lon": 73.8567, "appid": WEATHER_API_KEY},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        aqi_val = data["list"][0]["main"]["aqi"]
        aqi_labels = {1: "good", 2: "fair", 3: "moderate", 4: "poor", 5: "hazardous"}
        aqi_colors = {1: "#00ff88", 2: "#aaff00", 3: "#ffaa00", 4: "#ff4444", 5: "#ff0000"}
        pm25 = round(data["list"][0]["components"]["pm2_5"], 1)
        return {"aqi": aqi_val, "label": aqi_labels.get(aqi_val, "unknown"), "color": aqi_colors.get(aqi_val, "#808080"), "pm25": pm25}
    except Exception:
        return None

def build_weather_block(weather, aqi):
    if not weather and not aqi:
        return "<!-- weather data unavailable -->"
    lines = []
    if weather:
        lines.append(f'{weather["temp"]}c ({weather["feels"]}c feels) -- {weather["desc"]} -- {weather["humidity"]}% humidity')
    if aqi:
        lines.append(f'aqi {aqi["aqi"]}/5 ({aqi["label"]}) -- pm2.5 {aqi["pm25"]} ug/m3 -- pune, in')
    return "\n".join(lines)

def replace_section(content, start_marker, end_marker, new_body):
    pattern = re.compile(
        rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
        re.DOTALL,
    )
    replacement = f"{start_marker}\n{new_body}\n{end_marker}"
    return pattern.sub(replacement, content)

def main():
    weather = fetch_pune_weather()
    aqi = fetch_pune_aqi()
    block = build_weather_block(weather, aqi)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    updated = replace_section(
        content,
        "<!-- PUNE-WEATHER:START -->",
        "<!-- PUNE-WEATHER:END -->",
        block,
    )

    if updated != content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("README updated with weather")
    else:
        print("No changes")

if __name__ == "__main__":
    main()
