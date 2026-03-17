"""
tweet_generator.py

ブンブン（花粉症持ち・データ一筋・40代）の声で X 投稿文を生成する。

設計方針:
- 花粉症の当事者として語る（情報提供者ではなく、同じ苦しみを持つ者）
- 命令形・断言・短文でキレよく
- 読んだ人が「このアカウントをフォローしたい」と思う個性を出す
- 将来的に花粉症グッズ・薬のアフィリエイトへの導線を設計できる構成
- 全体で Twitter 換算 280 字以内
"""

import random
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from data_integrator import IntegratedPollenData


JST = ZoneInfo("Asia/Tokyo")


def _today_jst_str() -> str:
    now = datetime.now(JST)
    dow = "月火水木金土日"[now.weekday()]
    return now.strftime(f"%-m/%-d({dow})")


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


def _twitter_len(s: str) -> int:
    return sum(2 if ord(c) > 127 else 1 for c in s)


# ────────────────────────────────────────
# レベル別・冒頭フック（ブンブンの声）
# ────────────────────────────────────────
HOOK_EXTREME = [
    "今日の東京、正直きつい。",
    "今日は外に出たくない日のやつ。",
    "データ見て軽く絶望した。今日の東京。",
    "今日は花粉症の人間にとって試練の日。",
]
HOOK_HIGH = [
    "今日の東京、普通に厳しい。",
    "今日も花粉が容赦ない。",
    "油断できない数字が出た。今日の東京。",
    "今日は対策しないと後悔する日。",
]
HOOK_MID = [
    "今日もそこそこ飛んでる。東京。",
    "悪くはないが、油断できない日。",
    "今日の東京、まあ普通にある。",
]
HOOK_LOW = [
    "今日は比較的マシ。でも続けること。",
    "今日は少し楽な日。習慣は崩すな。",
    "数字は低め。でもゼロじゃない。",
]


def _generate_hook(combined: int) -> str:
    if combined >= 5:
        return random.choice(HOOK_EXTREME)
    if combined >= 4:
        return random.choice(HOOK_HIGH)
    if combined >= 3:
        return random.choice(HOOK_MID)
    return random.choice(HOOK_LOW)


# ────────────────────────────────────────
# 差分を矢印に変換
# ────────────────────────────────────────
def _diff_arrow(diff_raw) -> str:
    s = str(diff_raw).strip() if diff_raw else "→"
    if s in ("→", "↑", "↓", "↗", "↘"):
        return s
    try:
        v = float(s)
        if v > 0:
            return "↑"
        if v < 0:
            return "↓"
        return "→"
    except Exception:
        return "→"


# ────────────────────────────────────────
# 天気インサイト（ブンブン視点・短く断言）
# ────────────────────────────────────────
def _weather_insight(weather: Optional[str], high_temp: Optional[str], wind: Optional[str]) -> str:
    temp_num = None
    try:
        if high_temp:
            temp_num = int(str(high_temp).strip())
    except Exception:
        pass

    is_rainy = weather and "雨" in weather
    is_windy = wind and "強" in wind
    is_hot = temp_num is not None and temp_num >= 20
    is_warm = temp_num is not None and temp_num >= 15

    if is_rainy:
        return random.choice([
            "雨は花粉を落とす。今日は比較的助かる。",
            "雨の日は花粉が少ない。外干しチャンス。",
        ])
    if is_hot and is_windy:
        return random.choice([
            "気温高＋強風。最悪の組み合わせ。",
            "暑さと風のダブルパンチ。今日は長居するな。",
        ])
    if is_hot:
        return random.choice([
            "気温が上がる午後がピーク。外出は午前中に。",
            "暖かい日は花粉が活発になる。午後は注意。",
        ])
    if is_warm and is_windy:
        return random.choice([
            "風に乗って広範囲に飛ぶ。屋外は最小限に。",
            "風向き次第で一気に来る。マスクは必須。",
        ])
    if is_warm:
        return random.choice([
            "暖かい午後に窓を開けるな。",
            "気温上昇＋晴れ。花粉が活発になる時間帯。",
        ])
    if is_windy:
        return random.choice([
            "強風で花粉が遠くまで飛ぶ。",
            "風が花粉を運ぶ。屋外の時間を減らせ。",
        ])

    return random.choice([
        "朝のうちに対策を済ませておけ。",
        "5分の準備が今日1日の差になる。",
    ])


