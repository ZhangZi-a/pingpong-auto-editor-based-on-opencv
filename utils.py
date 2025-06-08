import os
import cv2
import numpy as np
import subprocess

# 检查是否能用gpu加速
def select_encoder():
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True
        )
        if "h264_nvenc" in result.stdout:
            print("正在为您使用NVIDIA 编码器加速")
            return "h264_nvenc"
        elif "h264_qsv" in result.stdout:
            print("正在为您使用QSV 编码器加速")
            return "h264_qsv"
        elif "h264_amf" in result.stdout:
            print("正在为您使用AMF 编码器加速")
            return "h264_amf"
        else:
            print("无可用图像编码器加速,使用默认的libx264")
            return "libx264"
    except Exception as e:
        print("检测失败：", e)
        return False

def clean_tmp(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)  # 删除文件
        except Exception as e:
            print(f"删除失败 {file_path}: {e}")

            def draw_roi(image, x1, y1, x2, y2):
                if image is None:
                    return None
                img = image.copy()
                h, w = img.shape[:2]
                x1 = int(np.clip(x1, 0, w - 1))
                x2 = int(np.clip(x2, 0, w - 1))
                y1 = int(np.clip(y1, 0, h - 1))
                y2 = int(np.clip(y2, 0, h - 1))
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                return img

def draw_roi(image, x1, y1, x2, y2):
    if image is None:
        return None
    img = image.copy()
    h, w = img.shape[:2]
    x1 = int(np.clip(x1, 0, w - 1))
    x2 = int(np.clip(x2, 0, w - 1))
    y1 = int(np.clip(y1, 0, h - 1))
    y2 = int(np.clip(y2, 0, h - 1))
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return img
