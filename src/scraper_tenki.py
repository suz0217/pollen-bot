import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class TenkiPollenData:
    date: str
    pollen_level: str
    pollen_level_num: int


POLLEN_LEVEL_MAP = {
    "少ない": 1,
    "やや多い": 2,
    "多い": 3,
    "非常に多い": 4,
    "極めて多い": 5,
}


def get_tenki_data(
    url: str = "https://tenki.jp/pollen/3/16/4410/13101/"
) -> Optional[TenkiPollenData]:

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        body_text = soup.get_text()

        pollen_level = "不明"
        for level in ["極めて多い", "非常に多い", "多い", "やや多い", "少ない"]:
            if level in body_text:
                pollen_level = level
                break

        pollen_level_num = POLLEN_LEVEL_MAP.get(pollen_level, 0)

        match = re.search(r"(\d+)月(\d+)日", body_text)
        date_str = f"{match.group(1)}月{match.group(2)}日" if match else ""

        return TenkiPollenData(
            date=date_str,
            pollen_level=pollen_level,
            pollen_level_num=pollen_level_num,
        )

    except Exception as e:
        print(f"[ERROR] tenki scraping failed: {e}")
        return None