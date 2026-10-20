# -*- coding: utf-8 -*-
"""
daily_runner.py - Tự động hóa tạo video cho tỉnh thành tiếp theo mỗi ngày lúc 9:00 AM
"""
import json
import sys
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "provinces_data.json"
DESKTOP = Path(os.environ.get("USERPROFILE", "C:/Users/ADMIN")) / "Desktop"
OUT_DIR = DESKTOP / "Series_64_Tinh_Thanh"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_db():
    if not DB_PATH.exists():
        return []
    return json.loads(DB_PATH.read_text(encoding="utf-8"))

def save_db(data):
    DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_next_province():
    data = load_db()
    for item in data:
        if item.get("status") == "pending":
            return item
    return None

def mark_completed(province_id, video_path):
    data = load_db()
    for item in data:
        if item["id"] == province_id:
            item["status"] = "completed"
            item["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            item["video_file"] = str(video_path)
            break
    save_db(data)

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    
    p = get_next_province()
    if not p:
        print("[INFO] Chúc mừng! Đã hoàn thành toàn bộ 64 tỉnh thành Việt Nam!")
        return

    print("=" * 60)
    print(f"[*] HÔM NAY THỰC HIỆN TỈNH THÀNH: {p['id']}/64: {p['province']}")
    print(f"    - Miền: {p['region']}")
    print(f"    - Địa danh biểu tượng: {p['landmark']}")
    print(f"    - Thiết kế trang phục: {p['outfit']}")
    print(f"    - Thư mục lưu thành phẩm: {OUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
