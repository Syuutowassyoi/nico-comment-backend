from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
from datetime import datetime, timezone, timedelta
import os
import re
import traceback

app = FastAPI()

# CORS許可（GitHub Pagesなどからアクセス可能に）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 必要に応じてドメイン限定可能
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VIDEO_ID = os.getenv("VIDEO_ID", "sm125732")
LOG_FILE = "comment_log.json"
JST = timezone(timedelta(hours=9))  # 日本時間

# コメント数を取得
def fetch_comment_count():
    url = f"https://ext.nicovideo.jp/api/getthumbinfo/{VIDEO_ID}"
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(f"API request failed with status {res.status_code}")

    match = re.search(r"<comment_num>(\d+)</comment_num>", res.text)
    if not match:
        # デバッグ用にログ出力（必要に応じてコメントアウト可）
        print("API response (partial):", res.text[:500])
        raise Exception("comment_num not found in API response")

    count = int(match.group(1))
    return count

# ログに保存（JST）
def save_comment_count(count):
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M")
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
    with open(LOG_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    data.append({"time": now, "count": count})
    with open(LOG_FILE, "w") as f:
        json.dump(data, f)

# 起動時に1件保存（初期化目的）
@app.on_event("startup")
def startup_event():
    try:
        count = fetch_comment_count()
        save_comment_count(count)
        print(f"Startup fetch success: {count}")
    except Exception as e:
        print("Startup fetch failed:", e)

@app.get("/")
def read_root():
    return {"message": "Nico Comment Backend is running!"}

# コメント取得＆保存（更新用）
@app.get("/update")
def update_count():
    try:
        count = fetch_comment_count()
        if count is not None:
            save_comment_count(count)
            return {"status": "success", "count": count}
        return {"status": "no count"}
    except Exception as e:
        # エラー時も落とさず、詳細に返す
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }

# ログ取得（フロント用）
@app.get("/data")
def get_data():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        try:
