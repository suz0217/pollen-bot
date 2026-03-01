“””
ツイート生成モジュール
統合データからツイート文を生成する

テンプレート構造:
【花粉症の人へ】
{日付} 東京
スギ：{レベル}（前日比{↑↓→}）
ヒノキ：{レベル}（前日比{↑↓→}）
最高{気温}℃ / {風} / {天気}

▼ 今日やること
・{条件別アクション 3〜5個}

{最後の一言}
“””

import random
from datetime import datetime
from data_integrator import IntegratedPollenData

def generate_tweet(data: IntegratedPollenData) -> str:
“”“統合データからツイート文を生成”””

```
# ヘッダー
header = f"【花粉症の人へ】\n{data.date}({data.day_of_week}) 東京"

# 花粉データ行
sugi_line = f"スギ：{data.sugi_level}（前日比{data.sugi_diff}）"
hinoki_line = f"ヒノキ：{data.hinoki_level}（前日比{data.hinoki_diff}）"

# 気象行
weather_parts = [f"最高{data.high_temp}℃"]
if data.wind and data.wind != "不明":
    weather_parts.append(data.wind)
if data.weather and data.weather != "不明":
    weather_parts.append(data.weather)
weather_line = " / ".join(weather_parts)

# アクション指示
actions = _generate_actions(data)
actions_block = "▼ 今日やること\n" + "\n".join(f"・{a}" for a in actions)

# 最後の一言
closing = _generate_closing(data)

# 組み立て
tweet = f"""{header}
```

{sugi_line}
{hinoki_line}
{weather_line}

{actions_block}

{closing}”””

```
# 280文字制限チェック（日本語は1文字=2としてカウント）
tweet = _trim_to_limit(tweet)

return tweet
```

def _generate_actions(data: IntegratedPollenData) -> list[str]:
“””
条件に応じたアクション指示を生成
花粉レベル × 気象条件の組み合わせで出し分け
“””
actions = []
sugi = data.sugi_level_num
hinoki = data.hinoki_level_num
combined = max(sugi, hinoki)

```
# === 花粉レベル別ベースアクション ===

if combined >= 5:
    # 極めて多い
    actions.append("薬は外出30分前に必ず飲む")
    actions.append("マスクは不織布二重かN95が正解")
    actions.append("帰宅後すぐシャワー、服は玄関で払う")
    actions.append("布団・洗濯物は絶対に外に干さない")
    actions.append("コンタクトよりメガネ推奨")

elif combined >= 4:
    # 非常に多い
    actions.append("薬は外出前に飲んでおく")
    actions.append("不織布マスク必須、できれば立体型")
    actions.append("帰宅後は顔を洗って服を着替える")
    actions.append("洗濯物は部屋干しが安全")

elif combined >= 3:
    # 多い
    actions.append("薬を忘れずに")
    actions.append("マスクは不織布で")
    actions.append("帰ったら手洗い・うがいに加えて顔も洗う")

elif combined >= 2:
    # やや多い
    actions.append("念のためマスクはしておく")
    actions.append("症状が出やすい人は薬を飲んでおく")

else:
    # 少ない
    actions.append("今日はマスクなしでもいける人が多い")
    actions.append("ただし油断は禁物、薬は携帯しておく")

# === 気象条件による追加アクション ===

# 風が強い日
wind_text = data.wind.lower() if data.wind else ""
if "強" in wind_text or "やや強" in wind_text:
    actions.append("風が強いので花粉が舞いやすい。外出は午前中に")

# 雨の日
if data.weather and ("雨" in data.weather):
    # 雨の日は花粉が少ない → 逆にチャンス情報
    if combined >= 3:
        actions.insert(0, "雨で花粉は抑えめ。買い物やるなら今日")
        # 過剰なアクションを削除
        actions = [a for a in actions if "N95" not in a and "二重" not in a]

# 晴れ＋気温高い（花粉飛びやすい）
try:
    temp = int(data.high_temp)
    if temp >= 18 and data.weather and "晴" in data.weather and combined >= 3:
        actions.append("気温高め＋晴れで花粉が飛びやすい条件")
except (ValueError, TypeError):
    pass

# 週末判定
now = datetime.now()
if now.weekday() >= 5 and combined >= 3:  # 土日
    actions.append("外出するなら午前中が比較的マシ")

# ヒノキが強い場合の追加
if hinoki >= 3 and sugi >= 3:
    actions.append("スギ＋ヒノキのダブルパンチ。アレグラで効かない人は受診を")
elif hinoki >= 3:
    actions.append("ヒノキが本格化。スギ用の薬が効かない人はヒノキかも")

# 最大5個に制限
return actions[:5]
```

