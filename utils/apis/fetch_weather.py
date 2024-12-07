import requests_cache
import retry_requests
import openmeteo_requests
from utils.error_data import WeatherDataError
import datetime as dt


log = open("./local/data/log.txt", "w")

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry_requests.retry(
    cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

URL = "https://api.open-meteo.com/v1/forecast"

wcs = {
    "0n": "clear-night",
    "0d": "clear-day",
    "1n": "cloudy-1-night",
    "1d": "cloudy-1-day",
    "2n": "cloudy-2-night",
    "2d": "cloudy-2-day",
    "3": "cloudy",
    "45n": "fog-night",
    "45d": "fog-day",
    "48": "fog",
    "51": "rainy-1",
    "53": "rainy-2",
    "55": "rainy-3",
    "56": "rainy-1",
    "57": "rainy-3",
    "61": "rainy-1",
    "63": "rainy-2",
    "65": "rainy-3",
    "66": "rainy-1",
    "67": "rainy-3",
    "71": "snowy-1",
    "73": "snowy-2",
    "75": "snowy-3",
    "77": "snowy-1",
    "80": "rainy-3",
    "81": "rainy-3",
    "82": "rainy-3",
    "85": "snowy-3",
    "86": "snowy-3",
    "95": "thunderstorms"
}


def process_change(interval_name, lat, lon):

    if interval_name == '10 дней':
        return daily_weather_request(lat, lon)
    else:
        return hourly_weather_request(interval_name, lat, lon)


def hourly_weather_request(interval_name, lat, lon):
    global wcs, URL, log
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "surface_pressure", "wind_speed_10m", "weather_code"],
        "forecast_days": 4,
        "past_days": 1,
        "timezone": "auto"
    }

    response = openmeteo.weather_api(URL, params=params)[0]
    log.write(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}\n")
    hourly = response.Hourly()
    weather_data = {
        "temperature": list(hourly.Variables(0).ValuesAsNumpy()),
        "humidity": list(hourly.Variables(1).ValuesAsNumpy()),
        "apparent_temperature": list(hourly.Variables(2).ValuesAsNumpy()),
        "precipitation": list(hourly.Variables(3).ValuesAsNumpy()),
        "pressure": list(hourly.Variables(4).ValuesAsNumpy()),
        "wind": list(hourly.Variables(5).ValuesAsNumpy()),
        "weather_code": list(hourly.Variables(6).ValuesAsNumpy())
    }
    hours = list()
    if interval_name == 'Сейчас':
        time_h_now = dt.datetime.now().hour
        log.write(f"Time now(UTC): {time_h_now}\n")
        for i in range(-2, 8):
            hours.append(time_h_now + i + 24)
    elif interval_name == 'Сегодня':
        for i in range(26, 47, 2):
            hours.append(i)
        hours = hours[:10:]
    elif interval_name == 'Завтра':
        for i in range(50, 72, 2):
            hours.append(i)
        hours = hours[:10:]
    elif interval_name == '3 дня':
        for i in range(9):
            hours.append(8*i + 24)
        hours.append(23+24*2)

    return_data = dict()
    for i in range(len(hours)):
        tmp = list()
        for key, value in weather_data.items():
            if key == 'temperature':
                tmp.append(
                    f"{f'{value[hours[i]]:.2f}{chr(176)}C'.rstrip('0').rstrip('.')}"
                )
            elif key == 'apparent_temperature':
                tmp.append(f"{value[hours[i]]:.2f}{chr(176)}C")
            elif key == 'precipitation':
                tmp.append(f"{value[hours[i]]:.2f} мм")
            elif key == 'pressure':
                tmp.append(f"{value[hours[i]]:.2f} кПа")
            elif key == 'wind':
                tmp.append(f"{value[hours[i]]:.2f} м/с")
            elif key == 'humidity':
                tmp.append(f"{value[hours[i]]:.2f}%")

        return_data[hours[i]] = '\n'.join(tmp)
    if return_data is None:
        raise WeatherDataError("Ответ от api.open-meteo.com пуст.")

    return_icons = list()
    dl = ".\\source\\icons\\weather\\"

    for h in hours:
        wc = str(int(weather_data['weather_code'][h]))
        if wc == "0" or wc == "1" or wc == "2" or wc == "45":
            if 6 < h % 24 < 22:
                wc += "d"
            else:
                wc += "n"
        return_icons.append(dl + wcs[wc] + ".svg")

    return [return_data, return_icons]


def daily_weather_request(lat, lon):
    global URL, wcs
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["weather_code", "temperature_2m_min", "temperature_2m_max", "apparent_temperature_min", "apparent_temperature_max", "precipitation_sum", "wind_speed_10m_max"],
        "forecast_days": 14,
        "timezone": "auto"
    }
    response = openmeteo.weather_api(URL, params=params)[0]
    daily = response.Daily()
    weather_data = {
        'weather_code': daily.Variables(0).ValuesAsNumpy(),
        'temperature_min': daily.Variables(1).ValuesAsNumpy(),
        'temperature_max': daily.Variables(2).ValuesAsNumpy(),
        'apparent_temperature_min': daily.Variables(3).ValuesAsNumpy(),
        'apparent_temperature_max': daily.Variables(4).ValuesAsNumpy(),
        'precipitation': daily.Variables(5).ValuesAsNumpy(),
        'wind': daily.Variables(6).ValuesAsNumpy()
    }
    
    return_data = dict()
    return_icons = list()
    for i in range(10):
        tmp = list()
        for key, value in weather_data.items():
            if key == 'temperature_min':
                tmp.append(
                    f"{f'{value[i]:.2f}{chr(176)}C'.rstrip('0').rstrip('.')}"
                )
            elif key == 'temperature_max':
                tmp[0] += " -- " + f"{value[i]:.2f}{chr(176)}C"
            elif key == 'apparent_temperature_min':
                tmp.append("-")
                tmp.append(f"{value[i]:.2f}{chr(176)}C")
            elif key == 'apparent_temperature_max':
                tmp[2] += " -- " + f"{value[i]:.2f}{chr(176)}C"
            elif key == 'precipitation':
                tmp.append(f"{value[i]:.2f} мм")
            elif key == 'wind':
                tmp.append("-")
                tmp.append(f"{value[i]:.2f} м/с")

        return_data[i] = '\n'.join(tmp)

        dl = ".\\source\\icons\\weather\\"
        wc = str(int(weather_data['weather_code'][i]))
        if wc == "0" or wc == "1" or wc == "2" or wc == "45":
            wc += "d"
        return_icons.append(dl + wcs[wc] + ".svg")

    return [return_data, return_icons]
