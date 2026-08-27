#!/usr/bin/env python3
"""
Server web cục bộ phục vụ giao diện preview.html và API render video
"""
import http.server
import json
import os
import subprocess
import sys
import urllib.parse
import webbrowser
import cv2
import numpy as np
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PORT = 8000

class WhiteboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def do_POST(self):
        if self.path == "/api/render":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                img_path = ROOT_DIR / data.get("image", "")
                ann_path = ROOT_DIR / data.get("annotation", "")
                out_path = ROOT_DIR / data.get("output", "output.mp4")
                hand_path = ROOT_DIR / "assets" / "drawing-hand.png"
                
                # Hỗ trợ tải ảnh trực tiếp dạng base64 từ trình duyệt
                if "imageDataBase64" in data and data["imageDataBase64"]:
                    import base64
                    img_b64 = data["imageDataBase64"]
                    if "," in img_b64:
                        img_b64 = img_b64.split(",", 1)[1]
                    img_bytes = base64.b64decode(img_b64)
                    upload_dir = ROOT_DIR / "uploads"
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    scene_name = data.get("sceneName", "scene_upload")
                    img_path = upload_dir / f"{scene_name}.png"
                    ann_path = upload_dir / f"{scene_name}.annotation.json"
                    out_path = upload_dir / f"{scene_name}_whiteboard.mp4"
                    img_path.write_bytes(img_bytes)

                # Nếu client gửi kèm cấu hình json mới thì lưu lại trước khi render
                if "annotationData" in data and ann_path:
                    ann_path.parent.mkdir(parents=True, exist_ok=True)
                    ann_path.write_text(json.dumps(data["annotationData"], ensure_ascii=False, indent=2), encoding="utf-8")

                venv_py = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
                if not venv_py.exists():
                    venv_py = Path(sys.executable)

                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"

                style_mode = data.get("style_mode", "photo_sync")
                render_img_path = img_path
                # Nếu người dùng chọn kiểu Phác thảo (Sketch)
                if style_mode == "sketch":
                    sketch_path = img_path.parent / f"{img_path.stem}_sketch.png"
                    subprocess.run([
                        str(venv_py),
                        str(ROOT_DIR / "scripts" / "photo_to_sketch.py"),
                        str(img_path),
                        str(sketch_path)
                    ], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
                    if sketch_path.exists():
                        render_img_path = sketch_path

                color_timing = "after-all" if style_mode == "photo_after_all" else "sync"
                aspect_ratio = data.get("aspect_ratio", "auto")
                cmd = [
                    str(venv_py),
                    str(ROOT_DIR / "scripts" / "render_stream_whiteboard.py"),
                    str(render_img_path),
                    str(ann_path),
                    str(out_path),
                    str(hand_path),
                    "--ink-path", data.get("ink_path", "grid"),
                    "--color-fill", data.get("color_fill", "contour-wipe"),
                    "--color-timing", color_timing,
                    "--aspect-ratio", aspect_ratio,
                    "--cap-long-edge", "960"
                ]
                
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
                if proc.returncode == 0:
                    rel_output = out_path.relative_to(ROOT_DIR).as_posix()
                    resp = {"status": "ok", "message": "Render thành công", "output": rel_output, "downloadUrl": "/" + rel_output}
                else:
                    resp = {"status": "error", "message": "Lỗi render: " + proc.stderr.strip()[:300]}
            except Exception as e:
                resp = {"status": "error", "message": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/api/render_batch":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                scenes = data.get("scenes", [])
                style_mode = data.get("style_mode", "photo_sync")
                aspect_ratio = data.get("aspect_ratio", "auto")
                merge_all = data.get("merge", True)
                
                venv_py = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
                if not venv_py.exists():
                    venv_py = Path(sys.executable)

                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                hand_path = ROOT_DIR / "assets" / "drawing-hand.png"
                upload_dir = ROOT_DIR / "uploads"
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                out_files = []
                for i, sc in enumerate(scenes):
                    raw_name = sc.get("name", f"scene_{i+1}")
                    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in raw_name)
                    if not safe_name:
                        safe_name = f"scene_{i+1}"
                    
                    img_path = ROOT_DIR / sc.get("image", "")
                    ann_path = ROOT_DIR / sc.get("annotation", "")
                    out_path = upload_dir / f"{safe_name}_whiteboard.mp4"
                    
                    if "imageDataBase64" in sc and sc["imageDataBase64"]:
                        import base64
                        b64 = sc["imageDataBase64"]
                        if "," in b64:
                            b64 = b64.split(",", 1)[1]
                        img_path = upload_dir / f"{safe_name}.png"
                        img_path.write_bytes(base64.b64decode(b64))
                    
                    if "annotationData" in sc and sc["annotationData"]:
                        ann_path = upload_dir / f"{safe_name}.annotation.json"
                        ann_path.write_text(json.dumps(sc["annotationData"], ensure_ascii=False, indent=2), encoding="utf-8")
                    
                    render_img = img_path
                    if style_mode == "sketch":
                        sketch_path = img_path.parent / f"{img_path.stem}_sketch.png"
                        subprocess.run([
                            str(venv_py), str(ROOT_DIR / "scripts" / "photo_to_sketch.py"),
                            str(img_path), str(sketch_path)
                        ], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
                        if sketch_path.exists():
                            render_img = sketch_path
                            
                    color_timing = "after-all" if style_mode == "photo_after_all" else "sync"
                    cmd = [
                        str(venv_py),
                        str(ROOT_DIR / "scripts" / "render_stream_whiteboard.py"),
                        str(render_img),
                        str(ann_path),
                        str(out_path),
                        str(hand_path),
                        "--ink-path", "grid",
                        "--color-fill", "contour-wipe",
                        "--color-timing", color_timing,
                        "--aspect-ratio", aspect_ratio,
                        "--cap-long-edge", "960"
                    ]
                    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
                    if proc.returncode == 0 and out_path.exists():
                        out_files.append(out_path)
                    else:
                        print(f"[err] Lỗi render scene {safe_name}: {proc.stderr.strip()[:200]}")

                if not out_files:
                    resp = {"status": "error", "message": "Không có cảnh nào render thành công"}
                else:
                    merged_rel = None
                    if merge_all and len(out_files) > 1:
                        merged_out = upload_dir / "merged_story_whiteboard.mp4"
                        merge_cmd = [str(venv_py), str(ROOT_DIR / "scripts" / "merge_scenes.py"), "--inputs"] + [str(p) for p in out_files] + ["--output", str(merged_out)]
                        m_proc = subprocess.run(merge_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
                        if m_proc.returncode == 0 and merged_out.exists():
                            merged_rel = merged_out.relative_to(ROOT_DIR).as_posix()

                    rel_outputs = [p.relative_to(ROOT_DIR).as_posix() for p in out_files]
                    final_dl = ("/" + merged_rel) if merged_rel else ("/" + rel_outputs[0])
                    resp = {
                        "status": "ok",
                        "message": f"Render thành công {len(out_files)} cảnh!",
                        "outputs": rel_outputs,
                        "merged": merged_rel,
                        "downloadUrl": final_dl
                    }
            except Exception as e:
                resp = {"status": "error", "message": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/api/ai_segment":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                api_key = data.get("apiKey") or None
                total_ms = int(data.get("totalMs", 8000))
                
                img_bgr = None
                if "imageDataBase64" in data and data["imageDataBase64"]:
                    import base64
                    b64 = data["imageDataBase64"]
                    if "," in b64:
                        b64 = b64.split(",", 1)[1]
                    img_bytes = base64.b64decode(b64)
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                elif "image" in data and data["image"]:
                    img_path = ROOT_DIR / data["image"]
                    if not img_path.exists():
                        img_path = ROOT_DIR / "uploads" / data["image"]
                    if img_path.exists():
                        img_bgr = cv2.imdecode(np.fromfile(str(img_path), dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if img_bgr is None:
                    resp = {"status": "error", "message": "Không tìm thấy dữ liệu hình ảnh"}
                else:
                    from scripts.ai_segmenter import segment_with_gemini
                    ann_data = segment_with_gemini(img_bgr, api_key=api_key, total_duration_ms=total_ms)
                    resp = {
                        "status": "ok",
                        "message": "AI phân vùng thành công",
                        "annotation": ann_data
                    }
            except Exception as e:
                resp = {"status": "error", "message": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

def main():
    server_class = getattr(http.server, "ThreadingHTTPServer", http.server.HTTPServer)
    server = server_class(("127.0.0.1", PORT), WhiteboardHandler)
    url = f"http://127.0.0.1:{PORT}/assets/preview.html"
    print(f"========================================================")
    print(f"  SRT Whiteboard Web Server dang chay tai:")
    print(f"  -> {url}")
    print(f"  (Nhan Ctrl+C de dung server)")
    print(f"========================================================")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDa dung server.")

if __name__ == "__main__":
    main()
