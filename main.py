from fastapi import FastAPI
import requests
import json
from datetime import datetime
import os
import traceback

app = FastAPI()

VIDEO_ID = os.getenv("VIDEO_ID", "sm125732")
LOG_FILE = "comment_log.json"

def fetch_comment_count():
    url = f"https://ext.nicovideo.jp/api/getthumbinfo/{VIDEO_ID}"
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(f"API request failed with status {res.status_code}")
    data = res.text
    lines = data.splitlines()
    count_line = next((line for line in lines if "<comment_num>" in line), None)
    if not count_line:
        raise Exception("comment_num not found in API response")
    count = int(count_line.replace("<comment_num>", "").replace("</comment_num>", ""))
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
        # 👇 詳細なトレースバック付きで返す
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }

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
