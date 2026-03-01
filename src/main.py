import os
import tweepy
from scraper_tenki import get_tenki_data


def post_to_x(text: str):
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_SECRET"],
    )

    client.create_tweet(text=text)


def main():
    data = get_tenki_data()

    if not data:
        print("データ取得失敗")
        return

    tweet_text = (
        f"🌸 本日の花粉予報（東京都千代田区）\n"
        f"{data.date}\n"
        f"花粉レベル：{data.pollen_level}（{data.pollen_level_num}/5）\n"
        f"#花粉 #花粉予報"
    )

    print(tweet_text)

    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if not dry_run:
        post_to_x(tweet_text)


if __name__ == "__main__":
    main()