# ────────────────────────────────────────
# 行動（命令形・短く・キレよく）
# ────────────────────────────────────────
def _generate_actions(combined: int, wind: Optional[str], weather: Optional[str]) -> list[str]:
    is_rainy = weather and "雨" in weather
    is_windy = wind and "強" in wind

    if is_rainy:
        return [
            "洗濯物：今日が外干しのチャンス",
            "換気：雨が上がる前に窓を閉めろ",
            "うがい＋洗顔：晴れの日と同じくやれ",
        ]

    if combined >= 5:
        pool = [
            "薬：外出60分前に飲め",
            "マスク：必ずつけて出ろ",
            "眼鏡：花粉用を使え",
            "帰宅後：即シャワー、服は玄関で脱げ",
            "洗濯物：部屋干し一択",
            "外出：午前中だけにしろ",
        ]
    elif combined >= 4:
        pool = [
            "薬：今すぐ飲め",
            "鼻にワセリン：塗るだけで防御力が上がる",
            "眼鏡：花粉を7割カットできる",
            "帰宅後：洗顔＋鼻うがいをやれ",
            "洗濯物：部屋干しか、取り込む前に払え",
            "玄関：上着を脱いで花粉を持ち込むな",
        ]
    elif combined >= 3:
        pool = [
            "症状がある人：今すぐ薬を飲め",
            "鼻ワセリン：5秒でできる最強対策",
            "眼鏡：つけるだけで目の花粉が激減する",
            "帰宅後30分以内の洗顔が効く",
            "玄関でコロコロをかけてから入れ",
        ]
    elif combined >= 2:
        pool = [
            "症状が気になるならマスクをしろ",
            "帰宅後のうがい＋洗顔を習慣にしろ",
            "洗濯物は取り込む前に軽く払え",
            "目薬：痒くなる前に差すのが正解",
        ]
    else:
        pool = [
            "今日は比較的楽。でも対策習慣は続けろ",
            "帰宅後のうがい＋洗顔：続けると全体が楽になる",
            "薬・目薬のストックを今日確認しておけ",
        ]

    if is_windy and combined < 5:
        pool.insert(0, "強風で広範囲に飛ぶ。外出は短時間で")

    random.shuffle(pool)
    return pool[:3]


# ────────────────────────────────────────
# 締めの一言（ブンブンの言い切り）
# ────────────────────────────────────────
CLOSING_EXTREME = [
    "今日は対策した人間だけが生き残る。",
    "外出後は即シャワー。これだけは守れ。",
    "今日は無理するな。本当に。",
]
CLOSING_HIGH = [
    "今日は対策した人が明日楽になる。",
    "鼻と目を守って出ろ。今日は本番だ。",
    "準備した人間とそうでない人間で夜の快適さが変わる。",
]
CLOSING_MID = [
    "5分の準備で今日の夜が変わる。",
    "後回しにするな。今やれ。",
    "朝のうちに準備を済ませておけ。",
]
CLOSING_LOW = [
    "マシな日こそ習慣を崩すな。",
    "油断だけはするな。",
    "続けることが、シーズンを乗り切るコツだ。",
]


def _generate_closing(combined: int) -> str:
    if combined >= 5:
        return random.choice(CLOSING_EXTREME)
    if combined >= 4:
        return random.choice(CLOSING_HIGH)
    if combined >= 3:
        return random.choice(CLOSING_MID)
    return random.choice(CLOSING_LOW)


# ────────────────────────────────────────
# メイン生成
# ────────────────────────────────────────
def generate_tweet(data: IntegratedPollenData) -> str:
    date_str = _today_jst_str()

    sugi_num = _to_int_level(getattr(data, "sugi_level_num", None),
                             default=_to_int_level(getattr(data, "sugi_level", None), 0))
    hinoki_num = _to_int_level(getattr(data, "hinoki_level_num", None),
                               default=_to_int_level(getattr(data, "hinoki_level", None), 0))
    sugi_label = getattr(data, "sugi_level", "")
    hinoki_label = getattr(data, "hinoki_level", "")

    sugi_arrow = _diff_arrow(getattr(data, "sugi_diff", "→"))
    hinoki_arrow = _diff_arrow(getattr(data, "hinoki_diff", "→"))

    high_temp = getattr(data, "high_temp", None)
    wind = getattr(data, "wind", None)
    weather = getattr(data, "weather", None)

    combined = max(sugi_num, hinoki_num)

    # ── 冒頭フック ──
    hook = _generate_hook(combined)

    # ── データ行 ──
    data_line = f"{date_str} 東京　スギ {sugi_num}/5{sugi_arrow}　ヒノキ {hinoki_num}/5{hinoki_arrow}"

    # ── 天気まとめ ──
    weather_bits = []
    if high_temp and str(high_temp).strip():
        weather_bits.append(f"最高{high_temp}℃")
    if wind and str(wind).strip():
        weather_bits.append(str(wind))
    if weather and str(weather).strip() and weather != "不明":
        weather_bits.append(str(weather))
    weather_summary = "　".join(weather_bits) if weather_bits else ""

    insight = _weather_insight(
        weather=str(weather) if weather else None,
        high_temp=str(high_temp) if high_temp else None,
        wind=str(wind) if wind else None,
    )

    # ── 行動 ──
    actions = _generate_actions(
        combined=combined,
        wind=str(wind) if wind else None,
        weather=str(weather) if weather else None,
    )

    # ── 締め＋ハッシュタグ ──
    closing = _generate_closing(combined)
    hashtags = "#花粉 #花粉症 #花粉予報"

    # ── 組み立て（文字数を計算しながら行動を詰め込む）──
    lines = [hook, data_line]
    if weather_summary:
        lines.append(weather_summary)
    lines += ["", insight, "▼やること"]

    skeleton = "\n".join(lines) + "\n\n" + closing + "\n" + hashtags
    budget = 278 - _twitter_len(skeleton)

    action_lines = []
    for action in actions:
        line = f"・{action}"
        cost = _twitter_len(line) + 1
        if budget >= cost:
            action_lines.append(line)
            budget -= cost

    body = "\n".join(lines)
    if action_lines:
        body += "\n" + "\n".join(action_lines)
    body += "\n\n" + closing + "\n" + hashtags

    return body
