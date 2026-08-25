import os
import re
import json
import requests
from datetime import datetime, date

USERNAME = "VTongTV"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
WEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
README_PATH = "README.md"
CONTRIB_PATH = "contributions.svg"

DARK_BG = "#0d1117"
DARK_CELL_EMPTY = "#161b22"
DARK_CELL_LEVELS = ["#0e4429", "#006d32", "#26a641", "#39d353"]
CELL_SIZE = 11
CELL_GAP = 3
CELL_STEP = CELL_SIZE + CELL_GAP
LEFT_MARGIN = 36
TOP_MARGIN = 20
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]

def fetch_contributions(year):
    if not TOKEN:
        return None
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
                color
              }
            }
          }
        }
      }
    }
    """
    variables = {
        "login": USERNAME,
        "from": f"{year}-01-01T00:00:00Z",
        "to": f"{year}-12-31T23:59:59Z" if year < datetime.now().year else f"{datetime.now().isoformat()}Z",
    }
    try:
        r = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers={"Authorization": f"bearer {TOKEN}"},
            timeout=30,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        result = []
        for w in weeks:
            for d in w["contributionDays"]:
                result.append({
                    "date": d["date"],
                    "count": d["contributionCount"],
                    "color": d.get("color", DARK_CELL_EMPTY),
                })
        return result
    except Exception as e:
        print(f"Error fetching {year}: {e}")
        return None

def get_level(count):
    if count == 0:
        return 0
    elif count <= 3:
        return 1
    elif count <= 6:
        return 2
    elif count <= 9:
        return 3
    else:
        return 4

def render_year_svg(days_data, year, y_offset):
    if not days_data:
        return ""
    jan1 = date(year, 1, 1)
    jan1_row = (jan1.weekday() + 1) % 7

    rects = []
    month_positions = {}
    current_month = -1
    col = 0

    for d in days_data:
        dt = date.fromisoformat(d["date"])
        if dt.year != year:
            continue
        doy = (dt - jan1).days
        col = (jan1_row + doy) // 7
        row = (jan1_row + doy) % 7
        level = get_level(d["count"])
        color = DARK_CELL_LEVELS[level - 1] if level > 0 else DARK_CELL_EMPTY
        x = LEFT_MARGIN + col * CELL_STEP
        y = y_offset + TOP_MARGIN + row * CELL_STEP
        rects.append(f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2" ry="2" fill="{color}"/>')

        month = dt.month
        if month != current_month:
            month_positions[month] = x
            current_month = month

    month_labels = []
    for m, mx in month_positions.items():
        month_labels.append(f'<text x="{mx}" y="{y_offset + 13}" font-size="10" fill="#8b949e" font-family="Helvetica,Arial,sans-serif">{MONTH_LABELS[m-1]}</text>')

    day_labels = []
    for row_idx in [1, 3, 5]:
        day_labels.append(f'<text x="2" y="{y_offset + TOP_MARGIN + row_idx * CELL_STEP + 9}" font-size="9" fill="#8b949e" font-family="Helvetica,Arial,sans-serif">{DAY_LABELS[row_idx]}</text>')

    year_label = f'<text x="{LEFT_MARGIN}" y="{y_offset + TOP_MARGIN + 7 * CELL_STEP + 14}" font-size="11" fill="#8b949e" font-family="Helvetica,Arial,sans-serif">{year}</text>'

    total_cols = max(col + 1, 53)
    width = LEFT_MARGIN + total_cols * CELL_STEP

    return "\n".join(month_labels + day_labels + rects + [year_label])

def generate_contributions_svg():
    years = list(range(2024, datetime.now().year + 1))
    years.reverse()
    all_data = {}
    for y in years:
        data = fetch_contributions(y)
        if data:
            all_data[y] = data

    if not all_data:
        return

    total_cols = 53
    svg_width = LEFT_MARGIN + total_cols * CELL_STEP + 10
    year_height = TOP_MARGIN + 7 * CELL_STEP + 20
    svg_height = len(all_data) * year_height + 10

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">')
    parts.append(f'<rect width="{svg_width}" height="{svg_height}" fill="{DARK_BG}" rx="6"/>')
    parts.append('<style>text{font-family:Helvetica,Arial,sans-serif}</style>')

    y_off = 0
    for y in years:
        if y in all_data:
            parts.append(render_year_svg(all_data[y], y, y_off))
            y_off += year_height

    parts.append('</svg>')

    with open(CONTRIB_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"Generated {CONTRIB_PATH}")

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
        return {"temp": temp, "feels": feels, "humidity": humidity, "desc": desc}
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
        pm25 = round(data["list"][0]["components"]["pm2_5"], 1)
        return {"aqi": aqi_val, "label": aqi_labels.get(aqi_val, "unknown"), "pm25": pm25}
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
    generate_contributions_svg()

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
