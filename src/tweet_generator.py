"""
tweet_generator.py

統合データ（IntegratedPollenData）から X 投稿文を生成する。

要件:
- 地名は「東京」だけ（区は出さない）
- 日付は必ず JST (Asia/Tokyo) で生成（GitHub Actions の UTC でズレないように）
- ブロックごとに改行して読みやすくする
- 全体で Twitter 換算 280 字以内に収める（日本語は2カウント）
- 「(更新 09:52)」のような更新時刻は出さない
"""

import random
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from data_integrator import IntegratedPollenData


# ----------------------------
# JST固定の日付（短縮形: 3/4(火)）
# ----------------------------
def _today_jst_str() -> str:
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    dow = "月火水木金土日"[now.weekday()]
    return now.strftime(f"%-m/%-d({dow})")


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
        if "/" in s:
            s = s.split("/")[0].strip()
        return int(float(s))
    except Exception:
        return default


# ----------------------------
# 天気×花粉の関係コメント（短め・最大15文字）
# ----------------------------
def _weather_insight(weather: Optional[str], high_temp: Optional[str], wind: Optional[str]) -> str:
    temp_num = None
    try:
        if high_temp and str(high_temp).strip():
            temp_num = int(str(high_temp).strip())
    except (ValueError, TypeError):
        pass

    is_rainy = weather and ("雨" in weather)
    is_windy = wind and "強" in wind
    is_hot = temp_num is not None and temp_num >= 20
    is_warm = temp_num is not None and temp_num >= 15

    if is_rainy:
        return random.choice([
            "雨の日は花粉が少ない。",
            "雨が花粉を地面に落とす日。",
        ])
    if is_hot and is_windy:
        return random.choice([
            "暑さ＋強風で花粉が大量飛散。",
            "気温高＋強風のダブルパンチ。",
        ])
    if is_hot:
        return random.choice([
            "暖かい午後に花粉がピークに。",
            "気温が高い日は花粉が活発になる。",
        ])
    if is_warm and is_windy:
        return random.choice([
            "風に乗って花粉が広範囲に飛ぶ。",
            "風向きに注意。花粉が四方から来る。",
        ])
    if is_warm:
        return random.choice([
            "暖かい日は午後の花粉に注意。",
            "気温が上がる午後は窓を閉めよう。",
        ])
    if is_windy:
        return random.choice([
            "強風で花粉が遠くまで飛ぶ。",
            "風が花粉を大量に巻き上げる。",
        ])

    return random.choice([
        "朝のうちに対策を済ませよう。",
        "5分の準備が今日1日を変える。",
    ])


# ----------------------------
# 行動（3つ・具体的・短め）
# ----------------------------
def _generate_actions(combined: int, wind: Optional[str], weather: Optional[str]) -> list[str]:
    is_rainy = weather and "雨" in weather
    is_windy = wind and "強" in wind

    if is_rainy:
        return [
            "洗濯物を外干しするなら今日がチャンス",
            "換気するなら雨が上がる前に窓を閉める",
            "帰宅後のうがい＋洗顔は晴れの日と同じく",
        ]

    if combined >= 5:
        pool = [
            "薬は外出60分前に飲む",
            "鼻にワセリンで花粉をブロック",
            "眼鏡で目への花粉を激減させる",
            "帰宅後すぐ洗顔＋鼻うがい",
            "洗濯物は部屋干し一択",
            "玄関で上着を脱いで花粉を持ち込まない",
        ]
    elif combined >= 4:
        pool = [
            "薬は外出30分前に飲む",
            "鼻にワセリンで花粉ブロック",
            "眼鏡で目の花粉を大幅カット",
            "帰宅後に洗顔＋鼻うがい",
            "綿や麻の服は花粉がつきにくい",
            "洗濯物は部屋干しか取り込む前に払う",
        ]
    elif combined >= 3:
        pool = [
            "症状がある人は出発前に薬を飲む",
            "鼻にワセリンを薄く塗るだけで効果あり",
            "眼鏡で花粉を防ぐと症状がラクになる",
            "帰宅後30分以内の洗顔が効果的",
            "玄関でコロコロをかけて花粉を落とす",
        ]
    elif combined >= 2:
        pool = [
            "症状が気になるならマスクをしておく",
            "帰宅後のうがい＋洗顔を習慣にしよう",
            "洗濯物は取り込む前に軽く払う",
            "目薬は痒くなる前に差すのがコツ",
        ]
    else:
        pool = [
            "今日は比較的ラク。でも対策習慣は続けよう",
            "帰宅後のうがい＋洗顔を続けると全体が楽になる",
            "薬・目薬のストックを今日確認しておこう",
        ]

    if is_windy and combined < 5:
        pool.insert(0, "強風で花粉が広範囲に飛ぶ。屋外は短めに")

    random.shuffle(pool)
    return pool[:3]


