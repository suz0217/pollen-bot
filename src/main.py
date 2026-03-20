import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import tweepy

from tweet_generator import generate_tweet
from data_integrator import integrate_data


HISTORY_FILE = os.getenv("POLLEN_HISTORY_FILE", "pollen_history.json")
JST = ZoneInfo("Asia/Tokyo")


# =========================
# 投稿履歴管理
# =========================

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_history(history: dict):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def already_posted(slot: str = "default") -> bool:
    """スロット（時間帯）ごとに重複チェック"""
    today = datetime.now(JST).strftime("%Y-%m-%d")
    history = load_history()
    posted = history.get("posted_slots", {})
    return posted.get(slot) == today


def mark_posted(slot: str = "default"):
    """スロット（時間帯）ごとに投稿済みマーク"""
    today = datetime.now(JST).strftime("%Y-%m-%d")
    history = load_history()
    if "posted_slots" not in history:
        history["posted_slots"] = {}
    # 日付が変わったらリセット
    if history.get("last_posted_date") != today:
        history["posted_slots"] = {}
    history["posted_slots"][slot] = today
    history["last_posted_date"] = today
    save_history(history)


# =========================
# X投稿
# =========================

def post_to_x(text: str) -> None:
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_SECRET"],
    )

    client.create_tweet(text=text)


# =========================
# メイン処理
# =========================

def main():
    # 環境変数からフォーマットとスロットを取得
    force_format = os.getenv("TWEET_FORMAT", "").strip() or None
    slot = os.getenv("TWEET_SLOT", "default").strip()

    # すでにこのスロットで投稿していたらスキップ
    if already_posted(slot):
        print(f"Already posted for slot '{slot}' today. Skip.")
        return

    # データ取得
    data = integrate_data()

    # ツイート生成
    tweet_text = generate_tweet(data, force_format=force_format)

    print(f"[slot={slot}, format={force_format or 'auto'}]")
    print(tweet_text)

    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    if dry_run:
        print("DRY_RUN=true, skipping post.")
        return

    try:
        post_to_x(tweet_text)
        mark_posted(slot)
        print("Posted successfully.")
    except tweepy.errors.Forbidden as e:
        print("403 Forbidden - Duplicate or permission issue.")
        print(e)
    except Exception as e:
        print("Unexpected error:")
        print(e)


if __name__ == "__main__":
    main()
