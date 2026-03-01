"""
tenki.jp 花粉情報スクレイピングモジュール
東京都千代田区の花粉予報を取得する
"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class TenkiPollenData:
    date: str
    weather: str
    high_temp: str
    low_temp: str
    wind: str
    pollen_level: str
    pollen_level_num: int
    humidity: str
    rain_probability: str
    raw_html_snippet: str


POLLEN_LEVEL_MAP = {
    "少ない": 1,
    "やや多い": 2,
    "多い": 3,
    "非常に多い": 4,
    "極めて多い": 5,
}


def fetch_tenki_pollen(
    url: str = "https://tenki.jp/pollen/3/16/4410/13101/"
) -> Optional[TenkiPollenData]:

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        pollen_level = _extract_pollen_level(soup)
        pollen_level_num = POLLEN_LEVEL_MAP.get(pollen_level, 0)

        weather_data = _extract_weather_data(soup)
        date_str = _extract_date(soup)

        return TenkiPollenData(
            date=date_str,
            weather=weather_data.get("weather", "不明"),
            high_temp=weather_data.get("high_temp", "不明"),
            low_temp=weather_data.get("low_temp", "不明"),
            wind=weather_data.get("wind", "不明"),
            pollen_level=pollen_level,
            pollen_level_num=pollen_level_num,
            humidity=weather_data.get("humidity", "不明"),
            rain_probability=weather_data.get("rain_prob", "不明"),
            raw_html_snippet=str(soup.title) if soup.title else "",
        )

    except Exception as e:
        print(f"[ERROR] tenki.jp scraping failed: {e}")
        return None


def _extract_pollen_level(soup: BeautifulSoup) -> str:
    body_text = soup.get_text()

    for level in ["極めて多い", "非常に多い", "多い", "やや多い", "少ない"]:
        if level in body_text:
            return level

    return "不明"


def _extract_weather_data(soup: BeautifulSoup) -> dict:
    data = {}

    high = soup.select_one(".high-temp .value")
    if high:
        data["high_temp"] = high.get_text(strip=True)

    low = soup.select_one(".low-temp .value")
    if low:
        data["low_temp"] = low.get_text(strip=True)

    weather = soup.select_one(".weather-telop")
    if weather:
        data["weather"] = weather.get_text(strip=True)

    wind = soup.select_one(".wind")
    if wind:
        data["wind"] = wind.get_text(strip=True)

    return data


def _extract_date(soup: BeautifulSoup) -> str:
    text = soup.get_text()
    match = re.search(r"(\d+)月(\d+)日", text)
    if match:
        return f"{match.group(1)}月{match.group(2)}日"
    return ""