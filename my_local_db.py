import streamlit as st
import json
import os
from datetime import datetime
import uuid
from datetime import datetime


# ---------- Config ----------
DATA_FILE = "chat_history.json"
USER_ID = "user_123"  # Static for now, can be dynamic in real app

# ---------- Helpers ----------
def load_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(DATA_FILE, "w") as f:
        json.dump(history, f, indent=4)

def add_message(user_id, thread_id, role, message):
    history = load_history()
    if user_id not in history:
        history[user_id] = {}
    if thread_id not in history[user_id]:
        history[user_id][thread_id] = []
    history[user_id][thread_id].append({
        "role": role,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    save_history(history)

def get_all_users():
    data=load_history()
    return list(data.keys())

def get_thread_messages(user_id, thread_id):
    history = load_history()
    if user_id in history and thread_id in history[user_id]:
        return sorted(history[user_id][thread_id], key=lambda x: x["timestamp"])
    return []



from datetime import datetime

def get_latest_thread_for_user(data, user_id):
    if user_id not in data:
        return None, []  # user doesn't exist

    # Keep only threads with at least one message
    threads = {
        tid: msgs
        for tid, msgs in data[user_id].items()
        if msgs
    }

    if not threads:
        return None, []  # no non-empty threads

    latest_thread = max(
        threads.items(),
        key=lambda t: max(datetime.fromisoformat(msg["timestamp"]) for msg in t[1])
    )[0]

    return latest_thread, list(threads.keys())

