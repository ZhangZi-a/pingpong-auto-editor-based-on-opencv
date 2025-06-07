import gradio as gr
import cv2
import os

from series_generator import start
from faster_cutter import process_video_segments
from utils import clean_tmp, draw_roi

def handle_video_list(files):
    if not files:
        return [], None, {}
    path_lst = [f.name for f in files]
    roi_dict = {}
    for path in path_lst:
        cap = cv2.VideoCapture(path)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        roi_dict[path] = [w // 4, 0, w * 3 // 4, h * 3 // 4]
    return path_lst, gr.update(choices=path_lst, value=path_lst[0] if path_lst else None), roi_dict

def select_video(selected_video, frame_dict, roi_dict):
    if selected_video is None:
        return None, None, None, None, None, None, None
    cap = cv2.VideoCapture(selected_video)

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_rgb = frame_dict.get(selected_video, None)
    x1, y1, x2, y2 = roi_dict[selected_video]

    return (draw_roi(frame_rgb, x1, y1, x2, y2),
            f"帧数: {total} 分辨率: {w}x{h} 视频帧率{fps}    -----谨慎刷新，不保存窗口状态-----",
            gr.update(maximum=w - 1, value=x1),
            gr.update(maximum=h - 1, value=y1),
            gr.update(maximum=w - 1, value=x2),
            gr.update(maximum=h - 1, value=y2),
            gr.update(maximum=total - 1, value=0))


def load_frame_and_set_roi(frame_idx, selected_video, roi_dict, frame_dict):
    cap = cv2.VideoCapture(selected_video)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None, None, None, None, None

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_dict[selected_video] = frame_rgb
    x1, y1, x2, y2 = roi_dict[selected_video]

    return draw_roi(frame_rgb, x1, y1, x2, y2), x1, y1, x2, y2


def update_image_with_roi(video_path, frame_dict, roi_dict, x1, y1, x2, y2):
    frame_state = frame_dict.get(video_path, None)
    roi_dict[video_path] = (x1, y1, x2, y2)
    if frame_state is None:
        return None
    return draw_roi(frame_state, x1, y1, x2, y2)


def batch_process_video(video_lst, roi_dict):
    output_video_paths = []

    # 暂存文件夹
    temp_dir = "./tmp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    clean_tmp(temp_dir)

    for i, path in enumerate(video_lst):
        if path is None:
            print(f"error in video path:{path}")
            return None

        print(f"-----------------------------------------正在处理第{i + 1}个视频-----------------------------------------")

        cap = cv2.VideoCapture(path)
        x1, y1, x2, y2 = roi_dict[path]
        roi = ((x1, y1), (x2, y2))
        annotations = start(cap, False, roi, i + 1, gr.Progress())
        cap.release()

        annotations = sorted(annotations, key=lambda arg: arg[1] - arg[0], reverse=True)

        if len(annotations) == 0:
            print(f"第{i + 1}个视频无对局：{temp_dir}")
            continue

        output_video_path = os.path.join(temp_dir, f"processed_output_{i + 1}.mp4")
        process_video_segments(path, annotations, output_video_path, i + 1, gr.Progress())
        output_video_paths.append(output_video_path)
        print(f'第{i + 1}个视频已暂存到{temp_dir}')

    return output_video_paths


with gr.Blocks() as demo:
    gr.Markdown("## 🎥 乒乓球比赛视频剪辑系统")

    video_list_state = gr.State([])  # 存储每个视频的列表
    frame_dict_state = gr.State({})  # 存储当前每个视频的帧图像数据
    roi_dict_state = gr.State({})  # 每个视频的ROI设置

    video_input = gr.File(label='输入视频', file_types=[".mp4", ".avi", '.MP4', '.mov', '.MOV'], file_count="multiple", type="filepath")
    video_selector = gr.Dropdown(label='选择视频', choices=[])
    video_info = gr.Textbox(label="视频信息", interactive=False)

    with gr.Row():
        frame_slider = gr.Slider(minimum=0, maximum=100, step=1, label="选择帧")
        load_btn = gr.Button("加载帧")

    image_output = gr.Image(label="带 ROI 的当前帧")

    with gr.Row():
        x1_slider = gr.Slider(0, 100, step=1, label="x1")
        y1_slider = gr.Slider(0, 100, step=1, label="y1")
        x2_slider = gr.Slider(0, 100, step=1, label="x2")
        y2_slider = gr.Slider(0, 100, step=1, label="y2")

    process_btn = gr.Button("🚀 开始处理视频")
    result_video = gr.File(label='输出视频')

    video_input.change(
        fn=handle_video_list,
        inputs=video_input,
        outputs=[video_list_state, video_selector, roi_dict_state],
    )

    video_selector.change(
        fn=select_video,
        inputs=[video_selector, frame_dict_state, roi_dict_state],  # 会把当前选项的参数传入
        outputs=[image_output, video_info, x1_slider, y1_slider, x2_slider, y2_slider, frame_slider],
    )

    load_btn.click(
        fn=load_frame_and_set_roi,
        inputs=[frame_slider, video_selector, roi_dict_state, frame_dict_state],
        outputs=[image_output, x1_slider, y1_slider, x2_slider, y2_slider]
    )

    for slider in [x1_slider, y1_slider, x2_slider, y2_slider]:
        slider.change(
            fn=update_image_with_roi,
            inputs=[video_selector, frame_dict_state, roi_dict_state, x1_slider, y1_slider, x2_slider, y2_slider],
            outputs=image_output
        )

    process_btn.click(
        fn=batch_process_video,
        inputs=[video_list_state, roi_dict_state],
        outputs=[result_video]
    )

demo.launch(
    server_port=7860,
    max_file_size=10 * 1024 * 1024 * 1024,
    )
