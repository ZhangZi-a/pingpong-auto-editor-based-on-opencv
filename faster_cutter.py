import cv2
import os
from tqdm import tqdm
from moviepy import VideoFileClip, concatenate_audioclips
import gradio as gr

def process_video_segments(input_cap, segments, output_path, progress=gr.Progress()):
    """
    用OpenCV裁剪多段视频帧（无声），
    用MoviePy裁剪对应音频，
    最后合并音视频输出。

    segments中时间单位为秒，比如 [(10,20), (30,40)]

    :param input_cap: 输入视频路径
    :param segments: 时间段列表，单位秒 [(start_sec, end_sec), ...]
    :param output_path: 输出视频路径
    """
    cap = cv2.VideoCapture(input_cap)
    if not cap.isOpened():
        print("无法打开视频文件")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 总切片数
    segments_count = len(segments)
    count = 1

    # 临时无声视频文件
    temp_video_path = "temp_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))

    for (start_frame, end_frame) in tqdm(segments, desc='正在合成视频切片：'):
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        for frame_idx in range(start_frame, end_frame):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        if progress is not None:
            progress(count / segments_count, desc=f"正在合成视频切片 {count}/{segments_count}")
        count += 1

    cap.release()
    out.release()

    # 使用moviepy处理音频合成
    video_clip = VideoFileClip(temp_video_path)
    original_video = VideoFileClip(input_cap)

    count = 0
    audio_clips = []
    for (start_frame, end_frame) in tqdm(segments, desc='正在合成音频切片：'):
        start_sec = start_frame / fps
        end_sec = end_frame / fps
        audio_clip = original_video.audio.subclipped(start_sec, end_sec)
        audio_clips.append(audio_clip)

        if progress is not None:
            progress(count / segments_count, desc=f"正在合成音频切片 {count}/{segments_count}")
        count += 1

    final_audio = concatenate_audioclips(audio_clips)

    if progress is not None:
        progress(1, desc='正在生成剪辑视频...')

    # 给无声视频加上拼接好的音频
    final_clip = video_clip.with_audio(final_audio)

    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    video_clip.close()
    original_video.close()
    # 删除临时无声视频
    os.remove(temp_video_path)

if __name__ == '__main__':
    input_path = 'video/short1.mp4'
    output_path = 'output/test_short1.mp4'

    segments = [[772, 976], [1609, 1873], [1993, 2197], [2331, 2655], [2704, 3028], [3072, 3396], [3525, 3729], [3925, 4249], [4364, 4748], [4869, 5073], [5103, 5307], [5520, 5724], [5999, 6203], [6229, 6553], [6632, 6896]]
    process_video_segments(input_path, segments, output_path)