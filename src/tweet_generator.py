"""
tweet_generator.py

ブンブン（データ一筋・40代・言い切り型）の声で
熱中症予報 + 紫外線予報の X 投稿文を生成する。

設計方針:
- 当事者として語る（暑さと戦う人間の目線）
- 命令形・断言・短文でキレよく
- 読んだ人が「このアカウントをフォローしたい」と思う個性を出す
- 全体で Twitter 換算 280 字以内
"""

import random
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from data_integrator import IntegratedWeatherData


JST = ZoneInfo("Asia/Tokyo")


def _today_jst_str() -> str:
    now = datetime.now(JST)
    dow = "月火水木金土日"[now.weekday()]
    return now.strftime(f"%-m/%-d({dow})")


def _twitter_len(s: str) -> int:
    return sum(2 if ord(c) > 127 else 1 for c in s)


# ────────────────────────────────────────
# 熱中症レベル別・冒頭フック
# ────────────────────────────────────────
HOOK_DANGER = [
    "今日の東京、命に関わるレベル。",
    "データ見て血の気が引いた。今日の東京。",
    "今日は本気で危ない。冗談じゃない。",
    "今日は外に出るな、としか言えない数字。",
]
HOOK_SEVERE = [
    "今日の東京、普通にやばい。",
    "油断したら倒れる。今日はそのレベル。",
    "数字を見ろ。今日は厳重警戒だ。",
    "今日は対策しないと後悔する暑さ。",
]
HOOK_WARNING = [
    "今日もじわじわ来る暑さ。東京。",
    "見た目より危ない日。今日はそれ。",
    "暑さに慣れた頃が一番危ない。",
]
HOOK_CAUTION = [
    "今日は比較的マシ。でも水は飲め。",
    "数字は落ち着いてる。でもゼロじゃない。",
    "今日はまだ楽な方。習慣を崩すな。",
]
HOOK_SAFE = [
    "今日は過ごしやすい。でも油断するな。",
    "数字は低め。水分だけは続けろ。",
]


def _generate_hook(hs_level: int) -> str:
    if hs_level >= 5:
        return random.choice(HOOK_DANGER)
    if hs_level >= 4:
        return random.choice(HOOK_SEVERE)
    if hs_level >= 3:
        return random.choice(HOOK_WARNING)
    if hs_level >= 2:
        return random.choice(HOOK_CAUTION)
    return random.choice(HOOK_SAFE)


# ────────────────────────────────────────
# 差分矢印
# ────────────────────────────────────────
def _diff_arrow(diff_raw) -> str:
    s = str(diff_raw).strip() if diff_raw else "→"
    if s in ("→", "↑", "↓", "↑↑", "↓↓", "↗", "↘"):
        return s
    return "→"


# ────────────────────────────────────────
# UV 表示
# ────────────────────────────────────────
UV_EMOJI = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "🟣"}

def _uv_bar(uv_num: int) -> str:
    emoji = UV_EMOJI.get(uv_num, "⚪")
    return f"UV {emoji}{uv_num}/5"


# ────────────────────────────────────────
# 行動アドバイス
# ────────────────────────────────────────
def _generate_actions(hs_level: int, uv_level: int, weather: str) -> list[str]:
    is_rainy = weather and "雨" in weather

    if is_rainy:
        return [
            "水分：雨でも汗はかく。飲め",
            "室内：湿度が上がる。エアコン必須",
            "日焼け止め：曇りでもUVは通る",
        ]

    if hs_level >= 5:
        pool = [
            "外出：最小限にしろ。命に関わる",
            "水分：15分に1回飲め。喉が渇く前に",
            "エアコン：我慢するな。つけろ",
            "塩分：経口補水液を常備しろ",
            "帽子+日傘：直射日光を絶対に避けろ",
            "子ども・高齢者：特に注意。声をかけろ",
        ]
    elif hs_level >= 4:
        pool = [
            "水分：30分に1回。ペットボトルを手放すな",
            "エアコン：28℃設定でいい。つけろ",
            "日傘 or 帽子：直射は避けろ",
            "外出：昼12〜15時を避けろ",
            "塩飴・経口補水液を持ち歩け",
        ]
    elif hs_level >= 3:
        pool = [
            "水分：意識して飲め。忘れるから",
            "帽子：かぶるだけで体感が違う",
            "昼休み：涼しい場所で休め",
            "寝る前にコップ1杯の水を飲め",
        ]
    else:
        pool = [
            "水分補給の習慣を続けろ",
            "エアコンの試運転を済ませておけ",
            "明日の天気を確認しておけ",
        ]

    if uv_level >= 4:
        pool.insert(0, "日焼け止め：SPF50を塗り直せ")
    elif uv_level >= 3:
        pool.insert(0, "日焼け止め：2時間ごとに塗り直せ")
    elif uv_level >= 2:
        pool.insert(0, "日焼け止め：外出前に塗っておけ")

    random.shuffle(pool)
    return pool[:3]