def _generate_closing(data: IntegratedPollenData) -> str:
“””
最後の一言を生成
花粉レベルと条件に基づいて選択
“””
sugi = data.sugi_level_num
combined = max(sugi, data.hinoki_level_num)

```
if combined >= 5:
    return random.choice(CLOSING_EXTREME)
elif combined >= 4:
    return random.choice(CLOSING_SEVERE)
elif combined >= 3:
    return random.choice(CLOSING_MODERATE)
elif combined >= 2:
    return random.choice(CLOSING_MILD)
else:
    return random.choice(CLOSING_LOW)
```

# === 最後の一言バリエーション ===

CLOSING_EXTREME = [
“今日は正直、外に出たくない。”,
“都内の空気、もはや凶器。”,
“ティッシュは1箱カバンに入れたほうがいい。”,
“花粉症じゃない人には絶対わからない日。”,
“今日外に出る人、覚悟だけは持っていってください。”,
“マスクの下で鼻水が止まらない日。”,
“これはもう天災。”,
“空気がザラつく日。”,
“耳鼻科が混む日。朝イチで行くべき。”,
“花粉のピーク、毎年こんなにキツかったっけ。”,
]

CLOSING_SEVERE = [
“油断するとやられる日。”,
“昨日よりキツい。体感でわかるレベル。”,
“薬飲み忘れると午後から地獄になる。”,
“電車で隣の人がずっと鼻すすってたら、それは自分かもしれない。”,
“目を擦りたくなるけど、擦ると悪化する。我慢。”,
“マスクの隙間から入ってくるのが一番つらい。”,
“ワセリンを鼻の穴に塗ると少しマシになる。本当に。”,
“帰ったら玄関で服を払う。これだけで夜が変わる。”,
]

CLOSING_MODERATE = [
“まだ耐えられるけど、午後から増えるパターン。”,
“昼過ぎに症状出始めたら、すぐ薬飲んで。”,
“今日くらいならマスクだけでなんとかなる。”,
“症状軽い人は気づかないかもしれないけど、飛んでる。”,
“花粉症歴が長い人ほど、今日の微妙さがわかるはず。”,
]

CLOSING_MILD = [
“今日は比較的マシな日。”,
“油断して薬飲まないと夕方に後悔するのがこの時期。”,
“軽症の人は今日は薬なしでいけるかも。”,
“マシな日こそ、明日に備えて体を休めておく。”,
]

CLOSING_LOW = [
“今日は久しぶりに人間として生きられる。”,
“窓を開けていい日がこんなに嬉しいとは。”,
“今日は換気と布団干しのチャンス。”,
“花粉が少ない日は貴重。有効活用してください。”,
“この平穏がいつまで続くかは、誰にもわからない。”,
]

def _trim_to_limit(tweet: str, max_chars: int = 280) -> str:
“””
X(Twitter)の文字数制限に収める
日本語は1文字=2文字としてカウントされる
実質140全角文字程度
“””
# Twitter API v2では日本語1文字=2としてカウント
def twitter_length(text: str) -> int:
count = 0
for ch in text:
if ord(ch) > 127:
count += 2
else:
count += 1
return count

```
current_len = twitter_length(tweet)
if current_len <= max_chars:
    return tweet

# アクションを1個ずつ削って調整
lines = tweet.split("\n")
while twitter_length("\n".join(lines)) > max_chars and len(lines) > 5:
    # 後ろから「・」で始まる行を削除
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("・"):
            lines.pop(i)
            break
    else:
        break

return "\n".join(lines)
```

if **name** == “**main**”:
# テスト用のモックデータ
mock_data = IntegratedPollenData(
date=“3/1”,
day_of_week=“土”,
sugi_level=“非常に多い”,
sugi_level_num=4,
hinoki_level=“少ない”,
hinoki_level_num=1,
sugi_diff=“↑↑”,
hinoki_diff=“→”,
weather=“晴れ”,
high_temp=“15”,
low_temp=“5”,
wind=“南風やや強い”,
humidity=“40%”,
rain_probability=“10/10/20/10”,
data_sources=[“tenki.jp”, “google_pollen”],
confidence=“high”,
)

```
tweet = generate_tweet(mock_data)
print("=== 生成ツイート ===")
print(tweet)
print(f"\n文字数: {len(tweet)}文字")
```
