from fastapi import FastAPI
import requests
import json
from datetime import datetime
import os

app = FastAPI()

# 動画IDは環境変数から取得（例：sm125732）
VIDEO_ID = os.getenv("VIDEO_ID", "sm125732")
LOG_FILE = "comment_log.json"

# コメント数をニコニコAPIから取得する関数
def fetch_comment_count():
    url = f"https://ext.nicovideo.jp/api/getthumbinfo/{VIDEO_ID}"
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(f"API request failed with status {res.status_code}")
    
    # XMLの中から <comment_num> を探す
    data = res.text
    lines = data.splitlines()
    count_line = next((line for line in lines if "<comment_num>" in line), None)
    if not count_line:
        raise Exception("comment_num not found in API response")
    
    # 数字だけ取り出す
    count = int(count_line.replace("<comment_num>", "").replace("</comment_num>", ""))
    return count

# コメント数を JSON に保存する関数
def save_comment_count(count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    # ファイルが無ければ初期化
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
    # ログ読み込み → 追記 → 保存
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
        # エラーの原因を返す
        return {"status": "error", "message": str(e)}

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
