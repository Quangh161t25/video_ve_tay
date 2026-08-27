#!/usr/bin/env python3
"""
多幕合并：把各场景的白板动画 MP4 按顺序硬切拼接成一条完整视频。

优先用系统 ffmpeg 无损拼接（-c copy，不重编码）；各片尺寸/编码不一致或无
ffmpeg 时，回退到 PyAV 逐帧重编码并缩放补边到第一段尺寸。单片仍保留。

用法：
  <ENV_PY> merge_scenes.py --inputs a.mp4 b.mp4 c.mp4 --output final.mp4
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def _ffmpeg_concat_copy(inputs: list[Path], output: Path) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in inputs:
            f.write(f"file '{p.resolve().as_posix()}'\n")
        list_path = Path(f.name)
    try:
        res = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c", "copy", str(output)],
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            print(f"  ffmpeg 无损拼接完成: {output}")
            return True
        print(f"  [warn] ffmpeg -c copy 失败，尝试重编码: {res.stderr.strip()[:200]}")
        res = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c:v", "libx264", "-crf", "20",
             "-pix_fmt", "yuv420p", "-vf", "scale='trunc(iw/2)*2':'trunc(ih/2)*2'", str(output)],
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            print(f"  ffmpeg 重编码拼接完成: {output}")
            return True
        print(f"  [warn] ffmpeg 重编码也失败: {res.stderr.strip()[:200]}")
        return False
    finally:
        list_path.unlink(missing_ok=True)


def _pyav_concat(inputs: list[Path], output: Path) -> bool:
    try:
        import cv2
        script_dir = Path(__file__).resolve().parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        from stream_render import transcode_h264
    except Exception as e:
        print(f"  [warn] Khong the import cv2/transcode_h264: {e}")
        return False

    cap0 = cv2.VideoCapture(str(inputs[0]))
    fps = cap0.get(cv2.CAP_PROP_FPS) or 60.0
    w = int(cap0.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap0.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap0.release()

    raw_out = output.with_name(output.stem + "_raw.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(raw_out), fourcc, fps, (w, h))

    total_frames = 0
    for inp in inputs:
        cap = cv2.VideoCapture(str(inp))
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            if frame.shape[1] != w or frame.shape[0] != h:
                frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
            writer.write(frame)
            total_frames += 1
        cap.release()

    writer.release()
    try:
        transcode_h264(raw_out, output)
        print(f"  Ghep noi video hoan tat: {output}")
        return True
    except Exception as e:
        print(f"  [err] Loi transcode sau khi ghep: {e}")
        if raw_out.exists() and not output.exists():
            shutil.move(str(raw_out), str(output))
            return True
        return False


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="按顺序合并多幕白板动画 MP4")
    p.add_argument("--inputs", nargs="+", required=True, help="按播放顺序的 MP4 列表")
    p.add_argument("--output", required=True, help="合并输出路径")
    args = p.parse_args(argv)

    inputs = [Path(x) for x in args.inputs]
    missing = [str(x) for x in inputs if not x.exists()]
    if missing:
        print(f"[err] 缺少输入文件: {', '.join(missing)}", file=sys.stderr)
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if _ffmpeg_concat_copy(inputs, output) or _pyav_concat(inputs, output):
        print(f"OUTPUT={output.resolve()}")
        return 0
    print("[err] 合并失败：系统无 ffmpeg 且 PyAV 不可用", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
