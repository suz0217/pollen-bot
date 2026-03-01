# src/data_integrator.py

from dataclasses import dataclass
from datetime import datetime


@dataclass
class IntegratedPollenData:
    date: str
    day_of_week: str

    sugi_level: str
    sugi_level_num: int
    sugi_diff: str

    hinoki_level: str
    hinoki_level_num: int
    hinoki_diff: str

    high_temp: str
    wind: str
    weather: str


def integrate_data() -> IntegratedPollenData:
    """
    仮の統合データ（テスト用）
    本来はAPIやスクレイピング結果をここでまとめる
    """

    today = datetime.now()

    return IntegratedPollenData(
        date=today.strftime("%m月%d日"),
        day_of_week=["月", "火", "水", "木", "金", "土", "日"][today.weekday()],

        sugi_level="5/5",
        sugi_level_num=5,
        sugi_diff="↑",

        hinoki_level="4/5",
        hinoki_level_num=4,
        hinoki_diff="→",

        high_temp="15",
        wind="北風強い",
        weather="晴れ",
    )