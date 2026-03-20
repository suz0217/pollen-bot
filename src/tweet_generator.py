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
# 花粉の迷信データベース（mythbust用）
# ────────────────────────────────────────
MYTHS = [
    {"myth": "雨の翌日は花粉が少ない", "fact": "逆。雨で地面に落ちた花粉が乾いて再飛散する。翌日のほうが多いことがある。"},
    {"myth": "マスクをしていれば大丈夫", "fact": "普通のマスクで防げるのは約7割。目・髪・服からも入る。マスクだけでは足りない。"},
    {"myth": "花粉症は大人になってから発症する", "fact": "2歳で発症した記録がある。年齢は関係ない。蓄積量で決まる。"},
    {"myth": "室内にいれば安全", "fact": "服や髪に付着した花粉が室内に入る。帰宅後の対策なしでは室内も汚染される。"},
    {"myth": "花粉症は治らない", "fact": "舌下免疫療法で約8割が改善する。ただし3年以上の継続が必要。"},
    {"myth": "ヨーグルトで花粉症が治る", "fact": "腸内環境は免疫に影響するが、ヨーグルトだけで治る科学的根拠はない。薬を飲め。"},
    {"myth": "夜は花粉が飛ばない", "fact": "日中飛んだ花粉が夕方〜夜に地表に降りてくる。帰宅時間帯が実は危険。"},
    {"myth": "花粉は午前中がピーク", "fact": "午前中に飛散開始、昼に最大、夕方に再ピーク。1日2回のピークがある。"},
    {"myth": "鼻水が出なければ花粉症じゃない", "fact": "目の痒み・くしゃみ・肌荒れ・頭痛だけの花粉症もある。症状は人それぞれ。"},
    {"myth": "スギ花粉が終われば楽になる", "fact": "スギの後にヒノキ、その後にイネ科、秋にブタクサ。年間を通じて何かしら飛んでいる。"},
    {"myth": "花粉症の薬は眠くなるから飲みたくない", "fact": "第二世代の抗ヒスタミン薬はほぼ眠くならない。医者に相談して変えろ。"},
    {"myth": "空気清浄機があれば部屋は安全", "fact": "空気清浄機は空中の花粉を吸うが、床に落ちた花粉は取れない。併用で掃除しろ。"},
    {"myth": "布団を外に干しても叩けばOK", "fact": "叩くと花粉が繊維の奥に入り込む。掃除機で吸うか布団乾燥機を使え。"},
    {"myth": "目をこすれば痒みが治まる", "fact": "こすると結膜が傷つき症状が悪化する。冷やすか目薬を差せ。"},
    {"myth": "花粉は見えないから量がわからない", "fact": "車のボンネットを見ろ。黄色い粉が積もっていたら相当飛んでいる。"},
    {"myth": "少量の花粉なら問題ない", "fact": "花粉症はコップ理論。少量でも蓄積する。症状が出る前から対策しろ。"},
    {"myth": "引っ越せば花粉症が治る", "fact": "北海道でもシラカバ花粉がある。沖縄以外、日本中どこでも花粉は飛んでいる。"},
]


# ────────────────────────────────────────
# データ抽出ヘルパー
# ────────────────────────────────────────
def _extract_data(data: IntegratedPollenData) -> dict:
    sugi_num = _to_int_level(getattr(data, "sugi_level_num", None),
                             default=_to_int_level(getattr(data, "sugi_level", None), 0))
    hinoki_num = _to_int_level(getattr(data, "hinoki_level_num", None),
                               default=_to_int_level(getattr(data, "hinoki_level", None), 0))
    sugi_arrow = _diff_arrow(getattr(data, "sugi_diff", "→"))
    hinoki_arrow = _diff_arrow(getattr(data, "hinoki_diff", "→"))
    high_temp = getattr(data, "high_temp", None)
    wind = getattr(data, "wind", None)
    weather = getattr(data, "weather", None)
    combined = max(sugi_num, hinoki_num)
    date_str = _today_jst_str()
    data_line = f"{date_str} 東京　スギ {sugi_num}/5{sugi_arrow}　ヒノキ {hinoki_num}/5{hinoki_arrow}"
    weather_bits = []
    if high_temp and str(high_temp).strip():
        weather_bits.append(f"最高{high_temp}℃")
    if wind and str(wind).strip():
        weather_bits.append(str(wind))
    if weather and str(weather).strip() and weather != "不明":
        weather_bits.append(str(weather))
    weather_summary = "　".join(weather_bits) if weather_bits else ""
    return {
        "sugi_num": sugi_num, "hinoki_num": hinoki_num,
        "sugi_arrow": sugi_arrow, "hinoki_arrow": hinoki_arrow,
        "high_temp": high_temp, "wind": wind, "weather": weather,
        "combined": combined, "date_str": date_str,
        "data_line": data_line, "weather_summary": weather_summary,
    }