# ────────────────────────────────────────
# 締めの一言
# ────────────────────────────────────────
CLOSING_DANGER = [
    "今日は生き延びることが最優先。",
    "我慢は美徳じゃない。エアコンつけろ。",
    "倒れてからでは遅い。今すぐ対策しろ。",
]
CLOSING_SEVERE = [
    "今日は対策した人間だけが無事に帰れる。",
    "準備した人間とそうでない人間で夜の体調が変わる。",
    "水を持って出ろ。それが今日の正解だ。",
]
CLOSING_WARNING = [
    "5分の準備で今日の体調が変わる。",
    "慣れた頃が危ない。続けろ。",
    "水分と日陰。これだけ守れ。",
]
CLOSING_LOW = [
    "マシな日こそ習慣を崩すな。",
    "続けることが、夏を乗り切るコツだ。",
    "油断だけはするな。",
]


def _generate_closing(hs_level: int) -> str:
    if hs_level >= 5:
        return random.choice(CLOSING_DANGER)
    if hs_level >= 4:
        return random.choice(CLOSING_SEVERE)
    if hs_level >= 3:
        return random.choice(CLOSING_WARNING)
    return random.choice(CLOSING_LOW)


# ────────────────────────────────────────
# 熱中症の誤解データベース（mythbust用）
# ────────────────────────────────────────
MYTHS = [
    {"myth": "暑くなければ熱中症にならない", "fact": "湿度が高ければ25℃でも起きる。WBGT（暑さ指数）は気温だけじゃない。"},
    {"myth": "室内なら安全", "fact": "熱中症の約4割は室内で発生する。エアコンなしの部屋は外より危険。"},
    {"myth": "喉が渇いてから水を飲めばいい", "fact": "渇きを感じた時点で体は2%脱水。感じる前に飲め。"},
    {"myth": "お茶やコーヒーで水分補給できる", "fact": "カフェインに利尿作用がある。水か麦茶がベスト。"},
    {"myth": "若いから大丈夫", "fact": "10-20代の運動中の熱中症が毎年大量発生。体力と耐熱性は別。"},
    {"myth": "汗をかかない日は安全", "fact": "湿度が高すぎると汗が蒸発しない。体温が下がらず危険。"},
    {"myth": "日焼け止めは曇りの日は不要", "fact": "曇りでもUVの80%は地表に届く。雲を過信するな。"},
    {"myth": "SPFが高いほど長時間もつ", "fact": "SPF50でも2-3時間で効果が落ちる。塗り直しが必須。"},
    {"myth": "日傘は女性のもの", "fact": "日傘で体感温度が3-7℃下がる。性別関係なく使え。"},
    {"myth": "経口補水液は予防に飲むもの", "fact": "予防は水+塩飴。経口補水液は症状が出てからの回復用。"},
    {"myth": "エアコン28℃設定は暑すぎる", "fact": "28℃は室温目標。設定温度を28℃にしても室温は28℃にならないことが多い。"},
    {"myth": "夜は熱中症にならない", "fact": "夜間熱中症は毎年発生。昼の疲労と脱水が蓄積して夜に発症する。"},
    {"myth": "子どもの暑さは大人と同じ", "fact": "地面に近い子どもは大人より+5℃以上の体感温度。ベビーカーも要注意。"},
    {"myth": "帽子をかぶっていれば大丈夫", "fact": "帽子は頭部の直射を防ぐだけ。水分・休憩・日陰の3つが必要。"},
    {"myth": "紫外線は夏だけの問題", "fact": "5月から9月がピークだが、春と秋もUV指数3以上の日は多い。"},
    {"myth": "色の薄い服が涼しい", "fact": "白は涼しいがUVを通す。黒はUVを防ぐが暑い。ベストは濃い色+通気性。"},
    {"myth": "水をかぶれば体温が下がる", "fact": "首・脇・太ももの付け根を冷やすのが効果的。頭からかぶるより効く。"},
]


