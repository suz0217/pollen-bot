"""
ツイート生成モジュール（完成版）
統合データから読みやすく、価値のある投稿を生成する
"""

import random
from data_integrator import IntegratedPollenData


def generate_tweet(data: IntegratedPollenData) -> str:
    """統合データからツイート文を生成"""

    # ===== ヘッダー =====
    header = f"【花粉症の人へ】\n{data.date}({data.day_of_week}) 東京"

    # ===== 花粉データ =====
    sugi_line = f"スギ：{data.sugi_level}（前日比{data.sugi_diff}）"
    hinoki_line = f"ヒノキ：{data.hinoki_level}（前日比{data.hinoki_diff}）"

    # ===== 気象 =====
    weather_parts = [f"最高{data.high_temp}℃"]
    if data.wind and data.wind != "不明":
        weather_parts.append(data.wind)
    if data.weather and data.weather != "不明":
        weather_parts.append(data.weather)

    weather_line = " / ".join(weather_parts)

    # ===== 今日やること =====
    actions = _generate_actions(data)
    actions_block = "▼ 今日やること\n" + "\n".join(f"・{a}" for a in actions)

    # ===== 締めの一言 =====
    closing = _generate_closing(data)

    tweet = f"""{header}
{sugi_line}
{hinoki_line}
{weather_line}
{actions_block}
{closing}"""

    return _trim_to_limit(tweet)


# ==========================
# アクション生成ロジック
# ==========================

def _generate_actions(data: IntegratedPollenData) -> list[str]:
    actions = []

    combined = max(data.sugi_level_num, data.hinoki_level_num)

    if combined >= 5:
        actions.extend([
            "薬は外出30分前に必ず飲む",
            "不織布マスク必須（できれば立体型）",
            "帰宅後すぐシャワー",
            "洗濯物は部屋干し",
        ])

    elif combined >= 4:
        actions.extend([
            "薬は外出前に飲んでおく",
            "マスク必須",
            "帰宅後は顔を洗う",
        ])

    elif combined >= 3:
        actions.extend([
            "薬を忘れずに",
            "マスクは推奨",
        ])

    elif combined >= 2:
        actions.extend([
            "症状ある人は薬を携帯",
        ])

    else:
        actions.extend([
            "今日は比較的ラクな日",
        ])

    # 風が強い日
    if data.wind and "強" in data.wind:
        actions.append("風が強いので花粉が舞いやすい")

    return actions[:4]


# ==========================
# 締めの一言
# ==========================

CLOSING_EXTREME = [
    "今日は正直きつい日。",
    "都内の空気、重たい。",
    "覚悟して外に出る日。",
]

CLOSING_HIGH = [
    "油断するとやられる日。",
    "昨日より体感キツいかも。",
]

CLOSING_MID = [
    "午後に悪化しやすいパターン。",
]

CLOSING_LOW = [
    "今日は比較的マシ。",
]


def _generate_closing(data: IntegratedPollenData) -> str:
    combined = max(data.sugi_level_num, data.hinoki_level_num)

    if combined >= 5:
        return random.choice(CLOSING_EXTREME)
    elif combined >= 4:
        return random.choice(CLOSING_HIGH)
    elif combined >= 3:
        return random.choice(CLOSING_MID)
    else:
        return random.choice(CLOSING_LOW)


# ==========================
# 文字数制限対応
# ==========================

def _trim_to_limit(text: str, max_chars: int = 280) -> str:
    """
    日本語は2カウントとして簡易計算
    """

    def twitter_length(s: str) -> int:
        count = 0
        for ch in s:
            count += 2 if ord(ch) > 127 else 1
        return count

    if twitter_length(text) <= max_chars:
        return text

    lines = text.split("\n")

    while twitter_length("\n".join(lines)) > max_chars and len(lines) > 5:
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith("・"):
                lines.pop(i)
                break
        else:
            break

    return "\n".join(lines)