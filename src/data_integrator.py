"""
data_integrator.py

複数データソース（tenki.jp + Google Pollen API）を統合し、
前日比の計算と履歴管理を行う。

これが花粉Botのデータパイプラインの心臓部。
"""

import os
import json
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from scraper_tenki import get_tenki_data
from api_google_pollen import fetch_google_pollen


@dataclass
class IntegratedPollenData:
    date: str
    day_of_week: str

    sugi_level: str
    sugi_level_num: int
    sugi_diff: str          # "↑↑", "↑", "→", "↓", "↓↓"

    hinoki_level: str
    hinoki_level_num: int
    hinoki_diff: str

    high_temp: str
    wind: str
    weather: str


# ── 前日比の記号 ──
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


# ── 履歴ファイル管理 ──
HISTORY_FILE = os.getenv("POLLEN_HISTORY_FILE", "pollen_history.json")


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


def _get_yesterday_levels(history: dict) -> tuple[int, int]:
    """前日の花粉レベルを取得（なければ0）"""
    return (
        history.get("yesterday_sugi", 0),
        history.get("yesterday_hinoki", 0),
    )


def _update_history(history: dict, sugi_num: int, hinoki_num: int):
    """今日のデータを履歴に保存（明日の前日比計算用）"""
    history["yesterday_sugi"] = sugi_num
    history["yesterday_hinoki"] = hinoki_num
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    history["last_update"] = now.strftime("%Y-%m-%d %H:%M")
    _save_history(history)


# ── Google Pollen API のインデックス(0-5) → tenki.jp 互換レベル(1-5) ──
GOOGLE_INDEX_TO_TENKI = {
    0: (0, "飛散なし"),
    1: (1, "少ない"),
    2: (2, "やや多い"),
    3: (3, "多い"),
    4: (4, "非常に多い"),
    5: (5, "極めて多い"),
}


def integrate_data() -> IntegratedPollenData:
    """
    全データソースを統合してツイート用データを生成する。

    データ取得優先度:
    1. tenki.jp スクレイピング（メインソース）
    2. Google Pollen API（スギ/ヒノキ個別データの補完）

    tenki.jp が取得できなければ Google Pollen API のみで動作。
    両方失敗した場合はフォールバック値を使用。
    """
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    date_str = now.strftime("%m月%d日")
    day_of_week = "月火水木金土日"[now.weekday()]

    # ── Step 1: tenki.jp からデータ取得 ──
    tenki = get_tenki_data()

    # ── Step 2: Google Pollen API からデータ取得 ──
    google = fetch_google_pollen()

    # ── Step 3: データ統合 ──
    # スギのレベル決定
    sugi_num = 0
    sugi_label = "不明"

    if google and google.cedar_index > 0:
        # Google API にスギ個別データがある場合
        sugi_num = google.cedar_index
        _, sugi_label = GOOGLE_INDEX_TO_TENKI.get(sugi_num, (0, "不明"))
        print(f"[INFO] Sugi from Google API: {sugi_label} ({sugi_num})")
    if tenki and tenki.pollen_level_num > 0:
        # tenki.jp のデータ（スギ/ヒノキ合算）
        # Google API のスギ個別がない場合、または tenki.jp のほうが高い場合に採用
        if sugi_num == 0 or tenki.pollen_level_num > sugi_num:
            sugi_num = tenki.pollen_level_num
            sugi_label = tenki.pollen_level
            print(f"[INFO] Sugi from tenki.jp: {sugi_label} ({sugi_num})")

    # ヒノキのレベル決定
    hinoki_num = 0
    hinoki_label = "不明"

    if google and google.cypress_index > 0:
        hinoki_num = google.cypress_index
        _, hinoki_label = GOOGLE_INDEX_TO_TENKI.get(hinoki_num, (0, "不明"))
        print(f"[INFO] Hinoki from Google API: {hinoki_label} ({hinoki_num})")
    else:
        # Google API なし → tenki.jp のレベルを少し下げてヒノキとする
        # （3月はスギ主体、ヒノキは3月下旬〜4月がピーク）
        if tenki and tenki.pollen_level_num > 0:
            # スギの1段下をヒノキの目安とする（3月上旬〜中旬の場合）
            if now.month == 3 and now.day <= 20:
                hinoki_num = max(1, tenki.pollen_level_num - 2)
            elif now.month >= 4 or (now.month == 3 and now.day > 20):
                # 3月下旬〜4月はヒノキもピーク
                hinoki_num = max(1, tenki.pollen_level_num - 1)
            else:
                hinoki_num = max(1, tenki.pollen_level_num - 2)

            _, hinoki_label = GOOGLE_INDEX_TO_TENKI.get(hinoki_num, (0, "不明"))
            print(f"[INFO] Hinoki estimated from tenki.jp: {hinoki_label} ({hinoki_num})")

    # ── Step 4: 前日比計算 ──
    history = _load_history()
    yest_sugi, yest_hinoki = _get_yesterday_levels(history)
    sugi_diff = _diff_arrow(sugi_num, yest_sugi)
    hinoki_diff = _diff_arrow(hinoki_num, yest_hinoki)

    # 初回（前日データなし）は「→」にする
    if yest_sugi == 0 and yest_hinoki == 0:
        sugi_diff = "→"
        hinoki_diff = "→"
        print("[INFO] No yesterday data. Using → for diff.")

    # 今日のデータを履歴に保存
    _update_history(history, sugi_num, hinoki_num)

    # ── Step 5: 天気情報 ──
    high_temp = ""
    wind = ""
    weather = ""

    if tenki:
        high_temp = tenki.high_temp or ""
        wind = tenki.wind or ""
        weather = tenki.weather_summary or ""

    # ── Step 6: フォールバック ──
    if sugi_num == 0:
        sugi_num = 1
        sugi_label = "少ない"
        print("[WARN] All sources failed for sugi. Using fallback: 少ない")

    if hinoki_num == 0:
        hinoki_num = 1
        hinoki_label = "少ない"
        print("[WARN] All sources failed for hinoki. Using fallback: 少ない")

    if not weather:
        weather = "不明"
        print("[WARN] Weather data unavailable.")

    # ── 完成 ──
    result = IntegratedPollenData(
        date=date_str,
        day_of_week=day_of_week,
        sugi_level=sugi_label,
        sugi_level_num=sugi_num,
        sugi_diff=sugi_diff,
        hinoki_level=hinoki_label,
        hinoki_level_num=hinoki_num,
        hinoki_diff=hinoki_diff,
        high_temp=high_temp,
        wind=wind,
        weather=weather,
    )

    print(f"[INFO] Final: スギ={sugi_label}({sugi_num}) ヒノキ={hinoki_label}({hinoki_num}) "
          f"天気={weather} 気温={high_temp}℃")

    return result


if __name__ == "__main__":
    print("=== データ統合テスト ===")
    data = integrate_data()
    print(f"\n--- 統合結果 ---")
    print(f"日付: {data.date}({data.day_of_week})")
    print(f"スギ: {data.sugi_level} ({data.sugi_level_num}/5) 前日比{data.sugi_diff}")
    print(f"ヒノキ: {data.hinoki_level} ({data.hinoki_level_num}/5) 前日比{data.hinoki_diff}")
    print(f"天気: {data.weather} / {data.high_temp}℃ / {data.wind}")
