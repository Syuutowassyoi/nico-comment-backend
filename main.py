from fastapi import FastAPI
import requests
import json
from datetime import datetime
import os

app = FastAPI()
VIDEO_ID = os.getenv("VIDEO_ID", "sm125732")
LOG_FILE = "comment_log.json"

def fetch_comment_count():
    url = f"https://ext.nicovideo.jp/api/getthumbinfo/{VIDEO_ID}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.text
    count_line = [line for line in data.splitlines() if "<comment_num>" in line]
    if not count_line:
        return None
    count = int(count_line[0].replace("<comment_num>", "").replace("</comment_num>", ""))
    return count

def save_comment_count(count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
    with open(LOG_FILE, "r") as f:
        data = json.load(f)
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
        import traceback
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
        data = json.load(f)
    return data
