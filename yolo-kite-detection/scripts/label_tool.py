"""
极简 YOLO 标注工具（tkinter 版，零额外依赖）

为什么用它：
    labelImg 在这台机器上画框时闪退（Qt 5.15.2 兼容问题），
    本脚本只用 Python 自带的 tkinter + Pillow，直接输出 YOLO 格式 txt，
    不需要再转换 PascalVOC。

功能：
    - 打开图片目录（文件名排序）
    - 鼠标左键拖拽画框
    - 右键点框：删除该框
    - 自动保存：每次画框/删框后立即写同名 .txt
    - 键盘：A/← 上一张  D/→ 下一张  Z 撤销最后一个框  Esc 退出

用法：
    python label_tool.py --img-dir E:\\dsh_yolo_hw\\dataset\\images\\all ^
                         --label-dir E:\\dsh_yolo_hw\\dataset\\labels\\all ^
                         --class-name kite

YOLO 标注格式（每行一个框）：
    <class_id> <cx> <cy> <w> <h>   均为 0~1 归一化
"""
import argparse
import glob
import os
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageDraw, ImageTk


class LabelTool:
    def __init__(self, img_dir, label_dir, class_name):
        self.img_dir = img_dir
        self.label_dir = label_dir
        self.class_id = 0
        self.class_name = class_name
        os.makedirs(label_dir, exist_ok=True)

        exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp")
        self.images = []
        for e in exts:
            self.images.extend(glob.glob(os.path.join(img_dir, e)))
        self.images.sort()
        if not self.images:
            raise SystemExit(f"{img_dir} 下没有图片")

        self.idx = 0
        self.boxes = []  # [(cx, cy, w, h)] 归一化
        self.start = None  # 当前拖拽起点（画布坐标）
        self.preview = None  # 当前拖拽矩形 id
        self.scale = 1.0
        self.offset = (0, 0)

        self.root = tk.Tk()
        self.root.title(f"YOLO 标注 - {class_name}")
        self.root.geometry("1000x860")

        # 顶部信息栏
        self.info = tk.Label(self.root, text="", font=("Microsoft YaHei", 12), anchor="w")
        self.info.pack(fill="x", padx=8, pady=4)

        self.hint = tk.Label(
            self.root,
            text="左键拖拽画框 | 右键点框删除 | A/← 上一张 | D/→ 下一张 | Z 撤销 | Esc 退出",
            font=("Microsoft YaHei", 10),
            fg="#555",
            anchor="w",
        )
        self.hint.pack(fill="x", padx=8)

        # 画布
        self.canvas = tk.Canvas(self.root, bg="#202020", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)
        self.root.bind("<Key-a>", lambda e: self.nav(-1))
        self.root.bind("<Key-A>", lambda e: self.nav(-1))
        self.root.bind("<Left>", lambda e: self.nav(-1))
        self.root.bind("<Key-d>", lambda e: self.nav(1))
        self.root.bind("<Key-D>", lambda e: self.nav(1))
        self.root.bind("<Right>", lambda e: self.nav(1))
        self.root.bind("<Key-z>", lambda e: self.undo())
        self.root.bind("<Key-Z>", lambda e: self.undo())
        self.root.bind("<Escape>", lambda e: self.quit())
        self.root.bind("<Configure>", self.on_resize)

        self.load_image()

    # ---------- 文件读写 ----------
    def txt_path(self, img_path):
        stem = os.path.splitext(os.path.basename(img_path))[0]
        return os.path.join(self.label_dir, stem + ".txt")

    def load_boxes(self, img_path):
        p = self.txt_path(img_path)
        boxes = []
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 5:
                        boxes.append(tuple(float(v) for v in parts[1:5]))
        return boxes

    def save_boxes(self):
        p = self.txt_path(self.images[self.idx])
        with open(p, "w", encoding="utf-8") as f:
            for cx, cy, w, h in self.boxes:
                f.write(f"{self.class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")

    # ---------- 显示 ----------
    def load_image(self):
        path = self.images[self.idx]
        self.pil = Image.open(path).convert("RGB")
        self.img_w, self.img_h = self.pil.size
        self.boxes = self.load_boxes(path)
        self.fit_and_draw()

    def fit_and_draw(self):
        cw = max(self.canvas.winfo_width(), 100)
        ch = max(self.canvas.winfo_height(), 100)
        self.scale = min(cw / self.img_w, ch / self.img_h)
        disp_w = int(self.img_w * self.scale)
        disp_h = int(self.img_h * self.scale)
        self.offset = ((cw - disp_w) // 2, (ch - disp_h) // 2)
        disp = self.pil.resize((disp_w, disp_h), Image.LANCZOS)
        self.tkimg = ImageTk.PhotoImage(disp)
        self.draw_all()
        name = os.path.basename(self.images[self.idx])
        self.info.config(
            text=f"[{self.idx + 1}/{len(self.images)}] {name}   "
                 f"原图 {self.img_w}x{self.img_h}   "
                 f"框数 {len(self.boxes)}   类别 {self.class_name}(id={self.class_id})"
        )

    def draw_all(self):
        self.canvas.delete("all")
        ox, oy = self.offset
        self.canvas.create_image(ox, oy, anchor="nw", image=self.tkimg)
        for cx, cy, w, h in self.boxes:
            x1 = ox + (cx - w / 2) * self.img_w * self.scale
            y1 = oy + (cy - h / 2) * self.img_h * self.scale
            x2 = ox + (cx + w / 2) * self.img_w * self.scale
            y2 = oy + (cy + h / 2) * self.img_h * self.scale
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="#00e600", width=2)
            self.canvas.create_text(
                x1 + 2, y1 + 2, anchor="nw", text=self.class_name,
                fill="#00e600", font=("Microsoft YaHei", 11, "bold"),
            )

    def on_resize(self, event):
        if event.widget is self.canvas:
            self.fit_and_draw()

    # ---------- 坐标换算 ----------
    def to_img(self, x, y):
        ox, oy = self.offset
        ix = (x - ox) / self.scale
        iy = (y - oy) / self.scale
        return max(0.0, min(ix, self.img_w)), max(0.0, min(iy, self.img_h))

    # ---------- 鼠标 ----------
    def on_press(self, ev):
        self.start = (ev.x, ev.y)
        self.preview = self.canvas.create_rectangle(
            ev.x, ev.y, ev.x, ev.y, outline="#ffcc00", width=2, dash=(4, 2)
        )

    def on_drag(self, ev):
        if self.start and self.preview:
            self.canvas.coords(self.preview, self.start[0], self.start[1], ev.x, ev.y)

    def on_release(self, ev):
        if not self.start:
            return
        x1, y1 = self.start
        x2, y2 = ev.x, ev.y
        if self.preview:
            self.canvas.delete(self.preview)
            self.preview = None
        self.start = None
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            self.draw_all()
            return
        ix1, iy1 = self.to_img(min(x1, x2), min(y1, y2))
        ix2, iy2 = self.to_img(max(x1, x2), max(y1, y2))
        w = (ix2 - ix1) / self.img_w
        h = (iy2 - iy1) / self.img_h
        if w < 0.003 or h < 0.003:
            self.draw_all()
            return
        cx = ((ix1 + ix2) / 2) / self.img_w
        cy = ((iy1 + iy2) / 2) / self.img_h
        self.boxes.append((cx, cy, w, h))
        self.save_boxes()
        self.draw_all()

    def on_right_click(self, ev):
        ox, oy = self.offset
        hit = None
        for i, (cx, cy, w, h) in enumerate(self.boxes):
            x1 = ox + (cx - w / 2) * self.img_w * self.scale
            y1 = oy + (cy - h / 2) * self.img_h * self.scale
            x2 = ox + (cx + w / 2) * self.img_w * self.scale
            y2 = oy + (cy + h / 2) * self.img_h * self.scale
            if x1 <= ev.x <= x2 and y1 <= ev.y <= y2:
                if hit is None or (x2 - x1) * (y2 - y1) < hit[1]:
                    hit = (i, (x2 - x1) * (y2 - y1))
        if hit:
            self.boxes.pop(hit[0])
            self.save_boxes()
            self.draw_all()

    # ---------- 导航 ----------
    def nav(self, step):
        new = self.idx + step
        if 0 <= new < len(self.images):
            self.idx = new
            self.load_image()

    def undo(self):
        if self.boxes:
            self.boxes.pop()
            self.save_boxes()
            self.draw_all()

    def quit(self):
        self.save_boxes()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img-dir", required=True)
    ap.add_argument("--label-dir", required=True)
    ap.add_argument("--class-name", default="kite")
    args = ap.parse_args()
    LabelTool(args.img_dir, args.label_dir, args.class_name).run()


if __name__ == "__main__":
    main()
