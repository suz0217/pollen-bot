# main.py
import os
from dotenv import load_dotenv

# ✅ ここが肝：必ず「あなたが編集した tweet_generator.py」を呼ぶ
from tweet_generator import generate_tweet

# データ統合（プロジェクト側の実装に合わせて import 名は存在する前提）
from data_integrator import integrate_data

# X投稿
import tweepy


def post_to_x(text: str) -> None:
    """Xへ投稿（OAuth 2.0 / User context）"""
    client = tweepy.Client(
        consumer_key=os.environ["X_CONSUMER_KEY"],
        consumer_secret=os.environ["X_CONSUMER_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    client.create_tweet(text=text)


def main() -> None:
    load_dotenv()

    # 例：東京に固定（区は不要にするなら integrator 側で location を '東京' に）
    # ここでは integrator が内部で必要な地点を取る想定
    data = integrate_data()

    tweet_text = generate_tweet(data)

    # ログ出し（Actions のログで内容確認できる）
    print(tweet_text)

    post_to_x(tweet_text)


if __name__ == "__main__":
    main()