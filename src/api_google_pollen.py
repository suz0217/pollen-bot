“””
Google Pollen API モジュール
東京の花粉データをGoogle Pollen APIから取得する
無料枠: 月5,000コール（1日1回なら余裕）
“””

import requests
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class GooglePollenData:
“”“Google Pollen APIから取得したデータ”””
date: str
# Tree pollen (スギ・ヒノキ含む)
tree_index: int  # 0-5 (None=0, Very Low=1, Low=2, Moderate=3, High=4, Very High=5)
tree_category: str
tree_description: str
# 個別植物データ
cedar_index: int  # スギ (Japanese Cedar)
cedar_category: str
cypress_index: int  # ヒノキ (Cypress/Hinoki)
cypress_category: str
# 健康アドバイス
health_recommendations: list = field(default_factory=list)

# Google API カテゴリ → 日本語マッピング

CATEGORY_JP = {
“None”: “飛散なし”,
“Very Low”: “ごく少ない”,
“Low”: “少ない”,
“Moderate”: “やや多い”,
“High”: “多い”,
“Very High”: “非常に多い”,
}

INDEX_TO_LEVEL = {
0: “飛散なし”,
1: “ごく少ない”,
2: “少ない”,
3: “やや多い”,
4: “多い”,
5: “非常に多い”,
}

def fetch_google_pollen(
lat: float = 35.6762,  # 東京
lng: float = 139.6503,
days: int = 2,
api_key: Optional[str] = None,
) -> Optional[GooglePollenData]:
“””
Google Pollen APIから花粉データを取得

```
API Doc: https://developers.google.com/maps/documentation/pollen/overview
無料枠: 月5,000コール
"""
api_key = api_key or os.environ.get("GOOGLE_POLLEN_API_KEY", "")

if not api_key:
    print("[WARN] GOOGLE_POLLEN_API_KEY not set. Skipping Google Pollen API.")
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

    # 今日のデータ（最初のエントリ）
    today = data["dailyInfo"][0]
    date_info = today.get("date", {})
    date_str = f"{date_info.get('month', '?')}月{date_info.get('day', '?')}日"

    # 花粉タイプ情報を解析
    tree_data = _extract_pollen_type(today, "TREE")
    cedar_data = _extract_plant_species(today, "JAPANESE_CEDAR")  # スギ
    cypress_data = _extract_plant_species(today, "JAPANESE_CYPRESS")  # ヒノキ

    # 健康アドバイス
    recommendations = []
    for ptype in today.get("pollenTypeInfo", []):
        recs = ptype.get("healthRecommendations", [])
        recommendations.extend(recs)

    return GooglePollenData(
        date=date_str,
        tree_index=tree_data.get("index", 0),
        tree_category=tree_data.get("category", "不明"),
        tree_description=tree_data.get("description", ""),
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
```

def _extract_pollen_type(daily_info: dict, type_code: str) -> dict:
“”“花粉タイプ（TREE/GRASS/WEED）情報を抽出”””
for ptype in daily_info.get(“pollenTypeInfo”, []):
if ptype.get(“code”) == type_code:
index_info = ptype.get(“indexInfo”, {})
return {
“index”: index_info.get(“value”, 0),
“category”: CATEGORY_JP.get(index_info.get(“category”, “”), “不明”),
“description”: index_info.get(“indexDescription”, “”),
“in_season”: ptype.get(“inSeason”, False),
}
return {}

def _extract_plant_species(daily_info: dict, species_code: str) -> dict:
“”“個別植物種情報を抽出”””
for ptype in daily_info.get(“pollenTypeInfo”, []):
for plant in ptype.get(“plantInfo”, []):
if plant.get(“code”) == species_code:
index_info = plant.get(“indexInfo”, {})
return {
“index”: index_info.get(“value”, 0),
“category”: CATEGORY_JP.get(index_info.get(“category”, “”), “不明”),
“in_season”: plant.get(“inSeason”, False),
}
return {}

if **name** == “**main**”:
print(”=== Google Pollen API テスト ===”)
result = fetch_google_pollen()
if result:
print(f”日付: {result.date}”)
print(f”樹木全体: {result.tree_category} (index: {result.tree_index})”)
print(f”スギ: {result.cedar_category} (index: {result.cedar_index})”)
print(f”ヒノキ: {result.cypress_category} (index: {result.cypress_index})”)
print(f”アドバイス: {result.health_recommendations[:2]}”)
else:
print(“取得失敗（APIキー未設定の場合は正常）”)
