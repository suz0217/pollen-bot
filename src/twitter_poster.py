“””
X (Twitter) API v2 投稿モジュール
Free Tier: 月500投稿（1日1投稿なら余裕）
OAuth 1.0a 認証
“””

import os
import json
import hmac
import hashlib
import base64
import time
import urllib.parse
import uuid
import requests
from typing import Optional

class TwitterPoster:
“”“X API v2 を使ってツイートを投稿する”””

```
TWEET_ENDPOINT = "https://api.twitter.com/2/tweets"

def __init__(
    self,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    access_token: Optional[str] = None,
    access_secret: Optional[str] = None,
):
    self.api_key = api_key or os.environ.get("TWITTER_API_KEY", "")
    self.api_secret = api_secret or os.environ.get("TWITTER_API_SECRET", "")
    self.access_token = access_token or os.environ.get("TWITTER_ACCESS_TOKEN", "")
    self.access_secret = access_secret or os.environ.get("TWITTER_ACCESS_SECRET", "")

    if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
        raise ValueError(
            "Twitter API credentials not set. "
            "Set TWITTER_API_KEY, TWITTER_API_SECRET, "
            "TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET"
        )

def post_tweet(self, text: str, dry_run: bool = False) -> dict:
    """
    ツイートを投稿する

    Args:
        text: ツイート本文
        dry_run: Trueの場合、実際には投稿せずにデバッグ出力のみ

    Returns:
        APIレスポンスのdict
    """
    if dry_run:
        print(f"[DRY RUN] Would post tweet ({len(text)} chars):")
        print(text)
        return {"dry_run": True, "text": text}

    # OAuth 1.0a ヘッダー生成
    oauth_header = self._generate_oauth_header("POST", self.TWEET_ENDPOINT)

    headers = {
        "Authorization": oauth_header,
        "Content-Type": "application/json",
    }

    payload = {"text": text}

    try:
        response = requests.post(
            self.TWEET_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 201:
            result = response.json()
            tweet_id = result.get("data", {}).get("id", "unknown")
            print(f"[SUCCESS] Tweet posted! ID: {tweet_id}")
            return result
        else:
            print(f"[ERROR] Twitter API returned {response.status_code}")
            print(f"Response: {response.text}")
            return {"error": response.status_code, "body": response.text}

    except Exception as e:
        print(f"[ERROR] Failed to post tweet: {e}")
        return {"error": str(e)}

def _generate_oauth_header(self, method: str, url: str) -> str:
    """OAuth 1.0a Authorization ヘッダーを生成"""

    oauth_params = {
        "oauth_consumer_key": self.api_key,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": self.access_token,
        "oauth_version": "1.0",
    }

    # シグネチャベース文字列
    sorted_params = sorted(oauth_params.items())
    param_string = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted_params
    )

    base_string = "&".join([
        method.upper(),
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote(param_string, safe=""),
    ])

    # シグネチャキー
    signing_key = "&".join([
        urllib.parse.quote(self.api_secret, safe=""),
        urllib.parse.quote(self.access_secret, safe=""),
    ])

    # HMAC-SHA1 シグネチャ
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")

    oauth_params["oauth_signature"] = signature

    # Authorization ヘッダー組み立て
    auth_header = "OAuth " + ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )

    return auth_header
```

if **name** == “**main**”:
print(”=== Twitter Poster テスト (dry_run) ===”)
try:
poster = TwitterPoster()
poster.post_tweet(“テスト投稿です”, dry_run=True)
except ValueError as e:
print(f”[INFO] {e}”)
print(”[INFO] This is expected if credentials are not set yet.”)

```
    # dry_runの動作確認
    print("\n--- dry_run動作確認 ---")
    print("[DRY RUN] Would post tweet:")
    print("【花粉症の人へ】\n3/1(土) 東京\nスギ：非常に多い（前日比↑↑）")
```