# ────────────────────────────────────────
# データ抽出ヘルパー
# ────────────────────────────────────────
def _extract_data(data: IntegratedWeatherData) -> dict:
    hs_num = data.heatstroke_level_num
    hs_arrow = _diff_arrow(data.heatstroke_diff)
    uv_num = data.uv_level_num
    uv_arrow = _diff_arrow(data.uv_diff)
    date_str = _today_jst_str()

    data_line = f"{date_str} 東京　熱中症 {data.heatstroke_level}{hs_arrow}　{_uv_bar(uv_num)}{uv_arrow}"

    weather_bits = []
    if data.high_temp and str(data.high_temp).strip():
        weather_bits.append(f"最高{data.high_temp}℃")
    if data.low_temp and str(data.low_temp).strip():
        weather_bits.append(f"最低{data.low_temp}℃")
    if data.wind and str(data.wind).strip():
        weather_bits.append(str(data.wind))
    if data.weather and str(data.weather).strip() and data.weather != "不明":
        weather_bits.append(str(data.weather))
    weather_summary = "　".join(weather_bits) if weather_bits else ""

    wbgt_line = ""
    if data.wbgt_max > 0:
        wbgt_line = f"WBGT {data.wbgt_max}℃"

    return {
        "hs_num": hs_num, "hs_label": data.heatstroke_level,
        "hs_arrow": hs_arrow,
        "uv_num": uv_num, "uv_label": data.uv_level,
        "uv_arrow": uv_arrow,
        "high_temp": data.high_temp, "low_temp": data.low_temp,
        "wind": data.wind, "weather": data.weather,
        "rain_chance": data.rain_chance,
        "date_str": date_str, "data_line": data_line,
        "weather_summary": weather_summary, "wbgt_line": wbgt_line,
        "wbgt_max": data.wbgt_max,
    }


# ────────────────────────────────────────
# フォーマット選択
# ────────────────────────────────────────
def _choose_format(hs_num: int, uv_num: int) -> str:
    now = datetime.now(JST)
    is_weekend = now.weekday() >= 5

    if hs_num >= 5:
        return "alert"
    if uv_num >= 4:
        return "uv_focus"
    if is_weekend:
        return "weekend"
    return random.choice(["standard", "comparison", "mythbust", "routine"])


# ────────────────────────────────────────
# standard（メイン）
# ────────────────────────────────────────
def _generate_standard(d: dict) -> str:
    hs = d["hs_num"]
    hook = _generate_hook(hs)
    actions = _generate_actions(hs, d["uv_num"], d["weather"])
    closing = _generate_closing(hs)
    hashtags = "#熱中症 #紫外線 #天気予報"

    lines = [hook, d["data_line"]]
    if d["wbgt_line"]:
        lines.append(d["wbgt_line"])
    if d["weather_summary"]:
        lines.append(d["weather_summary"])
    lines += ["", "▼やること"]

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
# alert（危険警報型）
# ────────────────────────────────────────
ALERT_TEMPLATES = [
    "今日の東京、熱中症「{hs_label}」。\n一言だけ言う。外に出るな。\n#熱中症 #猛暑",
    "WBGT {wbgt}℃。\n今日は命を守る日。エアコンをつけろ。水を飲め。\n#熱中症 #天気予報",
    "{date} 東京。熱中症「{hs_label}」。\n15分に1回水を飲め。以上。\n#熱中症 #紫外線",
    "今日の数字を見ろ。WBGT {wbgt}℃。\n対策なしで外出したら倒れる。\n#熱中症 #猛暑",
]

