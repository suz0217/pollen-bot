“””
tenki.jp 花粉情報スクレイピングモジュール
東京都千代田区の花粉予報を取得する
“””

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class TenkiPollenData:
“”“tenki.jpから取得した花粉データ”””
date: str
weather: str
high_temp: str
low_temp: str
wind: str
pollen_level: str  # “少ない”, “やや多い”, “多い”, “非常に多い”, “極めて多い”
pollen_level_num: int  # 1-5
humidity: str
rain_probability: str
raw_html_snippet: str  # デバッグ用

POLLEN_LEVEL_MAP = {
“少ない”: 1,
“やや多い”: 2,
“多い”: 3,
“非常に多い”: 4,
“極めて多い”: 5,
}

def fetch_tenki_pollen(url: str = “https://tenki.jp/pollen/3/16/4410/13101/”) -> Optional[TenkiPollenData]:
“””
tenki.jpから東京都千代田区の花粉情報を取得
URL: https://tenki.jp/pollen/3/16/4410/13101/ (東京都千代田区)
“””
headers = {
“User-Agent”: “Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36”
}

```
try:
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 花粉レベルを取得
    pollen_level = _extract_pollen_level(soup)
    pollen_level_num = POLLEN_LEVEL_MAP.get(pollen_level, 0)

    # 天気情報ページから気温等を取得
    weather_data = _extract_weather_data(soup)

    # 日付
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
```

def _extract_pollen_level(soup: BeautifulSoup) -> str:
“”“花粉レベルテキストを抽出”””
# pollen-levelクラスやテーブルから花粉レベルを取得
# tenki.jpの花粉ページ構造に基づく
selectors = [
“.pollen-index-value”,
“.pollen-telop”,
“.today-pollen .telop”,
“.pollen-area-today .telop”,
]
for sel in selectors:
elem = soup.select_one(sel)
if elem:
text = elem.get_text(strip=True)
for level in POLLEN_LEVEL_MAP:
if level in text:
return level

```
# テーブルやテキスト全体からフォールバック検索
body_text = soup.get_text()
# 最も重いレベルから順にチェック
for level in ["極めて多い", "非常に多い", "多い", "やや多い", "少ない"]:
    if level in body_text:
        return level

return "不明"
```

def _extract_weather_data(soup: BeautifulSoup) -> dict:
“”“天気・気温・風・湿度を抽出”””
data = {}

```
# 気温
high = soup.select_one(".high-temp .value, .high-temp temp")
if high:
    data["high_temp"] = high.get_text(strip=True)

low = soup.select_one(".low-temp .value, .low-temp temp")
if low:
    data["low_temp"] = low.get_text(strip=True)

# 天気
weather = soup.select_one(".weather-telop")
if weather:
    data["weather"] = weather.get_text(strip=True)

# 風
wind = soup.select_one(".wind-telop, .wind")
if wind:
    data["wind"] = wind.get_text(strip=True)

return data
```

def _extract_date(soup: BeautifulSoup) -> str:
“”“日付を抽出”””
date_elem = soup.select_one(”.left-style, .date-text, h2”)
if date_elem:
text = date_elem.get_text(strip=True)
match = re.search(r”(\d+)月(\d+)日”, text)
if match:
return f”{match.group(1)}月{match.group(2)}日”
return “”

def fetch_tenki_weather(url: str = “https://tenki.jp/forecast/3/16/4410/13101/”) -> dict:
“””
tenki.jpから東京都千代田区の天気詳細情報を取得
花粉ページとは別に天気ページからも情報を補完する
“””
headers = {
“User-Agent”: “Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36”
}

```
try:
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    data = {}

    # 今日の天気ブロック
    today = soup.select_one(".today-weather")
    if today:
        # 天気
        telop = today.select_one(".weather-telop")
        if telop:
            data["weather"] = telop.get_text(strip=True)

        # 最高気温
        high = today.select_one(".high-temp .value")
        if high:
            data["high_temp"] = high.get_text(strip=True)

        # 最低気温
        low = today.select_one(".low-temp .value")
        if low:
            data["low_temp"] = low.get_text(strip=True)

        # 降水確率
        rain_probs = today.select(".rain-probability td")
        if rain_probs:
            probs = [td.get_text(strip=True) for td in rain_probs]
            data["rain_probability"] = probs

        # 風向風速
        wind = today.select_one(".wind-blow")
        if wind:
            data["wind"] = wind.get_text(strip=True)

    return data

except Exception as e:
    print(f"[ERROR] tenki.jp weather scraping failed: {e}")
    return {}
```

if **name** == “**main**”:
# テスト実行
print(”=== tenki.jp 花粉情報テスト ===”)
result = fetch_tenki_pollen()
if result:
print(f”日付: {result.date}”)
print(f”花粉レベル: {result.pollen_level} ({result.pollen_level_num}/5)”)
print(f”天気: {result.weather}”)
print(f”最高気温: {result.high_temp}℃”)
else:
print(“取得失敗”)

```
print("\n=== tenki.jp 天気情報テスト ===")
weather = fetch_tenki_weather()
print(weather)
```
