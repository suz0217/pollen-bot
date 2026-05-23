"""
api_heatstroke.py (旧 api_google_pollen.py)

環境省 熱中症予防情報サイト (wbgt.env.go.jp) から
WBGT（暑さ指数）を取得する。

データソース: 環境省の暑さ指数予測値（CSV）
対象地点: 東京（地点コード: 44132）
"""

import requests
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")

WBGT_CSV_URL = "https://www.wbgt.env.go.jp/prev15WG/dl/yohou_all.csv"

TOKYO_POINT_CODE = "44132"


@dataclass
class HeatstrokeData:
    """環境省WBGTデータ"""
    date: str
    wbgt_max: float
    risk_level: str       # 「ほぼ安全」「注意」「警戒」「厳重警戒」「危険」
    risk_level_num: int   # 1-5


WBGT_LEVELS = [
    (31, 5, "危険"),
    (28, 4, "厳重警戒"),
    (25, 3, "警戒"),
    (21, 2, "注意"),
    (0,  1, "ほぼ安全"),
]


def _wbgt_to_risk(wbgt: float) -> tuple[int, str]:
    for threshold, num, label in WBGT_LEVELS:
        if wbgt >= threshold:
            return num, label
    return 1, "ほぼ安全"


def fetch_heatstroke_data() -> Optional[HeatstrokeData]:
    """
    環境省WBGTデータを取得。
    CSVが取得できない場合（冬季など）はNoneを返す。
    """
    print("[INFO] Fetching WBGT data from wbgt.env.go.jp...")

    try:
        resp = requests.get(WBGT_CSV_URL, timeout=15)
        resp.raise_for_status()
        resp.encoding = "shift_jis"
        lines = resp.text.strip().split("\n")

        today_str = datetime.now(JST).strftime("%Y%m%d")

        max_wbgt = None
        for line in lines:
            cols = line.split(",")
            if len(cols) < 5:
                continue
            if cols[0].strip() == TOKYO_POINT_CODE and today_str in cols[1].strip():
                try:
                    wbgt_vals = [float(c) for c in cols[3:] if c.strip() and c.strip() != ""]
                    if wbgt_vals:
                        line_max = max(wbgt_vals)
                        if max_wbgt is None or line_max > max_wbgt:
                            max_wbgt = line_max
                except (ValueError, IndexError):
                    continue

        if max_wbgt is None:
            print("[WARN] No WBGT data found for Tokyo today (may be off-season)")
            return None

        risk_num, risk_label = _wbgt_to_risk(max_wbgt)
        now = datetime.now(JST)
        date_str = f"{now.month}月{now.day}日"

        print(f"[INFO] WBGT: {max_wbgt}℃ → {risk_label} ({risk_num}/5)")
        return HeatstrokeData(
            date=date_str,
            wbgt_max=max_wbgt,
            risk_level=risk_label,
            risk_level_num=risk_num,
        )

    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] WBGT HTTP error: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] WBGT fetch failed: {e}")
        return None


if __name__ == "__main__":
    print("=== 環境省 WBGT テスト ===")
    result = fetch_heatstroke_data()
    if result:
        print(f"日付: {result.date}")
        print(f"WBGT最大: {result.wbgt_max}℃")
        print(f"リスク: {result.risk_level} ({result.risk_level_num}/5)")
    else:
        print("取得失敗（オフシーズンの場合は正常）")