# ----------------------------
# 締めの一言（短く・キレよく）
# ----------------------------
CLOSING_EXTREME = [
    "外出は最小限に。",
    "無理しないが正解。",
    "対策した人が生き残る。",
]
CLOSING_HIGH = [
    "対策した人が勝つ。",
    "鼻と目を守って出よう。",
    "今日は対策した人の勝ち。",
]
CLOSING_MID = [
    "朝のうちに準備を。",
    "後回しにしないで。",
    "早め対策で乗り切ろう。",
]
CLOSING_LOW = [
    "今日は比較的マシ。",
    "油断だけはしないで。",
    "続けることが大事。",
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
# 文字数チェック（Twitter換算）
# 日本語は2カウント、ASCII は1カウント
# ----------------------------
def _twitter_len(s: str) -> int:
    return sum(2 if ord(c) > 127 else 1 for c in s)


def _trim_to_limit(text: str, max_chars: int = 280) -> str:
    """超えていたら末尾の行から削る（ハッシュタグは残す）"""
    if _twitter_len(text) <= max_chars:
        return text

    lines = text.split("\n")
    hashtag_line = lines[-1] if lines else ""
    body_lines = lines[:-1]

    while body_lines and _twitter_len("\n".join(body_lines) + "\n" + hashtag_line) > max_chars:
        body_lines.pop()

    return "\n".join(body_lines) + "\n" + hashtag_line


# ----------------------------
# メイン生成
# ----------------------------
def generate_tweet(data: IntegratedPollenData) -> str:
    date_str = _today_jst_str()

    sugi_num = _to_int_level(getattr(data, "sugi_level_num", None), default=_to_int_level(getattr(data, "sugi_level", None), 0))
    hinoki_num = _to_int_level(getattr(data, "hinoki_level_num", None), default=_to_int_level(getattr(data, "hinoki_level", None), 0))
    sugi_label = getattr(data, "sugi_level", "")
    hinoki_label = getattr(data, "hinoki_level", "")

    sugi_diff_raw = getattr(data, "sugi_diff", "→")
    hinoki_diff_raw = getattr(data, "hinoki_diff", "→")

    high_temp = getattr(data, "high_temp", None)
    wind = getattr(data, "wind", None)
    weather = getattr(data, "weather", None)

    combined = max(sugi_num, hinoki_num)

    # ── ヘッダー ──
    header = f"【花粉症の人へ】{date_str} 東京"

    # ── 花粉レベル（2行） ──
    sugi_line = f"スギ：{sugi_label} {sugi_num}/5（前日比{sugi_diff_raw}）"
    hinoki_line = f"ヒノキ：{hinoki_label} {hinoki_num}/5（前日比{hinoki_diff_raw}）"

    # ── 天気 ──
    weather_bits = []
    if high_temp and str(high_temp).strip():
        weather_bits.append(f"最高{high_temp}℃")
    if wind and str(wind).strip():
        weather_bits.append(str(wind))
    if weather and str(weather).strip() and weather != "不明":
        weather_bits.append(str(weather))
    weather_summary = " ".join(weather_bits) if weather_bits else ""

    insight = _weather_insight(
        weather=str(weather) if weather else None,
        high_temp=str(high_temp) if high_temp else None,
        wind=str(wind) if wind else None,
    )

    # ── 行動候補 ──
    actions = _generate_actions(
        combined=combined,
        wind=str(wind) if wind else None,
        weather=str(weather) if weather else None,
    )

    # ── 締め＋ハッシュタグ（常に末尾に確保） ──
    closing = _generate_closing(combined)
    tail = f"{closing}\n#花粉 #花粉予報"

    # ── 骨格を作り、残り予算で行動を詰め込む ──
    skeleton_lines = [header, ""]
    skeleton_lines += [sugi_line, hinoki_line, ""]
    if weather_summary:
        skeleton_lines += [weather_summary, insight, ""]
    else:
        skeleton_lines += [insight, ""]
    skeleton_lines += ["▼今日やること"]

    skeleton = "\n".join(skeleton_lines) + "\n\n" + tail
    budget = 278 - _twitter_len(skeleton)  # 2文字バッファ込み

    action_lines = []
    for action in actions:
        line = f"・{action}"
        cost = _twitter_len(line) + 1  # +1 は改行文字分
        if budget >= cost:
            action_lines.append(line)
            budget -= cost

    tweet = "\n".join(skeleton_lines)
    if action_lines:
        tweet += "\n" + "\n".join(action_lines)
    tweet += "\n\n" + tail

    return tweet
