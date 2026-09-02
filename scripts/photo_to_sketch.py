#!/usr/bin/env python3
"""
Chuyển đổi ảnh chụp thật sang tranh vẽ phác thảo (Sketch/Line-art) trên nền giấy bảng trắng #F5EBD7
"""
import sys
import argparse
import cv2
import numpy as np
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def photo_to_sketch(img_bgr, bg_hex="#F5EBD7", stroke_intensity=1.1):
    # 1. Khử nhiễu nhưng giữ cạnh sắc nét bằng Bilateral filter
    smooth = cv2.bilateralFilter(img_bgr, 9, 75, 75)
    gray = cv2.cvtColor(smooth, cv2.COLOR_BGR2GRAY)
    
    # 2. Trích xuất đường viền sắc sảo
    edges = cv2.Canny(gray, 35, 95)
    
    # Lọc bỏ các đốm nhiễu hạt vụn li ti (< 12px) để nét vẽ tinh gọn, tự nhiên
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(edges, connectivity=8)
    clean_edges = np.zeros_like(edges)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= 12:
            clean_edges[labels == i] = 255
            
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    dilated_edges = cv2.dilate(clean_edges, kernel, iterations=1)
    
    # 3. Phủ bóng chì mỹ thuật tự nhiên (không tạo viền tối lem nhem)
    adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 8)
    shading = np.where(adapt < 128, 175, 255).astype(np.uint8)
    
    # Kết hợp nét vẽ chính và đánh bóng nhẹ
    combined = np.where(dilated_edges > 0, 30, shading)
    
    # 4. Trộn lên nền giấy ấm #F5EBD7
    r_bg = int(bg_hex[1:3], 16)
    g_bg = int(bg_hex[3:5], 16)
    b_bg = int(bg_hex[5:7], 16)
    
    h, w = img_bgr.shape[:2]
    out = np.zeros((h, w, 3), dtype=np.uint8)
    ratio = combined.astype(np.float32) / 255.0
    out[:, :, 0] = (ratio * b_bg).astype(np.uint8)
    out[:, :, 1] = (ratio * g_bg).astype(np.uint8)
    out[:, :, 2] = (ratio * r_bg).astype(np.uint8)
    return out

def main():
    parser = argparse.ArgumentParser(description="Chuyển ảnh thật sang tranh phác thảo bảng trắng")
    parser.add_argument("input", help="Đường dẫn ảnh gốc")
    parser.add_argument("output", help="Đường dẫn ảnh phác thảo xuất ra")
    args = parser.parse_args()
    
    inp = Path(args.input)
    if not inp.exists():
        print(f"[ERROR] Không tìm thấy ảnh: {inp}")
        return 1
        
    img = cv2.imread(str(inp))
    sketch = photo_to_sketch(img)
    cv2.imwrite(args.output, sketch)
    print(f"[OK] Đã chuyển đổi thành công: {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
