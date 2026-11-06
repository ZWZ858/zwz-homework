# -*- coding: utf-8 -*-
"""图片基础信息读取与简单编辑工具(基于 OpenCV)。"""

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


def make_output(in_path, suffix, new_ext=None):
    """根据原图路径生成新文件名,如 demo.jpg -> demo_resized.jpg。"""
    base, ext = os.path.splitext(in_path)
    ext = new_ext if new_ext else ext
    return "{}_{}{}".format(base, suffix, ext)


def unique_path(path):
    """若目标文件已存在,自动追加 _1、_2 后缀,避免覆盖已有文件。"""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists("{}_{}{}".format(base, i, ext)):
        i += 1
    return "{}_{}{}".format(base, i, ext)


def save_image(img, out_path):
    """保存图片并处理透明通道。返回 (实际保存路径, error)。"""
    ext = os.path.splitext(out_path)[1].lower()
    if not ext:
        return None, "输出路径缺少扩展名,无法判断保存格式"
    if ext in (".jpg", ".jpeg") and img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    out_path = unique_path(out_path)
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        return None, "保存失败:不支持的图片格式 ({})".format(ext)
    try:
        buf.tofile(out_path)
    except OSError as exc:
        return None, "写入文件失败: " + str(exc)
    return out_path, None


def do_resize(img, in_path, width, height, out_path):
    """缩放:可同时给宽高,也可只给其中一个(按比例缩放)。"""
    h, w = img.shape[:2]

    if width is None and height is None:
        return None, "参数错误:缩放需要至少指定 --width 或 --height 之一"
    if width is not None and width <= 0:
        return None, "参数错误:--width 必须大于 0"
    if height is not None and height <= 0:
        return None, "参数错误:--height 必须大于 0"

    if width is None:
        ratio = height / h
        new_w, new_h = max(1, round(w * ratio)), height
    elif height is None:
        ratio = width / w
        new_w, new_h = width, max(1, round(h * ratio))
    else:
        new_w, new_h = width, height

    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    if out_path is None:
        out_path = make_output(in_path, "resized")
    saved, err = save_image(resized, out_path)
    if err:
        return None, err
    return saved, "缩放完成: {}x{} -> {}x{}".format(w, h, new_w, new_h)


def do_crop(img, in_path, left, top, right, bottom, out_path):
    """裁剪:指定左、上、右、下坐标;区域越界时提示并裁剪到边界内。"""
    h, w = img.shape[:2]

    if not (left < right and top < bottom):
        return None, "参数错误:必须满足 left < right 且 top < bottom"
    if right <= 0 or bottom <= 0 or left >= w or top >= h:
        return None, "裁剪区域完全在图片外(图片尺寸 {}x{}),请检查坐标".format(w, h)

    warnings = []
    if left < 0 or top < 0 or right > w or bottom > h:
        warnings.append("提示:裁剪区域越界,已自动裁剪到图片边界内(图片 {}x{})".format(w, h))

    left, top = max(0, left), max(0, top)
    right, bottom = min(w, right), min(h, bottom)

    cropped = img[top:bottom, left:right]
    if out_path is None:
        out_path = make_output(in_path, "cropped")
    saved, err = save_image(cropped, out_path)
    if err:
        return None, err

    msg = "裁剪完成: 区域 ({},{}) -> ({},{})".format(left, top, right, bottom)
    if warnings:
        msg = "\n".join(warnings) + "\n" + msg
    return saved, msg


def do_rotate(img, in_path, angle, out_path):
    """旋转:支持 90 / 180 / 270 度。"""
    if angle == 90:
        rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        rotated = cv2.rotate(img, cv2.ROTATE_180)
    else:
        rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    if out_path is None:
        out_path = make_output(in_path, "rotated_{}".format(angle))
    saved, err = save_image(rotated, out_path)
    if err:
        return None, err
    return saved, "旋转完成: {} 度".format(angle)


def do_flip(img, in_path, direction, out_path):
    """翻转:horizontal 水平翻转,vertical 垂直翻转。"""
    code = 1 if direction == "horizontal" else 0
    flipped = cv2.flip(img, code)

    if out_path is None:
        out_path = make_output(in_path, "flipped_{}".format(direction))
    saved, err = save_image(flipped, out_path)
    if err:
        return None, err
    name = "水平" if direction == "horizontal" else "垂直"
    return saved, "翻转完成: {}翻转".format(name)


