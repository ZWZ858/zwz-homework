# -*- coding: utf-8 -*-
"""图片基础信息读取工具(基于 OpenCV)。"""

import argparse
import os
import sys

import cv2
import numpy as np


def load_image(path):
    """读取图片,兼容中文/非 ASCII 路径。返回 (img, error)。"""
    if not os.path.exists(path):
        return None, "文件不存在: " + path
    try:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size == 0:
            return None, "文件为空,无法读取: " + path
        img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
        if img is None:
            return None, "不是有效的图片文件: " + path
        return img, None
    except Exception as exc:
        return None, "读取图片时出错: " + str(exc)


def detect_format(path):
    """根据文件头(魔数)判断真实格式,失败时退回扩展名。"""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError:
        return os.path.splitext(path)[1].lstrip(".").upper() or "unknown"

    if head.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "GIF"
    if head.startswith(b"BM"):
        return "BMP"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "WEBP"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return "TIFF"
    return os.path.splitext(path)[1].lstrip(".").upper() or "unknown"


def human_size(num_bytes):
    """把字节数转换成 KB / MB,保留 2 位小数。"""
    if num_bytes >= 1024 * 1024:
        return "{:.2f} MB".format(num_bytes / (1024 * 1024))
    return "{:.2f} KB".format(num_bytes / 1024)


def color_mode(img):
    """根据通道数返回颜色模式描述。"""
    if img.ndim == 2 or img.shape[2] == 1:
        return "灰度 (Grayscale)"
    if img.shape[2] == 3:
        return "RGB (OpenCV 内部为 BGR)"
    if img.shape[2] == 4:
        return "RGBA (OpenCV 内部为 BGRA,含透明通道)"
    return "{} 通道".format(img.shape[2])


def print_info(path):
    """打印图片基础信息。"""
    img, err = load_image(path)
    if err:
        print("[错误] " + err, file=sys.stderr)
        return 1

    size_bytes = os.path.getsize(path)
    h, w = img.shape[:2]

    print("=" * 42)
    print("图片信息")
    print("=" * 42)
    print("文件名     : " + os.path.basename(path))
    print("图片格式   : " + detect_format(path))
    print("宽度和高度 : {} x {} 像素 (宽 x 高)".format(w, h))
    print("颜色模式   : " + color_mode(img))
    print("文件大小   : " + human_size(size_bytes))
    print("=" * 42)
    return 0


def build_parser():
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="图片基础信息读取工具(基于 OpenCV)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_info = sub.add_parser("info", help="读取图片基础信息")
    p_info.add_argument("image", help="图片路径")

    return parser


def main(argv=None):
    # 强制 UTF-8 输出,避免中文提示乱码
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    args = build_parser().parse_args(argv)
    if args.command == "info":
        return print_info(args.image)
    return 1


if __name__ == "__main__":
    sys.exit(main())
