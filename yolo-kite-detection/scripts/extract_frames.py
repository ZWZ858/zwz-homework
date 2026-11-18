"""
抽帧脚本：按固定帧间隔从视频中抽取图片，用于 YOLOv5 自定义数据集标注。

用法：
    python extract_frames.py --video 视频.mp4 --out E:\\dsh_yolo_hw\\dataset\\images\\all --every 6

参数：
    --video  输入视频路径
    --out    输出图片目录（不存在会自动创建）
    --every  每隔多少帧抽一张（默认 6，即 30fps 视频每 0.2 秒一张）
    --prefix 文件名前缀（默认 frame）
"""
import argparse
import os
import cv2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="输入视频路径")
    parser.add_argument("--out", required=True, help="输出图片目录")
    parser.add_argument("--every", type=int, default=6, help="抽帧间隔（帧）")
    parser.add_argument("--prefix", default="frame", help="文件名前缀")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"无法打开视频: {args.video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"视频: {args.video}")
    print(f"fps={fps:.2f} 总帧数={total} 时长={total / fps:.2f}s  抽帧间隔={args.every}")

    idx = 0
    saved = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % args.every == 0:
            # 文件名带帧号和毫秒时间戳，便于回溯
            name = f"{args.prefix}_{idx:04d}_t{idx / fps:.2f}s.jpg"
            path = os.path.join(args.out, name)
            cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved += 1
        idx += 1
    cap.release()
    print(f"完成：读取 {idx} 帧，保存 {saved} 张 -> {args.out}")


if __name__ == "__main__":
    main()