# ────────────────────────────────────────
# フォーマット選択
# ────────────────────────────────────────
def _choose_format(combined: int) -> str:
    now = datetime.now(JST)
    is_weekend = now.weekday() >= 5  # 土日

    if combined >= 5:
        return "oneline"
    if is_weekend:
        return "weekend"
    return random.choice(["standard", "comparison", "mythbust", "routine"])


# ────────────────────────────────────────
# フォーマット: standard（既存）
# ────────────────────────────────────────
def _generate_standard(d: dict) -> str:
    combined = d["combined"]
    hook = _generate_hook(combined)
    insight = _weather_insight(
        weather=str(d["weather"]) if d["weather"] else None,
        high_temp=str(d["high_temp"]) if d["high_temp"] else None,
        wind=str(d["wind"]) if d["wind"] else None,
    )
    actions = _generate_actions(
        combined=combined,
        wind=str(d["wind"]) if d["wind"] else None,
        weather=str(d["weather"]) if d["weather"] else None,
    )
    closing = _generate_closing(combined)
    hashtags = "#花粉 #花粉症 #花粉予報"
    lines = [hook, d["data_line"]]
    if d["weather_summary"]:
        lines.append(d["weather_summary"])
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


# ────────────────────────────────────────
# フォーマット: oneline（一言警報型）
# ────────────────────────────────────────
ONELINE_TEMPLATES = [
    "今日の東京、スギ{sugi}/5。\n一言だけ言う。外に出るな。\n#花粉 #花粉症",
    "スギ{sugi}/5　ヒノキ{hinoki}/5。\n今日は戦場。完全装備で出ろ。\n#花粉 #花粉予報",
    "{date} 東京。\nスギ{sugi}/5。過去最悪級。\n薬・マスク・眼鏡。以上。\n#花粉 #花粉症",
    "今日の数字を見ろ。スギ{sugi}/5。\n対策なしで外出したら後悔する。\n#花粉 #花粉症 #花粉予報",
]

def _generate_oneline(d: dict) -> str:
    template = random.choice(ONELINE_TEMPLATES)
    return template.format(
        sugi=d["sugi_num"], hinoki=d["hinoki_num"], date=d["date_str"]
    )


# ────────────────────────────────────────
# フォーマット: comparison（昨日比較型）
# ────────────────────────────────────────
COMPARISON_WORSE = [
    "昨日よりひどい。覚悟しろ。",
    "昨日マシだったからって油断するな。今日は違う。",
    "数字が上がった。対策を一段強化しろ。",
]
COMPARISON_BETTER = [
    "昨日より少しマシ。でも油断するな。",
    "数字は下がった。でも習慣を崩すな。",
    "少し楽な日。だが続けることが大事。",
]
COMPARISON_SAME = [
    "昨日と同じ。つまり対策も同じでいい。",
    "横ばい。変えなくていい。今日もやれ。",
]

def _generate_comparison(d: dict) -> str:
    combined = d["combined"]
    arrow = d["sugi_arrow"]
    if arrow in ("↑", "↗"):
        trend_comment = random.choice(COMPARISON_WORSE)
    elif arrow in ("↓", "↘"):
        trend_comment = random.choice(COMPARISON_BETTER)
    else:
        trend_comment = random.choice(COMPARISON_SAME)
    closing = _generate_closing(combined)
    lines = [
        trend_comment,
        "",
        d["data_line"],
    ]
    if d["weather_summary"]:
        lines.append(d["weather_summary"])
    lines += ["", closing, "#花粉 #花粉症 #花粉予報"]
    return "\n".join(lines)


