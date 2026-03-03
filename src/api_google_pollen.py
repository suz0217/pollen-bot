"""
api_google_pollen.py

Google Pollen API からスギ・ヒノキの個別花粉データを取得する。
無料枠: 月5,000コール（1日1回なら余裕）

APIキーが設定されていない場合はスキップして None を返す。
tenki.jp のみでも動作する設計。
"""

import os
import requests
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GooglePollenData:
    """Google Pollen API から取得したデータ"""
    date: str
    tree_index: int           # 0-5
    tree_category: str
    cedar_index: int          # スギ (Japanese Cedar) 0-5
    cedar_category: str
    cypress_index: int        # ヒノキ (Cypress) 0-5
    cypress_category: str
    health_recommendations: list = field(default_factory=list)


# Google API カテゴリ → 日本語マッピング
CATEGORY_JP = {
    "None": "飛散なし",
    "Very Low": "ごく少ない",
    "Low": "少ない",
    "Moderate": "やや多い",
    "High": "多い",
    "Very High": "非常に多い",
}


def _extract_pollen_type(daily_info: dict, type_code: str) -> dict:
    """花粉タイプ（TREE/GRASS/WEED）情報を抽出"""
    for ptype in daily_info.get("pollenTypeInfo", []):
        if ptype.get("code") == type_code:
            index_info = ptype.get("indexInfo", {})
            return {
                "index": index_info.get("value", 0),
                "category": CATEGORY_JP.get(index_info.get("category", ""), "不明"),
            }
    return {}


def _extract_plant_species(daily_info: dict, species_code: str) -> dict:
    """個別植物種情報を抽出"""
    for ptype in daily_info.get("pollenTypeInfo", []):
        for plant in ptype.get("plantInfo", []):
            if plant.get("code") == species_code:
                index_info = plant.get("indexInfo", {})
                return {
                    "index": index_info.get("value", 0),
                    "category": CATEGORY_JP.get(index_info.get("category", ""), "不明"),
                }
    return {}


def fetch_google_pollen(
    lat: float = 35.6762,
    lng: float = 139.6503,
    days: int = 2,
    api_key: Optional[str] = None,
) -> Optional[GooglePollenData]:
    """
    Google Pollen API から花粉データを取得

    API Doc: https://developers.google.com/maps/documentation/pollen/overview
    無料枠: 月5,000コール
    """
    api_key = api_key or os.environ.get("GOOGLE_POLLEN_API_KEY", "")

    if not api_key:
        print("[INFO] GOOGLE_POLLEN_API_KEY not set. Skipping Google Pollen API.")
        return None

    url = "https://pollen.googleapis.com/v1/forecast:lookup"
    params = {
        "key": api_key,
        "location.latitude": lat,
        "location.longitude": lng,
        "days": days,
        "languageCode": "ja",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if "dailyInfo" not in data or not data["dailyInfo"]:
            print("[WARN] No daily info in Google Pollen API response")
            return None

        today = data["dailyInfo"][0]
        date_info = today.get("date", {})
        date_str = f"{date_info.get('month', '?')}月{date_info.get('day', '?')}日"

        tree_data = _extract_pollen_type(today, "TREE")
        cedar_data = _extract_plant_species(today, "JAPANESE_CEDAR")
        cypress_data = _extract_plant_species(today, "JAPANESE_CYPRESS")

        recommendations = []
        for ptype in today.get("pollenTypeInfo", []):
            recs = ptype.get("healthRecommendations", [])
            recommendations.extend(recs)

        return GooglePollenData(
            date=date_str,
            tree_index=tree_data.get("index", 0),
            tree_category=tree_data.get("category", "不明"),
            cedar_index=cedar_data.get("index", 0),
            cedar_category=cedar_data.get("category", "不明"),
            cypress_index=cypress_data.get("index", 0),
            cypress_category=cypress_data.get("category", "不明"),
            health_recommendations=recommendations,
        )

    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] Google Pollen API HTTP error: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Google Pollen API failed: {e}")
        return None


if __name__ == "__main__":
    print("=== Google Pollen API テスト ===")
    result = fetch_google_pollen()
    if result:
        print(f"日付: {result.date}")
        print(f"樹木全体: {result.tree_category} (index: {result.tree_index})")
        print(f"スギ: {result.cedar_category} (index: {result.cedar_index})")
        print(f"ヒノキ: {result.cypress_category} (index: {result.cypress_index})")
    else:
        print("取得失敗（APIキー未設定の場合は正常）")
