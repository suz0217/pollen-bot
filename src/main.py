# src/main.py

import os
import tweepy
from tweet_generator import generate_tweet
from data_integrator import integrate_data


def post_to_x(text: str) -> None:
    """
    Xへ投稿（OAuth1.0a）
    Secrets名は TWITTER_〜 に合わせている
    """

    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_SECRET"],
    )

    client.create_tweet(text=text)


def main():
    # 統合データ取得
    data = integrate_data()

    # ツイート生成
    tweet_text = generate_tweet(data)

    # ログ確認用（Actionsで内容が見える）
    print(tweet_text)

    # 投稿
    post_to_x(tweet_text)


if __name__ == "__main__":
    main()