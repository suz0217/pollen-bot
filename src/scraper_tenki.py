"""
scraper_tenki.py

tenki.jp から東京（千代田区）の天気・紫外線・熱中症情報を取得する。

データ取得元:
  天気:    https://tenki.jp/forecast/3/16/4410/13101/
  紫外線:  https://tenki.jp/uv/3/16/4410/13101/
  熱中症:  https://tenki.jp/heatstroke/3/16/4410/13101/
"""

import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional


@dataclass
class TenkiWeatherData:
    """tenki.jp から取得した天気+紫外線+熱中症データ"""
    high_temp: str
    low_temp: str
    rain_chance: str
    weather_summary: str
    wind: str
    uv_level: str          # 「弱い」「やや強い」「強い」「非常に強い」「極端に強い」
    uv_level_num: int      # 1-5
    heatstroke_level: str   # 「ほぼ安全」「注意」「警戒」「厳重警戒」「危険」
    heatstroke_level_num: int  # 0-5


UV_LEVEL_MAP = {
    "弱い": 1,
    "中程度": 2,
    "強い": 3,
    "非常に強い": 4,
    "極端に強い": 5,
}

HEATSTROKE_LEVEL_MAP = {
    "ほぼ安全": 1,
    "注意": 2,
    "警戒": 3,
    "厳重警戒": 4,
    "危険": 5,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _rain_to_weather(rain_str: str) -> str:
    try:
        num = int(re.sub(r"[^\d]", "", rain_str))
        if num >= 70:
            return "雨"
        elif num >= 40:
            return "曇り時々雨"
        elif num >= 20:
            return "曇り"
        else:
            return "晴れ"
    except (ValueError, TypeError):
        return "不明"


def _fetch_page(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None


def _extract_weather_info(soup: BeautifulSoup) -> dict:
    body_text = soup.get_text(separator=" ")
    result = {"high_temp": "", "low_temp": "", "rain_chance": "", "wind": ""}

    chiyoda_idx = body_text.find("千代田区")
    if chiyoda_idx >= 0:
        nearby = body_text[chiyoda_idx:chiyoda_idx + 300]
        temp_match = re.search(r"(\d+)℃\s*/\s*(\d+)℃", nearby)
        if temp_match:
            result["high_temp"] = temp_match.group(1)
            result["low_temp"] = temp_match.group(2)

        rain_match = re.search(r"(\d+)\s*%", nearby)
        if rain_match:
            result["rain_chance"] = f"{rain_match.group(1)}%"

    if not result["high_temp"]:
        temp_match = re.search(r"(\d+)℃\s*/\s*(\d+)℃", body_text)
        if temp_match:
            result["high_temp"] = temp_match.group(1)
            result["low_temp"] = temp_match.group(2)

    if not result["rain_chance"]:
        rain_match = re.search(r"(\d+)\s*%", body_text)
        if rain_match:
            result["rain_chance"] = f"{rain_match.group(1)}%"

    wind_match = re.search(
        r"(北風|南風|東風|西風|北西の風|北東の風|南西の風|南東の風)[^\n]*?(強い|やや強い|弱い)?",
        body_text,
    )
    if wind_match:
        result["wind"] = wind_match.group(0).strip()

    return result


def _extract_uv_level(soup: BeautifulSoup) -> tuple[str, int]:
    for a in soup.find_all("a", href=True):
        if "uv_index_ranking" in a["href"]:
            link_text = a.get_text(separator=" ")
            for level in ["極端に強い", "非常に強い", "強い", "中程度", "弱い"]:
                if level in link_text:
                    return level, UV_LEVEL_MAP[level]

    body_text = soup.get_text(separator=" ")
    for level in ["極端に強い", "非常に強い", "強い", "中程度", "弱い"]:
        if level in body_text:
            return level, UV_LEVEL_MAP[level]
    return "不明", 0


def _extract_heatstroke_level(soup: BeautifulSoup) -> tuple[str, int]:
    body_text = soup.get_text(separator=" ")
    for level in ["危険", "厳重警戒", "警戒", "注意", "ほぼ安全"]:
        if level in body_text:
            return level, HEATSTROKE_LEVEL_MAP[level]
    return "不明", 0


def get_tenki_data(
    weather_url: str = "https://tenki.jp/forecast/3/16/4410/13101/",
    heatstroke_url: str = "https://tenki.jp/heatstroke/3/16/4410/13101/",
) -> Optional[TenkiWeatherData]:
    """
    tenki.jp から天気・紫外線・熱中症データを取得

    天気ページにUV情報が含まれるので、UVは天気ページから取得。
    熱中症は専用ページから取得。

    Returns:
        TenkiWeatherData: 取得成功時
        None: 天気データの取得に失敗した場合
    """
    print("[INFO] Fetching tenki.jp weather data...")

    weather_soup = _fetch_page(weather_url)
    if not weather_soup:
        return None

    weather_info = _extract_weather_info(weather_soup)
    weather_summary = _rain_to_weather(weather_info["rain_chance"])

    # 紫外線（天気ページ内のUVリンクから取得）
    uv_level, uv_level_num = _extract_uv_level(weather_soup)
    if uv_level_num > 0:
        print(f"[INFO] UV level: {uv_level} ({uv_level_num}/5)")
    else:
        print("[WARN] UV data not found in weather page")

    # 熱中症
    hs_level, hs_level_num = "不明", 0
    hs_soup = _fetch_page(heatstroke_url)
    if hs_soup:
        hs_level, hs_level_num = _extract_heatstroke_level(hs_soup)
        print(f"[INFO] Heatstroke level: {hs_level} ({hs_level_num}/5)")
    else:
        print("[WARN] Heatstroke page fetch failed")

    return TenkiWeatherData(
        high_temp=weather_info["high_temp"],
        low_temp=weather_info["low_temp"],
        rain_chance=weather_info["rain_chance"],
        weather_summary=weather_summary,
        wind=weather_info["wind"],
        uv_level=uv_level,
        uv_level_num=uv_level_num,
        heatstroke_level=hs_level,
        heatstroke_level_num=hs_level_num,
    )


if __name__ == "__main__":
    print("=== tenki.jp 天気・UV・熱中症 取得テスト ===")
    data = get_tenki_data()
    if data:
        print(f"気温: {data.high_temp}℃ / {data.low_temp}℃")
        print(f"降水確率: {data.rain_chance}")
        print(f"天気: {data.weather_summary}")
        print(f"風: {data.wind}")
        print(f"紫外線: {data.uv_level} ({data.uv_level_num}/5)")
        print(f"熱中症: {data.heatstroke_level} ({data.heatstroke_level_num}/5)")
    else:
        print("取得失敗")
