“””
花粉予報Bot メインスクリプト
毎朝GitHub Actionsから実行される

パイプライン:

1. tenki.jp + Google Pollen API からデータ取得
1. データ統合 + 前日比算出
1. ツイート文生成（テンプレート + 条件別アクション + 最後の一言）
1. X API Free Tier で投稿
   “””

import os
import sys
import json
from datetime import datetime

# srcディレクトリをパスに追加

sys.path.insert(0, os.path.dirname(os.path.abspath(**file**)))

from data_integrator import integrate_data
from tweet_generator import generate_tweet
from twitter_poster import TwitterPoster

def main():
print(f”=== 花粉予報Bot 実行開始 [{datetime.now().isoformat()}] ===\n”)

```
dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

# Step 1 & 2: データ取得 + 統合
print("[Step 1] データ取得・統合中...")
data = integrate_data()

if data is None:
    print("[FATAL] データ取得に完全失敗。ツイートを中止します。")
    sys.exit(1)

print(f"  スギ: {data.sugi_level} (前日比{data.sugi_diff})")
print(f"  ヒノキ: {data.hinoki_level} (前日比{data.hinoki_diff})")
print(f"  天気: {data.weather} 最高{data.high_temp}℃")
print(f"  ソース: {data.data_sources}")
print()

# Step 3: ツイート生成
print("[Step 2] ツイート生成中...")
tweet = generate_tweet(data)
print("--- 生成ツイート ---")
print(tweet)
print(f"--- (文字数: {len(tweet)}) ---\n")

# Step 4: 投稿
if dry_run:
    print("[Step 3] DRY RUN モード - 投稿をスキップ")
    print("[SUCCESS] テスト完了")
    return

print("[Step 3] X(Twitter)に投稿中...")
try:
    poster = TwitterPoster()
    result = poster.post_tweet(tweet)

    if "error" in result:
        print(f"[ERROR] 投稿失敗: {result}")
        sys.exit(1)
    else:
        print("[SUCCESS] 投稿完了!")

except ValueError as e:
    print(f"[ERROR] Twitter認証エラー: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] 予期せぬエラー: {e}")
    sys.exit(1)

print(f"\n=== 花粉予報Bot 実行完了 [{datetime.now().isoformat()}] ===")
```

if **name** == “**main**”:
main()
