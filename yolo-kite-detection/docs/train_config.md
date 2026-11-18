# 训练配置记录

本次作业训练所用参数与结果，供复现对照。

## 命令

```bat
cd E:\yolov5
python train.py ^
  --data    E:/dsh_yolo_hw/kite.yaml ^
  --weights yolov5s.pt ^
  --img 640 --batch 16 --epochs 150 ^
  --device 0 --workers 2 ^
  --project E:/dsh_yolo_hw/runs --name kite_yolov5s
```

## 环境

| 组件 | 版本 |
|---|---|
| Python | 3.11.18 |
| PyTorch | 2.10.0+cu128 |
| torchvision | 0.25.0+cu128 |
| YOLOv5 | v7.0 |
| GPU | NVIDIA GeForce RTX 5070 Ti Laptop (12 GB) |
| 驱动 / CUDA | 572.90 / 12.8 |

## 超参数

| 参数 | 值 |
|---|---|
| 预训练权重 | `yolov5s.pt` (COCO) |
| imgsz | 640 |
| batch | 16 |
| epochs | 150 |
| optimizer | SGD |
| lr0 / lrf | 0.01 / 0.01 |
| momentum | 0.937 |
| weight_decay | 0.0005 |
| warmup_epochs | 3.0 |
| box / cls / obj 损失权重 | 0.05 / 0.5 / 1.0 |
| hsv_h / hsv_s / hsv_v | 0.015 / 0.7 / 0.4 |
| translate / scale | 0.1 / 0.5 |
| fliplr | 0.5 |
| mosaic | 1.0 |
| mixup / copy_paste | 0.0 / 0.0 |
| patience | 100 |
| seed | 0 |

## 数据

| 划分 | 图片数 | 目标数 |
|---|---|---|
| train | 22 | 22 |
| val | 6 | 6 |

验证集图片：`frame_0000_t0.00s`、`frame_0018_t0.60s`、`frame_0030_t1.00s`、`frame_0060_t2.00s`、`frame_0084_t2.80s`、`frame_0102_t3.40s`（随机种子 0，8:2 划分）

## 结果

| 指标 | 验证集 |
|---|---|
| Precision | 0.991 |
| Recall | 1.000 |
| mAP@0.5 | 0.995 |
| mAP@0.5:0.95 | 0.711（最终验证） |
| 训练耗时 | 约 1.5 分钟 |

best mAP@0.5 在第 **27** 轮达到 0.995，此后稳定保持。

## 推理速度（RTX 5070 Ti, imgsz=640）

```
0.4 ms 预处理 + 5.0 ms 推理 + 1.3 ms NMS  ≈ 6.7 ms/帧
```

## 备注

训练结束保存权重后，YOLOv5 后台线程绘制 batch 预览图时抛出：

```
AttributeError: 'numpy.ndarray' object has no attribute 'save'
（utils/plots.py:116  annotator.im.save(fname)）
```

发生在权重已保存之后，不影响 `best.pt` / `last.pt` 与评估曲线。
