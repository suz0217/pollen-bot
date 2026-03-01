"""
tweet_generator.py

統合データ（IntegratedPollenData）から X 投稿文を生成する。

要件:
- 地名は「東京」だけ（区は出さない）
- 日付は必ず JST (Asia/Tokyo) で生成（GitHub Actions の UTC でズレないように）
- 文章はリッチ（スギ/ヒノキ/気象/行動3つ/締めの一言/ハッシュタグ）
- まとまりごとに改行はしない（= 全体を詰めて見やすく）
- 「(更新 09:52)」のような更新時刻は出さない
"""

import random
from datetime import datetime
from zoneinfo import ZoneInfo

from data_integrator import IntegratedPollenData


# ----------------------------
# JST固定の日付
# ----------------------------
def _today_jst_str() -> str:
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    dow = "月火水木金土日"[now.weekday()]
    return now.strftime(f"%m月%d日({dow})")


# ----------------------------
# 0-5 を想定（元が文字でも数字に寄せる）
# ----------------------------
def _to_int_level(x, default=0) -> int:
    try:
        if x is None:
            return default
        if isinstance(x, int):
            return x
        s = str(x).strip()
        # "5/5" みたいな形も許容
        if "/" in s:
            s = s.split("/")[0].strip()
        return int(float(s))
    except Exception:
        return default


def _arrow(delta: int) -> str:
    if delta > 0:
        return "↑"
    if delta < 0:
        return "↓"
    return "→"


# ----------------------------
# 行動（3つだけ出す）
# ----------------------------
def _generate_actions(combined: int, wind: str | None) -> list[str]:
    actions: list[str] = []

    if combined >= 5:
        actions += [
            "薬は外出30分前に必ず飲む",
            "不織布マスク必須（できれば立体型）",
            "帰宅後すぐ顔洗い＋着替え",
            "洗濯物は部屋干し",
        ]
    elif combined >= 4:
        actions += [
            "薬は外出前に飲んでおく",
            "マスク必須",
            "帰宅後は顔を洗う",
            "衣類は玄関で払う",
        ]
    elif combined >= 3:
        actions += [
            "薬を忘れずに",
            "マスク推奨",
            "目薬・ティッシュを携帯",
        ]
    elif combined >= 2:
        actions += [
            "症状ある人は薬を携帯",
            "マスク推奨",
            "外干しは控えめに",
        ]
    else:
        actions += [
            "今日は比較的ラクな日",
            "外出時は様子見でOK",
            "帰宅後のうがいで予防",
        ]

    # 風が強い日は一言加える（ただし3つに収まるよう調整）
    if wind and "強" in wind:
        actions.append("風が強いので花粉が舞いやすい")

    # 3つに固定
    return actions[:3]


# ----------------------------
# 締めの一言（短く、キレ）
# ----------------------------
CLOSING_EXTREME = [
    "今日は正直きつい日。",
    "無理しないのが正解。",
    "外出は最小限で。",
]
CLOSING_HIGH = [
    "油断するとやられる日。",
    "対策した人が勝つ日。",
]
CLOSING_MID = [
    "午後に悪化しやすいパターン。",
    "早め対策でラクになる。",
]
CLOSING_LOW = [
    "今日は比較的マシ。",
    "油断しすぎなければOK。",
]


def _generate_closing(combined: int) -> str:
    if combined >= 5:
        return random.choice(CLOSING_EXTREME)
    if combined >= 4:
        return random.choice(CLOSING_HIGH)
    if combined >= 3:
        return random.choice(CLOSING_MID)
    return random.choice(CLOSING_LOW)


# ----------------------------
# 文字数制限（雑に安全側）
# 日本語は概算で2カウント扱い
# ----------------------------
def _trim_to_limit(text: str, max_chars: int = 280) -> str:
    def twitter_len(s: str) -> int:
        cnt = 0
        for ch in s:
            cnt += 2 if ord(ch) > 127 else 1
        return cnt

    if twitter_len(text) <= max_chars:
        return text

    # 末尾から削る（行単位）
    parts = text.split(" ")
    while parts and twitter_len(" ".join(parts)) > max_chars:
        parts.pop()
    return " ".join(parts)


# ----------------------------
# メイン生成
# ----------------------------
def generate_tweet(data: IntegratedPollenData) -> str:
    # JSTの日付を固定採用（data.date は使わない）
    date_str = _today_jst_str()

    sugi_num = _to_int_level(getattr(data, "sugi_level_num", None), default=_to_int_level(getattr(data, "sugi_level", None), 0))
    hinoki_num = _to_int_level(getattr(data, "hinoki_level_num", None), default=_to_int_level(getattr(data, "hinoki_level", None), 0))

    sugi_delta = _to_int_level(getattr(data, "sugi_diff", 0), 0)
    hinoki_delta = _to_int_level(getattr(data, "hinoki_diff", 0), 0)

    high_temp = getattr(data, "high_temp", None)
    wind = getattr(data, "wind", None)
    weather = getattr(data, "weather", None)

    combined = max(sugi_num, hinoki_num)

    header = f"【花粉症の人へ】 {date_str} 東京"
    sugi_line = f"スギ：{sugi_num}/5（前日比{_arrow(sugi_delta)}）"
    hinoki_line = f"ヒノキ：{hinoki_num}/5（前日比{_arrow(hinoki_delta)}）"

    weather_bits = []
    if high_temp is not None and str(high_temp).strip() != "":
        weather_bits.append(f"最高{high_temp}℃")
    if wind and str(wind).strip() != "":
        weather_bits.append(str(wind))
    if weather and str(weather).strip() != "":
        weather_bits.append(str(weather))
    weather_line = " / ".join(weather_bits) if weather_bits else ""

    actions = _generate_actions(combined=combined, wind=str(wind) if wind else None)
    actions_text = " / ".join([f"・{a}" for a in actions])

    closing = _generate_closing(combined)

    hashtags = "#花粉 #花粉予報"

    # 改行は使わず、まとまりは「スペース」で区切る（ユーザー要望）
    tweet = " ".join([x for x in [header, sugi_line, hinoki_line, weather_line, "▼今日やること", actions_text, closing, hashtags] if x])

    return _trim_to_limit(tweet)