# ────────────────────────────────────────
# フォーマット: weekend（週末対策型）
# ────────────────────────────────────────
WEEKEND_HIGH = [
    "週末だからって窓を開けて掃除するな。花粉が入る。",
    "外でBBQ？帰宅後に即シャワーしろ。服は玄関で脱げ。",
    "買い物は午前中に。午後は花粉のピーク。",
]
WEEKEND_LOW = [
    "今日は掃除日和。窓を開けて換気しろ。",
    "布団を干すなら今日がチャンス。取り込む前に掃除機をかけろ。",
    "数字が低い日に薬・マスクを買い足しておけ。",
]

def _generate_weekend(d: dict) -> str:
    combined = d["combined"]
    now = datetime.now(JST)
    day_name = "土曜" if now.weekday() == 5 else "日曜"
    if combined >= 3:
        advice = random.choice(WEEKEND_HIGH)
    else:
        advice = random.choice(WEEKEND_LOW)
    closing = _generate_closing(combined)
    lines = [
        f"{day_name}の花粉情報。",
        d["data_line"],
    ]
    if d["weather_summary"]:
        lines.append(d["weather_summary"])
    lines += ["", advice, "", closing, "#花粉 #花粉症 #花粉予報"]
    return "\n".join(lines)


# ────────────────────────────────────────
# フォーマット: mythbust（花粉の真実型）
# ────────────────────────────────────────
def _generate_mythbust(d: dict) -> str:
    myth_item = random.choice(MYTHS)
    lines = [
        f"「{myth_item['myth']}」",
        "",
        f"→ {myth_item['fact']}",
        "",
        d["data_line"],
        "#花粉 #花粉症 #花粉予報",
    ]
    body = "\n".join(lines)
    if _twitter_len(body) > 278:
        # 長すぎる場合はデータ行を省略
        lines = [
            f"「{myth_item['myth']}」",
            f"→ {myth_item['fact']}",
            "#花粉 #花粉症",
        ]
        body = "\n".join(lines)
    return body


# ────────────────────────────────────────
# フォーマット: routine（朝ルーティン型）
# ────────────────────────────────────────
ROUTINE_STEPS_HIGH = [
    "薬を飲む（外出60分前）",
    "鼻にワセリンを塗る",
    "マスク＋花粉用眼鏡で出る",
    "玄関に粘着ローラーを置く",
    "帰宅したら即洗顔＋うがい",
]
ROUTINE_STEPS_MID = [
    "薬を飲む",
    "マスクをつける",
    "帰宅後に洗顔する",
    "洗濯物を部屋干しにする",
    "窓を開けない",
]
ROUTINE_STEPS_LOW = [
    "薬のストックを確認",
    "帰宅後にうがい＋洗顔",
    "布団を干すなら今日",
]

def _generate_routine(d: dict) -> str:
    combined = d["combined"]
    if combined >= 4:
        pool = ROUTINE_STEPS_HIGH
    elif combined >= 2:
        pool = ROUTINE_STEPS_MID
    else:
        pool = ROUTINE_STEPS_LOW
    random.shuffle(pool)
    steps = pool[:3]
    lines = [
        "今朝やること3つ。",
        d["data_line"],
        "",
    ]
    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. {step}")
    closing = _generate_closing(combined)
    lines += ["", closing, "#花粉 #花粉症 #花粉予報"]
    return "\n".join(lines)


# ────────────────────────────────────────
# メイン生成
# ────────────────────────────────────────
def generate_tweet(data: IntegratedPollenData, force_format: Optional[str] = None) -> str:
    d = _extract_data(data)
    fmt = force_format or _choose_format(d["combined"])

    generators = {
        "standard": _generate_standard,
        "oneline": _generate_oneline,
        "comparison": _generate_comparison,
        "weekend": _generate_weekend,
        "mythbust": _generate_mythbust,
        "routine": _generate_routine,
    }

    generator = generators.get(fmt, _generate_standard)
    body = generator(d)

    # 安全弁: 280文字を超えた場合はstandardにフォールバック
    if _twitter_len(body) > 280 and fmt != "standard":
        body = _generate_standard(d)

    return body
