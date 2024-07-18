import json, requests, sys


def get_current_weather(location, unit={"fahrenheit"}):
    """Get the current weather in a given location"""

    units = "imperial" if unit == "fahrenheit" else "metric"
    api_key = ""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units={units}"
    res = requests.get(url)

    if res.status_code == 200:
        data = res.json()

        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind = data["wind"]["speed"]
        description = data["weather"][0]["description"]
        temp = data["main"]["temp"]

        return json.dumps(
            {"resend": True, "location": location, "temperature": temp, "unit": unit}
        )

    return json.dumps({"resend": True, "location": location, "temperature": "unknown"})
