“””
データ統合モジュール
tenki.jp と Google Pollen API のデータを統合し、
前日比を算出する
“””

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional

from scraper_tenki import fetch_tenki_pollen, fetch_tenki_weather, TenkiPollenData
from api_google_pollen import fetch_google_pollen, GooglePollenData

HISTORY_FILE = os.environ.get(“POLLEN_HISTORY_FILE”, “pollen_history.json”)

@dataclass
class IntegratedPollenData:
“”“統合花粉データ”””
date: str
day_of_week: str

```
# 花粉レベル（統合後）
sugi_level: str       # スギ花粉レベル（日本語）
sugi_level_num: int   # 1-5
hinoki_level: str     # ヒノキ花粉レベル（日本語）
hinoki_level_num: int # 1-5

# 前日比
sugi_diff: str    # "↑", "↑↑", "↓", "↓↓", "→"
hinoki_diff: str  # 同上

# 気象データ
weather: str
high_temp: str
low_temp: str
wind: str
humidity: str
rain_probability: str

# メタ
data_sources: list  # ["tenki.jp", "google_pollen"]
confidence: str     # "high", "medium", "low"
```

# tenki.jp レベル → 数値

TENKI_LEVEL_TO_NUM = {
“少ない”: 1,
“やや多い”: 2,
“多い”: 3,
“非常に多い”: 4,
“極めて多い”: 5,
}

# Google Pollen index → 日本語レベル

GOOGLE_INDEX_TO_JP = {
0: “飛散なし”,
1: “少ない”,
2: “少ない”,
3: “やや多い”,
4: “多い”,
5: “非常に多い”,
}

# 統合レベル数値 → 日本語

NUM_TO_JP = {
0: “飛散なし”,
1: “少ない”,
2: “やや多い”,
3: “多い”,
4: “非常に多い”,
5: “極めて多い”,
}

DAY_OF_WEEK_JP = [“月”, “火”, “水”, “木”, “金”, “土”, “日”]

def integrate_data() -> Optional[IntegratedPollenData]:
“””
全データソースから取得・統合し、IntegratedPollenDataを返す
“””
sources = []

```
# 1. tenki.jp からデータ取得
tenki_pollen = fetch_tenki_pollen()
tenki_weather = fetch_tenki_weather()

if tenki_pollen:
    sources.append("tenki.jp")

# 2. Google Pollen API からデータ取得
google_pollen = fetch_google_pollen()
if google_pollen:
    sources.append("google_pollen")

if not tenki_pollen and not google_pollen:
    print("[ERROR] No data sources available")
    return None

# 3. データ統合
now = datetime.now()
date_str = f"{now.month}/{now.day}"
dow = DAY_OF_WEEK_JP[now.weekday()]

# スギレベル統合
sugi_num = _integrate_sugi_level(tenki_pollen, google_pollen)
sugi_level = NUM_TO_JP.get(sugi_num, "不明")

# ヒノキレベル統合
hinoki_num = _integrate_hinoki_level(google_pollen)
hinoki_level = NUM_TO_JP.get(hinoki_num, "不明")

# 前日比計算
yesterday = _load_yesterday_data()
sugi_diff = _calc_diff(sugi_num, yesterday.get("sugi_level_num", 0) if yesterday else None)
hinoki_diff = _calc_diff(hinoki_num, yesterday.get("hinoki_level_num", 0) if yesterday else None)

# 気象データ統合
weather = tenki_weather.get("weather", "不明") if tenki_weather else "不明"
high_temp = tenki_weather.get("high_temp", "?") if tenki_weather else "?"
low_temp = tenki_weather.get("low_temp", "?") if tenki_weather else "?"
wind = tenki_weather.get("wind", "不明") if tenki_weather else "不明"
humidity = tenki_weather.get("humidity", "不明") if tenki_weather else "不明"
rain_prob = ""
if tenki_weather and "rain_probability" in tenki_weather:
    rain_prob = "/".join(tenki_weather["rain_probability"])

# 信頼度
confidence = "high" if len(sources) >= 2 else ("medium" if len(sources) == 1 else "low")

result = IntegratedPollenData(
    date=date_str,
    day_of_week=dow,
    sugi_level=sugi_level,
    sugi_level_num=sugi_num,
    hinoki_level=hinoki_level,
    hinoki_level_num=hinoki_num,
    sugi_diff=sugi_diff,
    hinoki_diff=hinoki_diff,
    weather=weather,
    high_temp=high_temp,
    low_temp=low_temp,
    wind=wind,
    humidity=humidity,
    rain_probability=rain_prob,
    data_sources=sources,
    confidence=confidence,
)

# 今日のデータを保存（明日の前日比計算用）
_save_today_data(result)

return result
```

