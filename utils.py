import os
import cv2
import numpy as np
import subprocess

# 检查是否能用gpu加速
def test_encoder(encoder):
    """测试编码器是否真正可用"""
    test_cmd = [
        "ffmpeg", "-hide_banner",
        "-f", "lavfi", "-i", "testsrc=duration=1:size=1280x720:rate=30",
        "-c:v", encoder, "-f", "null", "-"
    ]

    try:
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False


def select_encoder():
    encoders = ['h264_nvenc', 'h264_qsv', 'h264_amf', 'h264_videotoolbox']

    for encoder in encoders:
        if test_encoder(encoder):
            print(f"已验证 {encoder} 可用")
            return encoder

    print("使用默认的 libx264 编码器")
    return "libx264"

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
