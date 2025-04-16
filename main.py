from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
from datetime import datetime
import os
import re
import traceback

app = FastAPI()

# CORS許可（GitHub Pagesなどからのアクセス許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 必要に応じて限定可能
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VIDEO_ID = os.getenv("VIDEO_ID", "sm125732")
LOG_FILE = "comment_log.json"

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

# ⭐️ アプリ起動時に自動で1回だけコメント数を保存！
@app.on_event("startup")
def startup_event():
    try:
        count = fetch_comment_count()
        save_comment_count(count)
        print(f"Startup update complete. Count = {count}")
    except Exception as e:
        print(f"Startup update failed: {e}")

@app.get("/")
def read_root():
    return {"message": "Nico Comment Backend is running!"}

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

@app.get("/data")
def get_data():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
    with open(LOG_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    # ログが空なら最新コメント数を自動取得・保存！
    if len(data) == 0:
        try:
            count = fetch_comment_count()
            save_comment_count(count)
            data = [{"time": datetime.now().strftime("%Y-%m-%d %H:%M"), "count": count}]
        except Exception as e:
            # 失敗した場合は空リストのまま
            pass
    return data

