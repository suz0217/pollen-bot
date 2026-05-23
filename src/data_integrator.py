"""
data_integrator.py

tenki.jp + 環境省WBGTを統合し、
天気・熱中症リスク・紫外線レベルと前日比を算出する。
"""

import os
import json
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from scraper_tenki import get_tenki_data
from api_google_pollen import fetch_heatstroke_data


@dataclass
class IntegratedWeatherData:
    date: str
    day_of_week: str

    heatstroke_level: str
    heatstroke_level_num: int   # 1-5
    heatstroke_diff: str        # "↑↑", "↑", "→", "↓", "↓↓"
    wbgt_max: float             # WBGT値（環境省）

    uv_level: str
    uv_level_num: int           # 1-5
    uv_diff: str

    high_temp: str
    low_temp: str
    wind: str
    weather: str
    rain_chance: str


def _diff_arrow(today: int, yesterday: int) -> str:
    diff = today - yesterday
    if diff >= 2:
        return "↑↑"
    elif diff == 1:
        return "↑"
    elif diff == 0:
        return "→"
    elif diff == -1:
        return "↓"
    else:
        return "↓↓"


HISTORY_FILE = os.getenv("POLLEN_HISTORY_FILE", "weather_history.json")


def _load_history() -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_history(history: dict):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"[WARN] Failed to save history: {e}")


def integrate_data() -> IntegratedWeatherData:
    """
    全データソースを統合して投稿用データを生成する。

    1. tenki.jp: 天気・気温・紫外線・熱中症
    2. 環境省WBGT: 暑さ指数（補完）
    """
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    date_str = now.strftime("%m月%d日")
    day_of_week = "月火水木金土日"[now.weekday()]

    tenki = get_tenki_data()
    wbgt_data = fetch_heatstroke_data()

    # 熱中症レベル（tenki.jpベース、環境省WBGTで補完）
    hs_num = 0
    hs_label = "不明"
    wbgt_max = 0.0

    if tenki and tenki.heatstroke_level_num > 0:
        hs_num = tenki.heatstroke_level_num
        hs_label = tenki.heatstroke_level
        print(f"[INFO] Heatstroke from tenki.jp: {hs_label} ({hs_num}/5)")

    if wbgt_data:
        wbgt_max = wbgt_data.wbgt_max
        if wbgt_data.risk_level_num > hs_num:
            hs_num = wbgt_data.risk_level_num
            hs_label = wbgt_data.risk_level
            print(f"[INFO] Heatstroke upgraded by WBGT: {hs_label} ({hs_num}/5)")

    # 紫外線
    uv_num = 0
    uv_label = "不明"
    if tenki and tenki.uv_level_num > 0:
        uv_num = tenki.uv_level_num
        uv_label = tenki.uv_level
        print(f"[INFO] UV from tenki.jp: {uv_label} ({uv_num}/5)")

    # 天気
    high_temp = tenki.high_temp if tenki else ""
    low_temp = tenki.low_temp if tenki else ""
    wind = tenki.wind if tenki else ""
    weather = tenki.weather_summary if tenki else "不明"
    rain_chance = tenki.rain_chance if tenki else ""

    # 前日比
    history = _load_history()
    yest_hs = history.get("yesterday_heatstroke", 0)
    yest_uv = history.get("yesterday_uv", 0)

    if yest_hs == 0 and yest_uv == 0:
        hs_diff = "→"
        uv_diff = "→"
    else:
        hs_diff = _diff_arrow(hs_num, yest_hs)
        uv_diff = _diff_arrow(uv_num, yest_uv)

    # 今日のデータを履歴に保存
    history["yesterday_heatstroke"] = hs_num
    history["yesterday_uv"] = uv_num
    history["last_update"] = now.strftime("%Y-%m-%d %H:%M")
    _save_history(history)

    # フォールバック
    if hs_num == 0:
        hs_num = 1
        hs_label = "ほぼ安全"

    if uv_num == 0:
        uv_num = 1
        uv_label = "弱い"

    result = IntegratedWeatherData(
        date=date_str,
        day_of_week=day_of_week,
        heatstroke_level=hs_label,
        heatstroke_level_num=hs_num,
        heatstroke_diff=hs_diff,
        wbgt_max=wbgt_max,
        uv_level=uv_label,
        uv_level_num=uv_num,
        uv_diff=uv_diff,
        high_temp=high_temp,
        low_temp=low_temp,
        wind=wind,
        weather=weather,
        rain_chance=rain_chance,
    )

    print(f"[INFO] Final: 熱中症={hs_label}({hs_num}) UV={uv_label}({uv_num}) "
          f"天気={weather} 気温={high_temp}℃")

    return result


if __name__ == "__main__":
    print("=== データ統合テスト ===")
    data = integrate_data()
    print(f"\n--- 統合結果 ---")
    print(f"日付: {data.date}({data.day_of_week})")
    print(f"熱中症: {data.heatstroke_level} ({data.heatstroke_level_num}/5) 前日比{data.heatstroke_diff}")
    print(f"WBGT: {data.wbgt_max}℃")
    print(f"紫外線: {data.uv_level} ({data.uv_level_num}/5) 前日比{data.uv_diff}")
    print(f"天気: {data.weather} / {data.high_temp}℃ / {data.wind}")
