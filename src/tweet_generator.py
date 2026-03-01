import random
from dataclasses import dataclass
from datetime import datetime

from data_integrator import IntegratedPollenData


# =========================
# 文言テーブル
# =========================

CLOSING_EXTREME = [
    "今日は正直、外に出たくない。",
    "都内の空気、重たい。",
    "今日は無理せず守りに入ろう。",
]
CLOSING_HIGH = [
    "油断するとやられる日。",
    "今日は体感キツいかも。",
    "なるべく花粉を避けていこう。",
]
CLOSING_MID = [
    "午後に悪化しやすいパターン。",
    "外出するなら短時間で。",
    "目と鼻を守っていこう。",
]
CLOSING_LOW = [
    "今日は比較的マシ。",
    "今日はラクな日。",
    "外出してもそこまで心配ないかも。",
]

# ざっくりテンプレ（レベル別）
ACTIONS_5 = [
    "薬は外出30分前に必ず飲む",
    "不織布マスク必須（できれば立体型）",
    "帰宅後すぐ顔洗い＋着替え",
    "洗濯物は部屋干し",
]
ACTIONS_4 = [
    "薬は外出前に飲んでおく",
    "マスク必須",
    "帰宅後は顔を洗う",
]
ACTIONS_3 = [
    "薬を忘れずに",
    "マスク推奨",
    "目が痒い人は目薬",
]
ACTIONS_2 = [
    "症状ある人は薬を携帯",
    "マスク推奨",
]
ACTIONS_1 = [
    "今日は比較的ラクな日",
]


# =========================
# ユーティリティ
# =========================

def _normalize_level_num(level_num: int) -> int:
    """1〜5に丸める"""
    try:
        n = int(level_num)
    except Exception:
        return 3
    return max(1, min(5, n))


def _arrow(delta: int) -> str:
    """前日比の矢印"""
    if delta > 0:
        return "↑"
    if delta < 0:
        return "↓"
    return "→"


def _format_date_jp(date_str: str) -> str:
    """
    data.date が 'YYYY-MM-DD' でも 'MM/DD' でも来ても、
    それっぽく '03月01日(日)' に寄せる。
    """
    # まず ISO想定
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%m月%d日(%a)").replace("Mon", "月").replace("Tue", "火").replace("Wed", "水") \
                .replace("Thu", "木").replace("Fri", "金").replace("Sat", "土").replace("Sun", "日")
        except Exception:
            pass

    # それ以外はそのまま
    return date_str


def _trim_to_limit(text: str, max_chars: int = 280) -> str:
    """
    Xの文字数は厳密にはURL等で変動するが、
    ここは「日本語=2カウント相当」で雑に落とす。
    """
    def twitter_length(s: str) -> int:
        count = 0
        for ch in s:
            count += 2 if ord(ch) > 127 else 1
        return count

    if twitter_length(text) <= max_chars:
        return text

    # 行単位で削る（下から落とす）
    lines = text.split("\n")
    while lines and twitter_length("\n".join(lines)) > max_chars:
        # 最後の行を落とす
        lines.pop()

    # 末尾が空行だらけなら整える
    while lines and lines[-1].strip() == "":
        lines.pop()

    return "\n".join(lines)


# =========================
# 本体
# =========================

def _generate_actions(data: IntegratedPollenData) -> list[str]:
    """
    花粉の強さ（スギ/ヒノキの大きい方）をベースに
    行動3つ程度に落とす
    """
    sugi = _normalize_level_num(getattr(data, "sugi_level_num", 3))
    hinoki = _normalize_level_num(getattr(data, "hinoki_level_num", 3))
    combined = max(sugi, hinoki)

    if combined >= 5:
        base = ACTIONS_5
    elif combined == 4:
        base = ACTIONS_4
    elif combined == 3:
        base = ACTIONS_3
    elif combined == 2:
        base = ACTIONS_2
    else:
        base = ACTIONS_1

    actions = base.copy()

    # 風が強い日は一言追加（任意）
    wind = getattr(data, "wind", "")
    if isinstance(wind, str) and ("強" in wind or "強い" in wind):
        actions.append("風が強いので花粉が舞いやすい")

    # 3つに絞る
    return actions[:3]


def _generate_closing(data: IntegratedPollenData) -> str:
    sugi = _normalize_level_num(getattr(data, "sugi_level_num", 3))
    hinoki = _normalize_level_num(getattr(data, "hinoki_level_num", 3))
    combined = max(sugi, hinoki)

    if combined >= 5:
        return random.choice(CLOSING_EXTREME)
    if combined == 4:
        return random.choice(CLOSING_HIGH)
    if combined == 3:
        return random.choice(CLOSING_MID)
    return random.choice(CLOSING_LOW)


def generate_tweet(data: IntegratedPollenData) -> str:
    """
    要件：
    - 「東京」だけ（区名は出さない）
    - まとまりごとに改行
    - 更新時刻は出さない
    """

    # ヘッダー
    header = "【花粉症の人へ】"

    # 日付
    date_str = getattr(data, "date", "")
    date_jp = _format_date_jp(date_str)

    # 花粉（表示は 5/5 形式）
    sugi_level = _normalize_level_num(getattr(data, "sugi_level_num", 3))
    hinoki_level = _normalize_level_num(getattr(data, "hinoki_level_num", 3))

    sugi_delta = int(getattr(data, "sugi_delta", 0) or 0)
    hinoki_delta = int(getattr(data, "hinoki_delta", 0) or 0)

    sugi_line = f"スギ：{sugi_level}/5（前日比{_arrow(sugi_delta)}）"
    hinoki_line = f"ヒノキ：{hinoki_level}/5（前日比{_arrow(hinoki_delta)}）"

    # 天気
    high_temp = getattr(data, "high_temp", "")
    weather = getattr(data, "weather", "")
    wind = getattr(data, "wind", "")

    weather_parts = []
    if high_temp:
        weather_parts.append(f"最高{high_temp}℃")
    if wind:
        weather_parts.append(str(wind))
    if weather:
        weather_parts.append(str(weather))
    weather_line = " / ".join(weather_parts) if weather_parts else ""

    # アクション
    actions = _generate_actions(data)
    actions_block = "▼ 今日やること\n" + "\n".join([f"・{a}" for a in actions])

    # 締め
    closing = _generate_closing(data)

    # ハッシュタグ
    footer = "#花粉 #花粉予報"

    # まとまりごとに空行を入れる（要望）
    tweet = (
        f"{header}\n\n"
        f"{date_jp} 東京\n\n"
        f"{sugi_line}\n"
        f"{hinoki_line}\n\n"
        f"{weather_line}\n\n"
        f"{actions_block}\n\n"
        f"{closing}\n\n"
        f"{footer}"
    )

    return _trim_to_limit(tweet, 280)