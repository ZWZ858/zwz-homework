# YOLOv5 风筝目标检测

自选视频 → 抽帧 → 标注 → 训练 YOLOv5s → 推理，检测画面中的 **风筝（kite）**（1 个类别）。

## 文件说明

| 文件 | 内容 |
|---|---|
| `result.mp4` | 使用自训练模型 `best.pt` 推理得到的检测视频（18.5 秒） |
| `frame_01.png` / `frame_02.png` / `frame_03.png` | 从 `result.mp4` 截取的 3 帧 |
| `best.pt` | 训练产出的权重（YOLOv5s 微调） |
| `kite.yaml` | 数据集配置 |
| `scripts/` | 抽帧、标注、划分、校验脚本 |

## 1. 视频来源

- 手机竖屏拍摄，**1080×1920，30 fps，5.6 秒，168 帧**，画面为一只红色凤凰造型风筝在空中飞行（带长尾）。
- 推理视频 `result.mp4` 为**原视频的慢放版本**：全部 168 帧逐帧完成 3.3 倍时间拉伸（9.09 fps），时长 18.5 秒，以满足 10–30 秒要求；帧内容与检测框完全不变。

## 2. 类别与标注数量

| class_id | 类别 | 标注框数 |
|---|---|---|
| 0 | `kite` | 28 |

- 抽帧：每 6 帧抽 1 张，共 **28 张**（脚本 `scripts/extract_frames.py`）。
- 标注格式：YOLO TXT，`class_id cx cy w h`，归一化到 0~1。
- 标注规范：**框住风筝身体与翅膀，不框长尾飘带**（尾巴随风摆动形状多变且占大量背景，计入会拉低 IoU）。
- 标注工具：labelImg 在本机（Qt 5.15.2）画框即崩溃，改用 `scripts/label_tool.py`（tkinter，直接输出 YOLO TXT）。
- 校验：`scripts/check_labels.py` 结果 —— 28 图 / 28 标注，无缺失、无孤儿、无越界框。框宽 0.138~0.274，框高 0.069~0.130，中心点 cx 0.319~0.566、cy 0.177~0.330。

## 3. train / val 划分

- 训练集 **22 张**，验证集 **6 张**，比例 **8 : 2**，随机种子 0（`scripts/split_dataset.py`）。
- 验证集 6 张：`frame_0000_t0.00s` / `0018_t0.60s` / `0030_t1.00s` / `0060_t2.00s` / `0084_t2.80s` / `0102_t3.40s`（每张含 1 个 kite）。
- 同一视频不同帧，验证集与训练集**无重复图片**。

## 4. 环境与复现

Python 3.11 / PyTorch 2.10.0+cu128 / torchvision 0.25.0+cu128 / YOLOv5 v7.0 / RTX 5070 Ti 12 GB。

```bat
:: 1) 数据集（本地准备，不需要提交）
python scripts\extract_frames.py --video 原视频.mp4 --out dataset\images\all --every 6
python scripts\label_tool.py --img-dir dataset\images\all --label-dir dataset\labels\all --class-name kite
python scripts\split_dataset.py --root dataset --val-ratio 0.2 --seed 0

:: 2) 训练
cd E:\yolov5
python train.py --data kite.yaml --weights yolov5s.pt --img 640 --batch 16 --epochs 150 ^
                --device 0 --workers 2 --project runs --name kite_yolov5s

:: 3) 推理
python detect.py --weights best.pt --source 原视频.mp4 --conf 0.25 --device 0
```

`dataset/` 目录结构：`images/{all,train,val}` + `labels/{all,train,val}`，图片与同名 `.txt` 一一对应。YAML 中路径用正斜杠 `/`。

## 5. 验证集指标

| 指标 | 值 |
|---|---|
| Precision | **0.991** |
| Recall | **1.000** |
| mAP@0.5 | **0.995** |
| mAP@0.5:0.95 | 0.711 |
| 训练耗时 | 约 1.5 分钟（150 epochs） |
| 推理速度 | 约 6.7 ms/帧（640 输入） |

`result.mp4` 共 168 帧，**每帧均检出 1 个 kite**，置信度 0.75~0.92，与验证集指标一致。

> 说明：验证集 6 张与训练集来自同一段视频，指标偏高，反映模型对本场景的拟合程度，不代表跨场景泛化能力。

## 6. 遇到的问题

1. **labelImg 崩溃**：本机 Qt 5.15.2 下光标变十字后点击无响应、数秒闪退，且该版本仅支持 PascalVOC 输出。改用自写的 `scripts/label_tool.py`（tkinter，直接输出 YOLO TXT），并保留 `scripts/voc2yolo.py` 作为 PascalVOC 转换备选。
2. **训练末尾绘图报错**：`utils/plots.py:116` 报 `AttributeError: 'numpy.ndarray' object has no attribute 'save'`（numpy 2.x + Pillow 13 兼容问题），发生在权重保存之后，**不影响 `best.pt` 与评估曲线**，仅导致缺少 batch 预览图。
3. **视频时长不足**：原视频仅 5.6 秒，低于 10 秒要求，故对检测结果做匀速慢放（保留全部帧）延长至 18.5 秒。
4. **预训练模型混淆**：COCO 预训练 yolov5s 将风筝判为 `kite` / `bird` / `airplane` 且置信度波动大（0.29~0.86），说明同类形状易混淆，这也是训练自定义单类模型的直接动机。
