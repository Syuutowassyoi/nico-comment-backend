from fastapi import FastAPI
import requests
import json
from datetime import datetime
import os
import re
import traceback

app = FastAPI()

# 環境変数から動画IDを取得
VIDEO_ID = os.getenv("VIDEO_ID", "sm125732")
LOG_FILE = "comment_log.json"

# コメント数をニコニコAPIから取得（正規表現で抽出）
def fetch_comment_count():
    url = f"https://ext.nicovideo.jp/api/getthumbinfo/{VIDEO_ID}"
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(f"API request failed with status {res.status_code}")
    
    match = re.search(r"<comment_num>(\d+)</comment_num>", res.text)
    if not match:
        raise Exception("comment_num not found in API response")
    
    count = int(match.group(1))
    return count

# コメント数をログファイルに保存
def save_comment_count(count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
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

# テスト用エンドポイント
@app.get("/")
def read_root():
    return {"message": "Nico Comment Backend is running!"}

# コメント数を更新するエンドポイント
@app.get("/update")
def update_count():
    try:
        count = fetch_comment_count()
        if count is not None:
            save_comment_count(count)
            return {"status": "success", "count": count}
        return {"status": "no count"}
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }

# ログを取得するエンドポイント
@app.get("/data")
def get_data():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    return data
