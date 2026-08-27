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
    # 1. Chuyển sang ảnh xám và khử nhiễu
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    smooth = cv2.bilateralFilter(gray, 7, 50, 50)
    
    # 2. Tạo nét đổ bóng bút chì (Dodge blend)
    inv = 255 - smooth
    blur = cv2.GaussianBlur(inv, (21, 21), 0)
    sketch = cv2.divide(smooth, 255 - blur, scale=256.0)
    
    # 3. Thêm đường viền nét chì sắc nét (Canny edge)
    edges = cv2.Canny(smooth, 30, 100)
    edges_inv = 255 - edges
    
    # Kết hợp nét vẽ và đổ bóng chì
    combined = np.minimum(sketch, edges_inv)
    combined = np.clip((combined.astype(np.float32) / 255.0) ** stroke_intensity * 255.0, 0, 255).astype(np.uint8)
    
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
