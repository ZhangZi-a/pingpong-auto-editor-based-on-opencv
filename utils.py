import os
import cv2
import numpy as np
import zipfile

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