def _integrate_sugi_level(tenki: Optional[TenkiPollenData], google: Optional[GooglePollenData]) -> int:
“””
スギ花粉レベルを統合
tenki.jpは全体の花粉レベル（スギ+ヒノキ混合）
Google Pollen APIはスギ個別のindexがある
→ 両方ある場合は高い方を採用（安全側に倒す）
“””
levels = []

```
if tenki and tenki.pollen_level_num > 0:
    levels.append(tenki.pollen_level_num)

if google and google.cedar_index > 0:
    # Google: 0-5 → tenki互換の 1-5 にマッピング
    mapped = min(google.cedar_index, 5)
    levels.append(mapped)

if not levels:
    return 0

# 安全側：高い方を採用
return max(levels)
```

def _integrate_hinoki_level(google: Optional[GooglePollenData]) -> int:
“””
ヒノキ花粉レベル
Google Pollen APIのcypress_indexを使用
tenki.jpはスギヒノキ混合なのでヒノキ単独は取れない
“””
if google and google.cypress_index > 0:
return min(google.cypress_index, 5)

```
# Google APIが使えない場合、時期から推定
now = datetime.now()
# ヒノキは3月下旬〜5月がシーズン
if now.month == 3 and now.day >= 20:
    return 2  # やや多い
elif now.month == 4:
    return 3  # 多い
elif now.month == 5 and now.day <= 15:
    return 2
else:
    return 1  # 少ない
```

def _calc_diff(today_num: int, yesterday_num: Optional[int]) -> str:
“”“前日比を計算”””
if yesterday_num is None:
return “—”  # 前日データなし

```
diff = today_num - yesterday_num

if diff >= 2:
    return "↑↑"
elif diff == 1:
    return "↑"
elif diff == 0:
    return "→"
elif diff == -1:
    return "↓"
else:  # diff <= -2
    return "↓↓"
```

def _load_yesterday_data() -> Optional[dict]:
“”“前日のデータをJSONファイルから読み込む”””
try:
if os.path.exists(HISTORY_FILE):
with open(HISTORY_FILE, “r”, encoding=“utf-8”) as f:
history = json.load(f)

```
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return history.get(yesterday)
except Exception as e:
    print(f"[WARN] Failed to load history: {e}")

return None
```

def _save_today_data(data: IntegratedPollenData):
“”“今日のデータをJSONファイルに保存”””
try:
history = {}
if os.path.exists(HISTORY_FILE):
with open(HISTORY_FILE, “r”, encoding=“utf-8”) as f:
history = json.load(f)

```
    today_key = datetime.now().strftime("%Y-%m-%d")
    history[today_key] = {
        "sugi_level_num": data.sugi_level_num,
        "hinoki_level_num": data.hinoki_level_num,
        "high_temp": data.high_temp,
        "weather": data.weather,
    }

    # 直近7日分だけ保持
    keys = sorted(history.keys())
    if len(keys) > 7:
        for old_key in keys[:-7]:
            del history[old_key]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

except Exception as e:
    print(f"[WARN] Failed to save history: {e}")
```

if **name** == “**main**”:
print(”=== データ統合テスト ===”)
result = integrate_data()
if result:
print(f”日付: {result.date}({result.day_of_week})”)
print(f”スギ: {result.sugi_level} (前日比{result.sugi_diff})”)
print(f”ヒノキ: {result.hinoki_level} (前日比{result.hinoki_diff})”)
print(f”天気: {result.weather} 最高{result.high_temp}℃”)
print(f”データソース: {result.data_sources}”)
print(f”信頼度: {result.confidence}”)
else:
print(“統合失敗”)
