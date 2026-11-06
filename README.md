# 图片信息读取与编辑工具

## 项目介绍

这是一个基于 **Python + OpenCV** 的**命令行**工具,能读取图片的基础信息,并完成几种常见的图片编辑。所有编辑结果都会保存为新文件,不覆盖原图,并在完成后打印保存位置。

### 支持的功能

- **读取图片信息**:文件名、图片格式、宽度和高度、颜色模式、文件大小
- **缩放**:指定宽高;只给宽或高时按比例缩放
- **裁剪**:指定左、上、右、下坐标;区域越界时给出提示
- **旋转**:支持 90 / 180 / 270 度
- **翻转**:水平翻转、垂直翻转
- **灰度化**:彩色图转灰度图
- **格式转换**:PNG / JPG / BMP / WEBP / TIFF 互转

## 环境配置

### Python 版本

Python 3.8 及以上(推荐 3.10+)。

### 安装依赖

Ubuntu / Debian:

    sudo apt install -y python3 python3-opencv python3-numpy

其它系统或使用 pip:

    pip install opencv-python numpy

(可选)使用 uv 管理环境:

    uv venv
    uv pip install opencv-python numpy

## 运行方式

### 启动

    python3 image_tool.py <子命令> <图片路径> [选项]

查看帮助:`python3 image_tool.py -h`

### 1. 读取图片信息

    python3 image_tool.py info demo.jpg

预期输出:

    ==========================================
    图片信息
    ==========================================
    文件名     : demo.jpg
    图片格式   : JPEG
    宽度和高度 : 640 x 480 像素 (宽 x 高)
    颜色模式   : RGB (OpenCV 内部为 BGR)
    文件大小   : 8.99 KB
    ==========================================

### 2. 缩放

    python3 image_tool.py resize demo.jpg --width 800
    python3 image_tool.py resize demo.jpg --height 600
    python3 image_tool.py resize demo.jpg --width 800 --height 600

只给宽时高度按比例缩放,只给高时宽度按比例缩放。预期输出:`缩放完成: 640x480 -> 800x600` 和 `已保存到: ...`

### 3. 裁剪

    python3 image_tool.py crop demo.jpg --left 100 --top 100 --right 500 --bottom 400

预期输出:`裁剪完成: 区域 (100,100) -> (500,400)` 和 `已保存到: ...`

### 4. 旋转

    python3 image_tool.py rotate demo.jpg --angle 90

`--angle` 可选 90 / 180 / 270。

### 5. 翻转

    python3 image_tool.py flip demo.jpg --direction horizontal
    python3 image_tool.py flip demo.jpg --direction vertical

### 6. 灰度化

    python3 image_tool.py grayscale demo.jpg

### 7. 格式转换

    python3 image_tool.py convert demo.png --format jpg
    python3 image_tool.py convert demo.jpg --format png

带透明通道的 PNG 转 JPG 时会自动转为 RGB。

### 错误处理

- 文件不存在、文件不是有效图片、参数非法(如宽高 <= 0)时给出明确提示,不会崩溃。
- 编辑结果保存为新文件(已存在则自动追加 `_1`、`_2` 后缀),不覆盖原图。
