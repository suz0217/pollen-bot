"""
scraper_tenki.py

tenki.jp から東京（千代田区）の花粉飛散レベルと天気情報を取得する。

データ取得元:
  花粉: https://tenki.jp/pollen/3/16/4410/13101/  (千代田区の花粉ページ)
  天気: https://tenki.jp/forecast/3/16/4410/13101/ (千代田区の天気ページ)

花粉レベル:
  「少ない」「やや多い」「多い」「非常に多い」「極めて多い」の5段階
"""

import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional


@dataclass
class TenkiPollenData:
    """tenki.jp から取得した花粉＋天気データ"""
    pollen_level: str        # 「少ない」〜「極めて多い」
    pollen_level_num: int    # 1〜5
    high_temp: str           # 最高気温（例: "15"）
    low_temp: str            # 最低気温（例: "8"）
    rain_chance: str         # 降水確率（例: "90%"）
    weather_summary: str     # 簡易天気（雨 / 曇り / 晴れ）
    wind: str                # 風情報


# tenki.jp の花粉レベル → 数値マッピング
POLLEN_LEVEL_MAP = {
    "少ない": 1,
    "やや多い": 2,
    "多い": 3,
    "非常に多い": 4,
    "極めて多い": 5,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _rain_to_weather(rain_str: str) -> str:
    """降水確率の文字列から天気を推定"""
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
    """ページ取得の共通処理"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None


def _extract_pollen_level(soup: BeautifulSoup) -> tuple[str, int]:
    """花粉レベルを抽出（優先度の高い順に探す）"""
    body_text = soup.get_text(separator=" ")

    # 千代田区の花粉レベルを特定する
    # tenki.jp では「千代田区」の直後に花粉レベルが表示される
    chiyoda_idx = body_text.find("千代田区")
    if chiyoda_idx >= 0:
        # 千代田区の後ろ100文字以内でレベルを探す
        nearby = body_text[chiyoda_idx:chiyoda_idx + 100]
        for level in ["極めて多い", "非常に多い", "多い", "やや多い", "少ない"]:
            if level in nearby:
                return level, POLLEN_LEVEL_MAP[level]

    # フォールバック: ページ全体から最高レベルを探す
    for level in ["極めて多い", "非常に多い", "多い", "やや多い", "少ない"]:
        if level in body_text:
            return level, POLLEN_LEVEL_MAP[level]

    return "不明", 0


def _extract_weather_info(soup: BeautifulSoup) -> dict:
    """天気情報（気温・降水確率・風）を抽出"""
    body_text = soup.get_text(separator=" ")
    result = {"high_temp": "", "low_temp": "", "rain_chance": "", "wind": ""}

    # 千代田区付近のテキストから気温を探す
    chiyoda_idx = body_text.find("千代田区")
    if chiyoda_idx >= 0:
        nearby = body_text[chiyoda_idx:chiyoda_idx + 200]
        temp_match = re.search(r"(\d+)℃\s*/\s*(\d+)℃", nearby)
        if temp_match:
            result["high_temp"] = temp_match.group(1)
            result["low_temp"] = temp_match.group(2)

        rain_match = re.search(r"(\d+)\s*%", nearby)
        if rain_match:
            result["rain_chance"] = f"{rain_match.group(1)}%"

    # 千代田区付近で見つからない場合はページ全体から
    if not result["high_temp"]:
        temp_match = re.search(r"(\d+)℃\s*/\s*(\d+)℃", body_text)
        if temp_match:
            result["high_temp"] = temp_match.group(1)
            result["low_temp"] = temp_match.group(2)

    if not result["rain_chance"]:
        rain_match = re.search(r"(\d+)\s*%", body_text)
        if rain_match:
            result["rain_chance"] = f"{rain_match.group(1)}%"

    # 風情報
    wind_match = re.search(
        r"(北風|南風|東風|西風|北西の風|北東の風|南西の風|南東の風)[^\n]*?(強い|やや強い|弱い)?",
        body_text,
    )
    if wind_match:
        result["wind"] = wind_match.group(0).strip()

    return result


def get_tenki_data(
    pollen_url: str = "https://tenki.jp/pollen/3/16/4410/13101/",
) -> Optional[TenkiPollenData]:
    """
    tenki.jp の千代田区花粉ページからデータを取得

    Returns:
        TenkiPollenData: 取得成功時
        None: 取得失敗時
    """
    print("[INFO] Fetching tenki.jp pollen data...")

    soup = _fetch_page(pollen_url)
    if not soup:
        return None

    # 花粉レベル
    pollen_level, pollen_level_num = _extract_pollen_level(soup)
    print(f"[INFO] Pollen level: {pollen_level} ({pollen_level_num}/5)")

    # 天気情報（花粉ページにも気温・降水確率が載っている）
    weather_info = _extract_weather_info(soup)

    # 天気推定
    weather_summary = _rain_to_weather(weather_info["rain_chance"])

    return TenkiPollenData(
        pollen_level=pollen_level,
        pollen_level_num=pollen_level_num,
        high_temp=weather_info["high_temp"],
        low_temp=weather_info["low_temp"],
        rain_chance=weather_info["rain_chance"],
        weather_summary=weather_summary,
        wind=weather_info["wind"],
    )


if __name__ == "__main__":
    print("=== tenki.jp 花粉データ取得テスト ===")
    data = get_tenki_data()
    if data:
        print(f"花粉レベル: {data.pollen_level} ({data.pollen_level_num}/5)")
        print(f"気温: {data.high_temp}℃ / {data.low_temp}℃")
        print(f"降水確率: {data.rain_chance}")
        print(f"天気: {data.weather_summary}")
        print(f"風: {data.wind}")
    else:
        print("取得失敗")
