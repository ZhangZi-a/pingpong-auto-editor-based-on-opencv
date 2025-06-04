import gradio as gr
import cv2
import numpy as np
import os

from series_generator import start
from faster_cutter import process_video_segments


def update_sliders_and_info(file, video_state):
    # 这里更新视频路径，保存到video_state
    if hasattr(file, 'name'):
        video_path = file.name
    elif isinstance(file, str):
        video_path = file
    else:
        return (
            gr.update(maximum=1, value=0),
            "无效视频",
            gr.update(value=0), gr.update(value=0),
            gr.update(value=50), gr.update(value=50),
            None  # video_state
        )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return (
            gr.update(maximum=1, value=0),
            "无法打开视频",
            gr.update(value=0), gr.update(value=0),
            gr.update(value=50), gr.update(value=50),
            None
        )

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    return (
        gr.update(maximum=total - 1, value=0),
        f"帧数: {total} 分辨率: {w}x{h} 视频帧率{fps}    -----谨慎刷新，不保存窗口状态-----",
        gr.update(maximum=w - 1, value=w // 4),
        gr.update(maximum=h - 1, value=h // 4),
        gr.update(maximum=w - 1, value=w * 3 // 4),
        gr.update(maximum=h - 1, value=h * 3 // 4),
        video_path
    )


def load_frame_and_set_roi(frame_idx, video_state, frame_state):
    if video_state is None:
        return None, None, None, None, None, None

    cap = cv2.VideoCapture(video_state)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None, None, None, None, None, None

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = frame_rgb.shape[:2]
    x1, y1 = w // 4, 0
    x2, y2 = w * 3 // 4, h * 3 // 4

    frame_state = frame_rgb.copy()
    return draw_roi(frame_rgb, x1, y1, x2, y2), x1, y1, x2, y2, frame_state


def draw_roi(image, x1, y1, x2, y2):
    img = image.copy()
    h, w = img.shape[:2]
    x1 = int(np.clip(x1, 0, w - 1))
    x2 = int(np.clip(x2, 0, w - 1))
    y1 = int(np.clip(y1, 0, h - 1))
    y2 = int(np.clip(y2, 0, h - 1))
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return img


def update_image_with_roi(x1, y1, x2, y2, frame_state):
    if frame_state is None:
        return None
    return draw_roi(frame_state, x1, y1, x2, y2)


def process_video(x1, y1, x2, y2, video_state):
    if video_state is None:
        return None

    cap = cv2.VideoCapture(video_state)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ROI = ((x1 / w, y1 / h), (x2 / w, y2 / h))
    annotations = start(cap, False, ROI, gr.Progress())
    cap.release()

    temp_dir = "./tmp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    output_video_path = os.path.join(temp_dir, "processed_output.mp4")
    process_video_segments(video_state, annotations, output_video_path, gr.Progress())
    print(f'已保存到{temp_dir}')


    return output_video_path


with gr.Blocks() as demo:
    gr.Markdown("## 🎥 乒乓球比赛视频剪辑系统")

    video_state = gr.State(None)  # 存储上传视频路径
    frame_state = gr.State(None)  # 存储当前帧图像数据

    video_input = gr.Video(label="上传视频")
    frame_info = gr.Textbox(label="帧信息", interactive=False)

    with gr.Row():
        frame_slider = gr.Slider(minimum=0, maximum=100, step=1, label="选择帧")
        load_btn = gr.Button("加载帧")

    image_output = gr.Image(label="当前帧带 ROI")

    with gr.Row():
        x1_slider = gr.Slider(0, 100, step=1, label="x1")
        y1_slider = gr.Slider(0, 100, step=1, label="y1")
        x2_slider = gr.Slider(0, 100, step=1, label="x2")
        y2_slider = gr.Slider(0, 100, step=1, label="y2")

    process_btn = gr.Button("🚀 开始处理视频")
    result_video = gr.Video(label="输出视频")

    video_input.change(
        fn=update_sliders_and_info,
        inputs=[video_input, video_state],
        outputs=[frame_slider, frame_info, x1_slider, y1_slider, x2_slider, y2_slider, video_state]
    )

    load_btn.click(
        fn=load_frame_and_set_roi,
        inputs=[frame_slider, video_state, frame_state],
        outputs=[image_output, x1_slider, y1_slider, x2_slider, y2_slider, frame_state]
    )

    for slider in [x1_slider, y1_slider, x2_slider, y2_slider]:
        slider.change(
            fn=update_image_with_roi,
            inputs=[x1_slider, y1_slider, x2_slider, y2_slider, frame_state],
            outputs=image_output
        )

    process_btn.click(
        fn=process_video,
        inputs=[x1_slider, y1_slider, x2_slider, y2_slider, video_state],
        outputs=[result_video]
    )

demo.launch(server_name="0.0.0.0", server_port=7860, max_file_size=2 * 1024 * 1024 * 1024)