def _generate_alert(d: dict) -> str:
    template = random.choice(ALERT_TEMPLATES)
    return template.format(
        hs_label=d["hs_label"], wbgt=d["wbgt_max"],
        date=d["date_str"],
    )


# ────────────────────────────────────────
# uv_focus（紫外線警報型）
# ────────────────────────────────────────
def _generate_uv_focus(d: dict) -> str:
    uv = d["uv_num"]
    uv_label = d["uv_label"]

    if uv >= 5:
        hook = "今日の紫外線、極端に強い。肌を焼きたくないなら読め。"
    elif uv >= 4:
        hook = "紫外線「非常に強い」。日焼け止め塗ったか？"
    else:
        hook = f"紫外線「{uv_label}」。油断するな。"

    tips = random.choice([
        "日焼け止めはSPF30以上。2時間ごとに塗り直せ。",
        "サングラス＋帽子＋日傘。この3つで8割防げる。",
        "10〜14時が紫外線のピーク。この時間帯の外出を減らせ。",
        "首の後ろを忘れるな。一番焼ける場所だ。",
        "曇りでもUVの80%は届く。天気で判断するな。",
    ])

    closing = _generate_closing(d["hs_num"])
    lines = [hook, "", d["data_line"]]
    if d["weather_summary"]:
        lines.append(d["weather_summary"])
    lines += ["", tips, "", closing, "#紫外線 #UV #日焼け止め"]
    return "\n".join(lines)


# ────────────────────────────────────────
# comparison（昨日比較型）
# ────────────────────────────────────────
COMPARISON_WORSE = [
    "昨日より暑い。覚悟しろ。",
    "昨日大丈夫だったからって油断するな。今日は違う。",
    "数字が上がった。対策を一段強化しろ。",
]
COMPARISON_BETTER = [
    "昨日より少しマシ。でも油断するな。",
    "数字は下がった。でも水は飲め。",
    "少し楽な日。だが続けることが大事。",
]
COMPARISON_SAME = [
    "昨日と同じ。つまり対策も同じでいい。",
    "横ばい。変えなくていい。今日もやれ。",
]

def _generate_comparison(d: dict) -> str:
    arrow = d["hs_arrow"]
    if arrow in ("↑", "↑↑"):
        trend = random.choice(COMPARISON_WORSE)
    elif arrow in ("↓", "↓↓"):
        trend = random.choice(COMPARISON_BETTER)
    else:
        trend = random.choice(COMPARISON_SAME)

    closing = _generate_closing(d["hs_num"])
    lines = [trend, "", d["data_line"]]
    if d["wbgt_line"]:
        lines.append(d["wbgt_line"])
    if d["weather_summary"]:
        lines.append(d["weather_summary"])
    lines += ["", closing, "#熱中症 #紫外線 #天気予報"]
    return "\n".join(lines)


# ────────────────────────────────────────
# weekend（週末対策型）
# ────────────────────────────────────────
WEEKEND_HIGH = [
    "週末のレジャー？水分を1.5倍持て。日陰を確保してから始めろ。",
    "公園？プール？子どもは大人より地面に近い。+5℃で考えろ。",
    "BBQやるなら日陰必須。経口補水液を1本置いておけ。",
]
WEEKEND_LOW = [
    "今日は過ごしやすい週末。でも日焼け止めは忘れるな。",
    "外出日和。水筒を持って出るだけでいい。",
    "マシな日にエアコンの試運転をしておけ。本番で壊れてたら地獄だ。",
]

def _generate_weekend(d: dict) -> str:
    now = datetime.now(JST)
    day_name = "土曜" if now.weekday() == 5 else "日曜"
    hs = d["hs_num"]

    advice = random.choice(WEEKEND_HIGH if hs >= 3 else WEEKEND_LOW)
    closing = _generate_closing(hs)

    lines = [f"{day_name}の暑さ情報。", d["data_line"]]
    if d["wbgt_line"]:
        lines.append(d["wbgt_line"])
    if d["weather_summary"]:
        lines.append(d["weather_summary"])
    lines += ["", advice, "", closing, "#熱中症 #紫外線 #天気予報"]
    return "\n".join(lines)


