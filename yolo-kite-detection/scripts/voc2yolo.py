"""
PascalVOC (.xml) -> YOLO (.txt) 标注格式转换脚本

labelImg 当前版本只能输出 PascalVOC 格式的 .xml，
YOLOv5 训练需要 YOLO 格式（归一化中心点 + 宽高）的 .txt。
本脚本把 labels 目录下的 .xml 批量转换为同名 .txt。

YOLO txt 每行格式：
    <class_id> <x_center> <y_center> <width> <height>
    坐标均为相对图片宽高的归一化值，范围 0~1

用法：
    python voc2yolo.py --xml-dir  E:\\dsh_yolo_hw\\dataset\\labels\\all \
                       --img-dir  E:\\dsh_yolo_hw\\dataset\\images\\all \
                       --class-name kite

    # 多个类别时用逗号分隔，按顺序对应类别 id 0,1,2...
    --class-name kite,bird
"""
import argparse
import glob
import os
import xml.etree.ElementTree as ET

import cv2


def convert_one(xml_path, img_dir, class2id, out_dir=None):
    """转换单个 xml，返回 (图片文件名, 框数量)。"""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 图片文件名和尺寸：优先用 xml 里的 size，缺失则读原图
    img_name = root.findtext("filename")
    size = root.find("size")
    if size is not None and size.findtext("width"):
        w = int(float(size.findtext("width")))
        h = int(float(size.findtext("height")))
    else:
        img_path = os.path.join(img_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            raise SystemExit(f"找不到图片且 xml 无尺寸信息: {img_path}")
        h, w = img.shape[:2]

    lines = []
    for obj in root.findall("object"):
        name = (obj.findtext("name") or "").strip()
        if name not in class2id:
            print(f"  [跳过] {os.path.basename(xml_path)} 未知类别 '{name}'")
            continue
        bnd = obj.find("bndbox")
        x1 = float(bnd.findtext("xmin"))
        y1 = float(bnd.findtext("ymin"))
        x2 = float(bnd.findtext("xmax"))
        y2 = float(bnd.findtext("ymax"))
        # 裁剪到图片范围内，避免标注越界导致 YOLO 报错
        x1 = max(0.0, min(x1, w))
        x2 = max(0.0, min(x2, w))
        y1 = max(0.0, min(y1, h))
        y2 = max(0.0, min(y2, h))
        bw = x2 - x1
        bh = y2 - y1
        if bw <= 1 or bh <= 1:
            continue
        cx = (x1 + x2) / 2 / w
        cy = (y1 + y2) / 2 / h
        lines.append(f"{class2id[name]} {cx:.6f} {cy:.6f} {bw / w:.6f} {bh / h:.6f}")

    out_dir = out_dir or os.path.dirname(xml_path)
    out_path = os.path.join(out_dir, os.path.splitext(os.path.basename(xml_path))[0] + ".txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")
    return img_name, len(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml-dir", required=True, help="PascalVOC xml 所在目录")
    parser.add_argument("--img-dir", required=True, help="对应图片目录（xml 缺尺寸时读这里）")
    parser.add_argument("--class-name", required=True, help="类别名，多个用逗号分隔，如 kite 或 kite,bird")
    parser.add_argument("--out-dir", default=None, help="输出目录，默认与 xml 同目录")
    args = parser.parse_args()

    names = [n.strip() for n in args.class_name.split(",") if n.strip()]
    class2id = {n: i for i, n in enumerate(names)}

    xmls = sorted(glob.glob(os.path.join(args.xml_dir, "*.xml")))
    if not xmls:
        raise SystemExit(f"{args.xml_dir} 下没有找到 .xml 文件")

    total_boxes = 0
    empty = []
    for x in xmls:
        img_name, n = convert_one(x, args.img_dir, class2id, args.out_dir)
        total_boxes += n
        if n == 0:
            empty.append(os.path.basename(x))

    print(f"转换完成：{len(xmls)} 个 xml -> txt")
    print(f"类别映射：{class2id}")
    print(f"共 {total_boxes} 个框")
    if empty:
        print(f"[注意] 以下 {len(empty)} 个 xml 没有任何有效框（可能是纯背景图，可保留空 txt）:")
        for e in empty:
            print("   ", e)


if __name__ == "__main__":
    main()
