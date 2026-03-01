"""
ツイート生成モジュール
統合データ(IntegratedPollenData)からツイート文を生成する
"""

import random
from datetime import datetime
from data_integrator import IntegratedPollenData


# === 締めの一言バリエーション ===
CLOSING_EXTREME = [
    "今日は正直、外に出たくない。",
    "都内の空気、もはや凶器。",
    "ティッシュは1箱カバンに入れたほうがいい。",
    "これはもう天災。",
    "耳鼻科が混む日。朝イチ推奨。",
]
CLOSING_SEVERE = [
    "油断するとやられる日。",
    "昨日よりキツい。体感でわかるレベル。",
    "薬飲み忘れると午後から地獄になる。",
    "帰ったら玄関で服を払う。これだけで夜が変わる。",
]
CLOSING_MODERATE = [
    "まだ耐えられるけど、午後から増えるパターン。",
    "昼過ぎに症状出始めたら、すぐ薬。",
    "今日くらいならマスクでなんとかなる。",
]
CLOSING_MILD = [
    "今日は比較的マシな日。",
    "マシな日こそ、明日に備えて体力温存。",
]
CLOSING_LOW = [
    "今日は久しぶりに人間として生きられる。",
    "換気のチャンス。窓を開けるなら今。",
]


def generate_tweet(data: IntegratedPollenData) -> str:
    """統合データからツイート文を生成"""

    # 1) ヘッダー（東京固定 / 千代田区は出さない）
    header = f"【花粉症の人へ】\n{data.date}({data.day_of_week}) 東京"

    # 2) 花粉（スギ/ヒノキ + 前日比）
    sugi_line = f"スギ：{data.sugi_level}（前日比{data.sugi_diff}）"
    hinoki_line = f"ヒノキ：{data.hinoki_level}（前日比{data.hinoki_diff}）"

    # 3) 天気
    parts = []
    if data.high_temp and data.high_temp != "不明":
        parts.append(f"最高{data.high_temp}℃")
    if data.wind and data.wind != "不明":
        parts.append(data.wind)
    if data.weather and data.weather != "不明":
        parts.append(data.weather)
    weather_line = " / ".join(parts) if parts else "天気情報：取得失敗"

    # 4) 今日やること（3〜5個）
    actions = _generate_actions(data)
    actions_block = "▼ 今日やること\n" + "\n".join(f"・{a}" for a in actions)

    # 5) 締め（毎回変わる＝403の重複回避に効く）
    closing = _generate_closing(data)

    # 6) 末尾に“投稿時刻(分)”を入れて重複回避を強化（同日再実行でも被りにくい）
    stamp = datetime.now().strftime("%H:%M")
    footer = f"\n#花粉 #花粉予報\n（更新 {stamp}）"

    tweet = f"{header}\n{sugi_line}\n{hinoki_line}\n{weather_line}\n{actions_block}\n{closing}{footer}"
    return _trim_to_limit(tweet, 280)


def _generate_actions(data: IntegratedPollenData) -> list[str]:
    actions = []
    combined = max(int(data.sugi_level_num), int(data.hinoki_level_num))

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
        ]
    elif combined >= 3:
        actions += [
            "薬を忘れずに",
            "マスク推奨",
        ]
    elif combined >= 2:
        actions += [
            "症状ある人は薬を携帯",
            "外出後は軽く洗顔",
        ]
    else:
        actions += ["今日は比較的ラクな日。換気のチャンス"]

    # 風が強い日は追加
    if data.wind and ("強" in data.wind):
        actions.append("風が強い→花粉が舞いやすい。目・鼻ガード強めに")

    # 最大5個
    return actions[:5]


def _generate_closing(data: IntegratedPollenData) -> str:
    combined = max(int(data.sugi_level_num), int(data.hinoki_level_num))
    if combined >= 5:
        return random.choice(CLOSING_EXTREME)
    if combined >= 4:
        return random.choice(CLOSING_SEVERE)
    if combined >= 3:
        return random.choice(CLOSING_MODERATE)
    if combined >= 2:
        return random.choice(CLOSING_MILD)
    return random.choice(CLOSING_LOW)


def _trim_to_limit(text: str, max_chars: int = 280) -> str:
    """
    日本語は2カウントとして簡易計算し、超えたら「・」行（アクション）から削る
    """
    def twitter_length(s: str) -> int:
        return sum(2 if ord(ch) > 127 else 1 for ch in s)

    if twitter_length(text) <= max_chars:
        return text

    lines = text.split("\n")
    while twitter_length("\n".join(lines)) > max_chars and len(lines) > 5:
        # 後ろから「・」行を削る
        removed = False
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith("・"):
                lines.pop(i)
                removed = True
                break
        if not removed:
            break

    return "\n".join(lines)