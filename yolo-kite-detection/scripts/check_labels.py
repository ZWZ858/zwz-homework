"""
校验 YOLO 标注：图片与标注配对、坐标合法性、框尺寸分布。

用法：
    python check_labels.py --img-dir dataset\\images\\all --label-dir dataset\\labels\\all
"""
import argparse
import glob
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img-dir", default=r"dataset\images\all")
    ap.add_argument("--label-dir", default=r"dataset\labels\all")
    args = ap.parse_args()

    imgs = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(args.img_dir, "*.jpg"))}
    lbls = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(args.label_dir, "*.txt"))}

    print(f"images={len(imgs)} labels={len(lbls)}")
    print("missing label:", sorted(imgs - lbls) or "none")
    print("orphan label :", sorted(lbls - imgs) or "none")

    bad, empty, sizes = [], [], []
    for p in sorted(glob.glob(os.path.join(args.label_dir, "*.txt"))):
        name = os.path.basename(p)
        with open(p, encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        if not lines:
            empty.append(name)
            continue
        for i, ln in enumerate(lines):
            parts = ln.split()
            if len(parts) != 5:
                bad.append((name, i, "字段数", ln))
                continue
            cls, cx, cy, w, h = int(parts[0]), *map(float, parts[1:])
            if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < w <= 1 and 0 < h <= 1):
                bad.append((name, i, "越界", ln))
            if w * h < 0.002:
                bad.append((name, i, "过小", ln))
            sizes.append((w, h, cx, cy))

    print(f"empty txt: {empty or 'none'}")
    print(f"bad boxes: {bad or 'none'}")
    if sizes:
        ws = [s[0] for s in sizes]
        hs = [s[1] for s in sizes]
        cxs = [s[2] for s in sizes]
        cys = [s[3] for s in sizes]
        print(f"boxes={len(sizes)}")
        print(f"w  min={min(ws):.3f} max={max(ws):.3f} mean={sum(ws) / len(ws):.3f}")
        print(f"h  min={min(hs):.3f} max={max(hs):.3f} mean={sum(hs) / len(hs):.3f}")
        print(f"cx min={min(cxs):.3f} max={max(cxs):.3f}")
        print(f"cy min={min(cys):.3f} max={max(cys):.3f}")


if __name__ == "__main__":
    main()
