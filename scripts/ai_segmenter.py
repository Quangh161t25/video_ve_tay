#!/usr/bin/env python3
"""
AI Smart Auto-Segmentation module using Google Gemini Vision API with OpenCV fallback.
Phan tich nhan dien doi tuong va thu tu ve bang trang thong minh (Nhan vat -> Do vat -> Hau canh).
"""
import sys
import json
import base64
import urllib.request
import urllib.error
import cv2
import numpy as np
from pathlib import Path

DEFAULT_API_KEY = "AIzaSyCTL1ybG64cdgPHydgTcJS-X2tsiyhQI6Y"

def segment_with_gemini(image_bgr: np.ndarray, api_key: str = None, total_duration_ms: int = 8000) -> dict:
    """Su dung Google Gemini 2.5 Flash Vision de phan tich doi tuong va tao cac vung ve."""
    key = api_key or DEFAULT_API_KEY
    h, w = image_bgr.shape[:2]
    # 1. Thu nhỏ ảnh vừa đủ (max 400px, JPEG 70) để gửi qua Google API chỉ mất 0.2s
    scale = 400.0 / max(h, w)
    small_img = cv2.resize(image_bgr, (max(1, int(round(w * scale))), max(1, int(round(h * scale)))), interpolation=cv2.INTER_AREA)
    _, buffer = cv2.imencode(".jpg", small_img, [cv2.IMWRITE_JPEG_QUALITY, 70])
    b64_image = base64.b64encode(buffer).decode("utf-8")

    prompt = (
        f"Analyze this image for a whiteboard animation drawing sequence.\n"
        f"Image resolution is {w}x{h} pixels.\n\n"
        f"Break this image down into 2 to 4 logical drawing layers/regions, ordered by natural drawing sequence:\n"
        f"1. Main subject / character / central focal point (Nhân vật chính / Tiêu điểm trung tâm)\n"
        f"2. Important secondary objects / foreground props (Đồ vật chính / Chi tiết phụ)\n"
        f"3. Background / scenery / atmosphere (Hậu cảnh / Phông nền)\n\n"
        f"For each region, provide:\n"
        f"- label: Short Vietnamese description (e.g. '1. Nhân vật chính', '2. Bàn ghế & Đồ vật', '3. Hậu cảnh')\n"
        f"- narrativeRole: Brief role description in Vietnamese\n"
        f"- box_2d: [ymin, xmin, ymax, xmax] normalized to 0-1000 scale\n"
        f"- direction: one of ['top_to_bottom', 'left_to_right', 'bottom_to_top', 'right_to_left', 'center_out']\n\n"
        f"Return ONLY a valid JSON array of objects with keys: 'label', 'narrativeRole', 'box_2d', 'direction'."
    )

    models = ["gemini-2.5-flash", "gemini-flash-latest"]
    last_err = None

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_image
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    content_parts = candidates[0].get("content", {}).get("parts", [])
                    if content_parts:
                        text = content_parts[0].get("text", "").strip()
                        if text.startswith("```"):
                            text = text.split("\n", 1)[1]
                            if text.endswith("```"):
                                text = text.rsplit("```", 1)[0]
                        parsed = json.loads(text.strip())
                        if isinstance(parsed, dict) and "elements" in parsed:
                            parsed = parsed["elements"]
                        if isinstance(parsed, list) and len(parsed) > 0:
                            return _build_annotation_config(parsed, w, h, total_duration_ms)
        except Exception as e:
            last_err = e
            print(f"[AI Segmenter] Model {model} failed: {e}")
            continue

    print(f"[AI Segmenter] Gemini API fallback to OpenCV: {last_err}")
    return segment_with_opencv(image_bgr, total_duration_ms)


def segment_with_opencv(image_bgr: np.ndarray, total_duration_ms: int = 8000) -> dict:
    """Co che phan tich du phong cuc bo bang thuat toan OpenCV Saliency & Contour Clusters."""
    h, w = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 40, 120)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > (w * h * 0.01):
            bx, by, bw, bh = cv2.boundingRect(cnt)
            boxes.append((bx, by, bw, bh, area))

    boxes.sort(key=lambda b: b[4], reverse=True)
    
    elements = []
    if len(boxes) >= 1:
        bx, by, bw, bh, _ = boxes[0]
        pad = 20
        x1 = max(0, bx - pad)
        y1 = max(0, by - pad)
        x2 = min(w, bx + bw + pad)
        y2 = min(h, by + bh + pad)
        elements.append({
            "label": "1. Nhân vật / Chủ thể chính",
            "narrativeRole": "Chủ thể trung tâm bức tranh",
            "box_2d": [int(y1 * 1000 / h), int(x1 * 1000 / w), int(y2 * 1000 / h), int(x2 * 1000 / w)],
            "direction": "top_to_bottom"
        })

    elements.append({
        "label": "2. Hạu cảnh & Chi tiết xung quanh",
        "narrativeRole": "Phần bối cảnh xung quanh",
        "box_2d": [0, 0, 1000, 1000],
        "direction": "left_to_right"
    })

    return _build_annotation_config(elements, w, h, total_duration_ms)


def _build_annotation_config(elements_raw: list, w: int, h: int, total_duration_ms: int) -> dict:
    """Chuyen doi danh sach vung raw tu AI sang cau truc annotation.json chuan."""
    elements = []
    count = len(elements_raw)
    
    available_dur = max(3000, total_duration_ms - 1000)
    dur_per_part = round(available_dur / max(1, count))
    
    cur_start = 300
    for idx, raw in enumerate(elements_raw):
        box = raw.get("box_2d", [0, 0, 1000, 1000])
        ymin, xmin, ymax, xmax = box[0], box[1], box[2], box[3]
        
        rx = int(round(xmin * w / 1000.0))
        ry = int(round(ymin * h / 1000.0))
        rw = max(20, int(round((xmax - xmin) * w / 1000.0)))
        rh = max(20, int(round((ymax - ymin) * h / 1000.0)))
        
        rx = max(0, min(w - 10, rx))
        ry = max(0, min(h - 10, ry))
        rw = min(w - rx, rw)
        rh = min(h - ry, rh)
        
        direction = raw.get("direction", "top_to_bottom")
        if direction not in ["top_to_bottom", "left_to_right", "bottom_to_top", "right_to_left", "center_out"]:
            direction = "top_to_bottom"
            
        label = raw.get("label") or f"Vùng {idx + 1}"
        role = raw.get("narrativeRole") or f"Phần {idx + 1} bức tranh"
        
        hand_start = [round(rx + rw / 2), ry + 10]
        hand_end = [round(rx + rw / 2), ry + rh - 10]
        
        elements.append({
            "id": f"part_{idx + 1}",
            "label": label,
            "sequence": idx + 1,
            "narrativeRole": role,
            "subtitle": "",
            "type": "structure" if idx == 0 else "detail",
            "region": {
                "x": rx,
                "y": ry,
                "width": rw,
                "height": rh
            },
            "reveal": {
                "direction": direction,
                "startMs": cur_start,
                "durationMs": dur_per_part,
                "maskPaddingPx": 20,
                "protectedRegions": []
            },
            "handPath": {
                "start": hand_start,
                "end": hand_end,
                "easing": "easeInOut"
            }
        })
        cur_start += dur_per_part

    return {
        "canvas": {
            "width": w,
            "height": h
        },
        "sceneDurationMs": total_duration_ms,
        "elements": elements
    }