# ────────────────────────────────────────
# mythbust（誤解破壊型）
# ────────────────────────────────────────
def _generate_mythbust(d: dict) -> str:
    myth_item = random.choice(MYTHS)
    lines = [
        f"「{myth_item['myth']}」",
        "",
        f"→ {myth_item['fact']}",
        "",
        d["data_line"],
        "#熱中症 #紫外線 #天気予報",
    ]
    body = "\n".join(lines)
    if _twitter_len(body) > 278:
        lines = [
            f"「{myth_item['myth']}」",
            f"→ {myth_item['fact']}",
            "#熱中症 #紫外線",
        ]
        body = "\n".join(lines)
    return body


# ────────────────────────────────────────
# routine（ルーティン型）
# ────────────────────────────────────────
ROUTINE_MORNING_HIGH = [
    "水筒に水を入れて出ろ",
    "日焼け止めを塗れ（首の後ろも）",
    "帽子 or 日傘を忘れるな",
    "塩飴を2つポケットに入れろ",
    "昼の外出を最小限にしろ",
]
ROUTINE_MORNING_MID = [
    "水を1本持って出ろ",
    "日焼け止めを塗っておけ",
    "帽子をかぶれ",
    "昼休みは涼しい場所で",
]
ROUTINE_MORNING_LOW = [
    "水分補給を意識しろ",
    "エアコンの設定を確認しておけ",
    "明日の天気を確認しておけ",
]

ROUTINE_EVENING_HIGH = [
    "帰宅したら水をコップ1杯飲め",
    "シャワーで体温を下げろ",
    "寝る前にもう1杯。夜間熱中症を防げ",
    "エアコンはつけたまま寝ろ",
    "明日の水筒と塩飴を準備しておけ",
]
ROUTINE_EVENING_MID = [
    "帰宅後すぐに水を飲め",
    "寝る前にコップ1杯の水",
    "明日の日焼け止めを出しておけ",
    "エアコンのタイマーを設定しろ",
]
ROUTINE_EVENING_LOW = [
    "水分補給だけは続けろ",
    "明日の天気を確認しておけ",
    "エアコンの試運転をしておけ",
]


def _generate_routine(d: dict) -> str:
    hs = d["hs_num"]
    now = datetime.now(JST)
    is_evening = now.hour >= 15

    if is_evening:
        if hs >= 4:
            pool = list(ROUTINE_EVENING_HIGH)
        elif hs >= 2:
            pool = list(ROUTINE_EVENING_MID)
        else:
            pool = list(ROUTINE_EVENING_LOW)
        header = "今夜やること3つ。"
    else:
        if hs >= 4:
            pool = list(ROUTINE_MORNING_HIGH)
        elif hs >= 2:
            pool = list(ROUTINE_MORNING_MID)
        else:
            pool = list(ROUTINE_MORNING_LOW)
        header = "今朝やること3つ。"

    random.shuffle(pool)
    steps = pool[:3]
    lines = [header, d["data_line"], ""]
    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. {step}")
    closing = _generate_closing(hs)
    lines += ["", closing, "#熱中症 #紫外線 #天気予報"]
    return "\n".join(lines)


# ────────────────────────────────────────
# メイン生成
# ────────────────────────────────────────
def generate_tweet(data: IntegratedWeatherData, force_format: Optional[str] = None) -> str:
    d = _extract_data(data)
    fmt = force_format or _choose_format(d["hs_num"], d["uv_num"])

    generators = {
        "standard": _generate_standard,
        "alert": _generate_alert,
        "uv_focus": _generate_uv_focus,
        "comparison": _generate_comparison,
        "weekend": _generate_weekend,
        "mythbust": _generate_mythbust,
        "routine": _generate_routine,
    }

    generator = generators.get(fmt, _generate_standard)
    body = generator(d)

    if _twitter_len(body) > 280 and fmt != "standard":
        body = _generate_standard(d)

    return body