def to_grayscale(img):
    """把彩色图转灰度图(兼容 3 通道和 4 通道)。"""
    if img.ndim == 2:
        return img
    if img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def do_grayscale(img, in_path, out_path):
    """灰度化。"""
    gray = to_grayscale(img)
    if out_path is None:
        out_path = make_output(in_path, "gray")
    saved, err = save_image(gray, out_path)
    if err:
        return None, err
    return saved, "灰度化完成"


def do_convert(img, in_path, fmt, out_path):
    """格式转换。目标扩展名由 --format 决定。"""
    fmt = fmt.lower().lstrip(".")
    ext_map = {"jpg": ".jpg", "jpeg": ".jpg", "png": ".png", "bmp": ".bmp",
               "webp": ".webp", "tif": ".tiff", "tiff": ".tiff"}
    if fmt not in ext_map:
        return None, "不支持的格式: {} (支持 jpg/png/bmp/webp/tiff)".format(fmt)
    ext = ext_map[fmt]

    if out_path is None:
        out_path = make_output(in_path, "converted", new_ext=ext)
    saved, err = save_image(img, out_path)
    if err:
        return None, err
    return saved, "格式转换完成: -> {}".format(os.path.splitext(saved)[1].upper())


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
    parser = argparse.ArgumentParser(description="图片基础信息读取与简单编辑工具(基于 OpenCV)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_info = sub.add_parser("info", help="读取图片基础信息")
    p_info.add_argument("image", help="图片路径")

    p_resize = sub.add_parser("resize", help="缩放图片")
    p_resize.add_argument("image", help="图片路径")
    p_resize.add_argument("--width", type=int, help="目标宽度(像素)")
    p_resize.add_argument("--height", type=int, help="目标高度(像素)")
    p_resize.add_argument("--output", help="输出文件路径(可选)")

    p_crop = sub.add_parser("crop", help="裁剪图片")
    p_crop.add_argument("image", help="图片路径")
    p_crop.add_argument("--left", type=int, required=True, help="左边界 x 坐标")
    p_crop.add_argument("--top", type=int, required=True, help="上边界 y 坐标")
    p_crop.add_argument("--right", type=int, required=True, help="右边界 x 坐标")
    p_crop.add_argument("--bottom", type=int, required=True, help="下边界 y 坐标")
    p_crop.add_argument("--output", help="输出文件路径(可选)")

    p_rotate = sub.add_parser("rotate", help="旋转图片")
    p_rotate.add_argument("image", help="图片路径")
    p_rotate.add_argument("--angle", type=int, required=True, choices=[90, 180, 270],
                          help="旋转角度(90/180/270)")
    p_rotate.add_argument("--output", help="输出文件路径(可选)")

    p_flip = sub.add_parser("flip", help="翻转图片")
    p_flip.add_argument("image", help="图片路径")
    p_flip.add_argument("--direction", required=True, choices=["horizontal", "vertical"],
                        help="翻转方向:horizontal(水平)/vertical(垂直)")
    p_flip.add_argument("--output", help="输出文件路径(可选)")

    p_gray = sub.add_parser("grayscale", help="灰度化")
    p_gray.add_argument("image", help="图片路径")
    p_gray.add_argument("--output", help="输出文件路径(可选)")

    p_convert = sub.add_parser("convert", help="格式转换")
    p_convert.add_argument("image", help="图片路径")
    p_convert.add_argument("--format", required=True,
                           help="目标格式:png / jpg / bmp / webp / tiff")
    p_convert.add_argument("--output", help="输出文件路径(可选)")

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

    img, err = load_image(args.image)
    if err:
        print("[错误] " + err, file=sys.stderr)
        return 1

    out_path = getattr(args, "output", None)
    if args.command == "resize":
        out, msg = do_resize(img, args.image, args.width, args.height, out_path)
    elif args.command == "crop":
        out, msg = do_crop(img, args.image, args.left, args.top,
                           args.right, args.bottom, out_path)
    elif args.command == "rotate":
        out, msg = do_rotate(img, args.image, args.angle, out_path)
    elif args.command == "flip":
        out, msg = do_flip(img, args.image, args.direction, out_path)
    elif args.command == "grayscale":
        out, msg = do_grayscale(img, args.image, out_path)
    elif args.command == "convert":
        out, msg = do_convert(img, args.image, args.format, out_path)
    else:
        build_parser().print_help()
        return 1

    if out is None:
        print("[错误] " + msg, file=sys.stderr)
        return 1

    print(msg)
    print("已保存到: " + os.path.abspath(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
