# 🏓 乒乓球比赛视频自动剪辑系统

这是一个web端的基于OpenCV的乒乓球检测与自动视频剪辑工具，可自动识别比赛中的乒乓球位置并生成精彩片段集锦。

## ✨ 功能特性
- **乒乓球实时检测**：使用OpenCV动态识别乒乓球位置
- **智能视频剪辑**：自动生成精彩片段，去除捡球的尴尬回放
- **输出自定义**：可配置输出画质、分辨率、格式等参数

## 📦 安装指南

### 系统依赖
- Python 3.10
- gradio 
- OpenCV 4.5+ (`pip install opencv-python`)

### 快速安装
```bash
git clone https://github.com/yourusername/pingpong-auto-editor-based-on-opencv.git
cd pingpong-auto-editor-based-on-opencv
pip install -r requirements.txt
```

## 📖使用教程

### 运行服务
1. 运行项目目录下的`app.py`文件
2. 进入"http://localhost:7860"

### 使用界面
1. 上传数个乒乓球比赛视频(需要为固定机位)
2. 在下拉框中选择视频，选定视频后，拉动选择帧，点击加载帧，滑动滑块框选出ROI区域，为每个上传的视频设置ROI框
3. ROI区域需要包含整个球桌以及球桌上方区域，ROI的正确设置非常重要，决定了在哪个区域内检测乒乓球，正确示例：
![](assets/sample.jpg)
4. 确定每个视频都调整好ROI之后，点击`🚀 开始处理视频`，耐心等待片刻就能得到新鲜出炉的剪辑版视频，记得下载下来哦

### 注意点
- 由于后台没有保存窗口状态，故刷新会导致页面丢失，尽量避免页面刷新
- 滑动ROI区域时后台会自动记录坐标，框选好后直接调整下一个视频即可
- 即使重新加载帧，也不会影响ROI的区域，这可以用来判断视频前后球桌位置是否有变动
- 不要忘记为每个视频分别设置ROI!

## 🛠️项目结构
```angular2html
.
├── app.py                # 主程序入口
├── faster_cutter.py      # 视频导出模块 
├── series_generator.py   # 切片序列生成模块
├── utils.py              # 工具函数模块
├── tmp/                  # 临时视频文件目录(自动生成)
│   └── ...               # 临时视频文件
├── requirements.txt      # 项目需求文档
└── README.md             # 项目介绍文件
```