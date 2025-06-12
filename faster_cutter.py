import cv2
import os
from tqdm import tqdm
import subprocess

from utils import select_encoder

def ffmpeg_merge_segments(input_path, segments, tmp_dir, output_path, progress=None, img_idx=0):
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # 准备切片暂存目录
    tmp_part_dir = os.path.join(tmp_dir, 'part')
    if not os.path.exists(tmp_part_dir):
        os.makedirs(tmp_part_dir)
    # 准备切片记录文件
    concat_file = os.path.join(tmp_part_dir, "concat_list.txt")
    temp_files = []

    i = 0
    for (start, end) in tqdm(segments, desc=f'FFmpeg帧拼接中：'):
        out_name = f"temp_{img_idx}_{i}.mp4"
        out_path = os.path.join(tmp_part_dir, out_name)
        temp_files.append(out_name)  # 5.0版本的ffmpeg会基于concat文件自己拼接，这里不给路径
        duration = end - start
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start / fps),  # 转为秒
            "-t", str(duration / fps),
            "-i", input_path,
            "-c", "copy",  # 无重编码
            "-avoid_negative_ts", "make_zero",  # 强制从时间戳从0开始，避免变速异常
            out_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if progress is not None:
            progress((i + 1) / len(segments), desc=f"第{img_idx}个视频处理中... FFmpeg帧拼接中 {i + 1}/{len(segments)}")

        i += 1

    # 生成合并文件列表
    with open(concat_file, "w") as f:
        for fpath in temp_files:
            f.write(f"file '{fpath}'\n")

    # 合并
    print('FFmpeg切片合并中...')
    if progress is not None:
        progress(1, desc=f"第{img_idx}个视频处理中... FFmpeg切片合并中...")

    # 选择编码器加速
    fourcc = select_encoder()
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c:v", fourcc,  # 使用编码器
        "-crf", "18",  # 质量控制参数，越小画质越高（18~28，推荐18-23）
        "-b:v", "6M",  # 码率控制
        "-preset", "fast",  # 编码速度和压缩效率
        "-c:a", "aac",  # 音频转为 AAC
        output_path
    ])
    print(f"结果已存于：{output_path}")

    # 清理
    for fpath in temp_files:
        os.remove(os.path.join(tmp_part_dir, fpath))
    os.remove(concat_file)

if __name__ == '__main__':
    input_path = 'video/sample3.mp4'
    output_path = 'output/output_sample3.mp4'

    segments = [[672, 860], [960, 1266], [1800, 3216], [3338, 3526], [3899, 4264], [4316, 4622], [4765, 5349], [5569, 6346], [6558, 6923], [7076, 7264], [7442, 7630], [7926, 8409], [8464, 8947], [9344, 9591], [9772, 10019]]
    ffmpeg_merge_segments(input_path, segments, './tmp', output_path)