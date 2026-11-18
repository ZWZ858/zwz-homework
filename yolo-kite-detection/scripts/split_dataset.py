"""
把 images/all + labels/all 按比例划分为 YOLOv5 标准的 train/val 目录结构。

用法：
    python split_dataset.py --root dataset --val-ratio 0.2 --seed 0
"""
import argparse
import glob
import os
import random
import shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="dataset", help="数据集根目录（内含 images/ labels/）")
    ap.add_argument("--val-ratio", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    root = args.root
    all_img = os.path.join(root, "images", "all")
    all_lbl = os.path.join(root, "labels", "all")

    imgs = sorted(glob.glob(os.path.join(all_img, "*.jpg")))
    if not imgs:
        raise SystemExit(f"{all_img} 下没有图片")

    random.Random(args.seed).shuffle(imgs)
    n_val = max(1, round(len(imgs) * args.val_ratio))
    val_imgs = set(imgs[:n_val])

    for sub in ("train", "val"):
        for kind in ("images", "labels"):
            os.makedirs(os.path.join(root, kind, sub), exist_ok=True)

    moved = {"train": 0, "val": 0}
    for img in imgs:
        stem = os.path.splitext(os.path.basename(img))[0]
        split = "val" if img in val_imgs else "train"
        lbl = os.path.join(all_lbl, stem + ".txt")
        if not os.path.exists(lbl):
            print(f"[跳过] 缺少标注: {stem}")
            continue
        shutil.copy2(img, os.path.join(root, "images", split, stem + ".jpg"))
        shutil.copy2(lbl, os.path.join(root, "labels", split, stem + ".txt"))
        moved[split] += 1

    print(f"总 {len(imgs)} 张 -> train {moved['train']} / val {moved['val']}")
    for split in ("train", "val"):
        n_i = len(glob.glob(os.path.join(root, "images", split, "*.jpg")))
        n_l = len(glob.glob(os.path.join(root, "labels", split, "*.txt")))
        print(f"  {split}: images={n_i} labels={n_l}")


if __name__ == "__main__":
    main()
