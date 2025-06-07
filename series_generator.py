from tqdm import tqdm
import cv2
import numpy as np
import gradio as gr

from faster_cutter import process_video_segments

def get_white_mask(f1, f2, f3):
    masks = []
    for frame in (f1, f2, f3):
        masks.append(cv2.inRange(frame, (180, 180, 180), (255, 255, 255)))
    and_mask1 = cv2.bitwise_or(masks[0], masks[1])
    and_mask2 = cv2.bitwise_or(and_mask1, masks[2])

    kernel = np.ones((3, 3), np.uint8)  # 你可以改为(5, 5)

    # 进行膨胀运算
    and_mask2 = cv2.dilate(and_mask2, kernel, iterations=1)

    return and_mask2

def draw_ROI(ROI_start, ROI_end, image):
    color = (0, 255, 0)
    thickness = 2
    cv2.rectangle(image, ROI_start, ROI_end, color, thickness)

def detect_ball(frame1, frame2, frame3, render, ROI_start, ROI_end, cur_frame):
    is_detect = False

    color_mask = get_white_mask(frame1, frame2, frame3)  # 颜色差分
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    gray3 = cv2.cvtColor(frame3, cv2.COLOR_BGR2GRAY)

    # 高斯模糊去噪
    gauss_kernel = (7, 7)
    gray1 = cv2.GaussianBlur(gray1, gauss_kernel, 0)
    gray2 = cv2.GaussianBlur(gray2, gauss_kernel, 0)
    gray3 = cv2.GaussianBlur(gray3, gauss_kernel, 0)

    # 计算两两差分
    diff1 = cv2.absdiff(gray1, gray2)
    diff2 = cv2.absdiff(gray2, gray3)
    combined_diff = cv2.bitwise_and(diff1, diff2)  # 合并差分

    _, diff_mask = cv2.threshold(combined_diff, 30, 255, cv2.THRESH_BINARY)
    # 形态学去噪（闭运算），去除空洞
    kernel = np.ones((5, 5), np.uint8)
    diff_mask = cv2.morphologyEx(diff_mask, cv2.MORPH_CLOSE, kernel)

    final_diff = cv2.bitwise_and(diff_mask, color_mask)

    kernel = np.ones((3, 3), np.uint8)
    final_diff = cv2.morphologyEx(final_diff, cv2.MORPH_OPEN, kernel)
    # 查找轮廓
    contours, _ = cv2.findContours(final_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        target_cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(target_cnt)
        if 45 < area < 80:
            # 计算最小外接圆
            (x, y), radius = cv2.minEnclosingCircle(target_cnt)
            center = (int(x), int(y))
            radius = int(radius)

            # 圆形度筛选（轮廓面积与外接圆面积比）
            circularity = area / (np.pi * radius ** 2 + 1e-5)  # 避免除零
            if 0.45 < circularity < 2:
                # print(area, circularity)
                is_detect = True
                if render:
                    cv2.circle(frame3, center, radius, (0, 255, 0), 2)  # 画圆
                    cv2.putText(frame3, "Ball", (center[0] - 20, center[1] - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    if render:
        draw_ROI(ROI_start, ROI_end, cur_frame)

        cv2.imshow("Original", frame3)
        cv2.imshow("white_mask", color_mask)
        cv2.imshow("Three-Frame mask", diff_mask)
        cv2.imshow("final_mask", final_diff)

    return is_detect

def start(cap, render, ROI, img_idx, progress=None):
    annotations = []

    # 获取总帧数
    total_fps = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    ROI_start = ROI[0]
    ROI_end = ROI[1]

    fps = int(cap.get(cv2.CAP_PROP_FPS))  # 帧率
    print(f'fps:{fps}')
    threshold = int(fps * 0.13)

    _, frame1 = cap.read()
    _, frame2 = cap.read()
    frame1 = frame1[ROI_start[1]:ROI_end[1], ROI_start[0]:ROI_end[0]]
    frame2 = frame2[ROI_start[1]:ROI_end[1], ROI_start[0]:ROI_end[0]]

    # 计算缩放后的尺寸
    width = 540
    h, w, _ = frame1.shape
    height = int(h / w * width)
    frame_size = (width, height)

    print(f'ROI窗口大小：{frame_size}')

    # 缩放ROI区域为固定大小
    frame1 = cv2.resize(frame1, frame_size, interpolation=cv2.INTER_AREA)  # 这个参数好像是更清晰，不管算了
    frame2 = cv2.resize(frame2, frame_size, interpolation=cv2.INTER_AREA)

    # 记录剪辑帧
    frame_count = 1
    start_frame = frame_count
    end_frame = frame_count
    # 是否跳过
    should_skip = False

    # 记录有效对局帧
    count = 0
    steps_count = 0
    detect_count = 0
    out_of_game = True

    with tqdm(total=total_fps, desc=f"正在生成切片序列 {frame_count}/{total_fps}") as pbar:
        while True:
            # 每秒统计有多少帧测到了球，以此判断是否在对局中
            if count == fps:
                if detect_count >= threshold:
                    # print(f'detect count:{detect_count}')
                    steps_count += 1
                # 到此为止不再检测到球，代表对局结束
                elif steps_count > 0:
                    # print(f'回合结束，本回合时长:{steps_count}s')
                    out_of_game = True
                    steps_count = 0
                    end_frame = frame_count + int(fps * 0.7)

                    # 如果开头过早，则直接在上一个回合中加长末尾
                    # if should_skip:
                    #     should_skip = False
                    #     annotations[-1][1] = end_frame
                    # else:
                    annotations.append([start_frame, end_frame])
                # 仍然未检测到球，保持对局外状态
                else:
                    out_of_game = True
                count = 0
                detect_count = 0


            ret, cur_frame = cap.read()
            if not ret:
                annotations[-1][1] = min(frame_count, annotations[-1][1])  # 修正最后一帧
                break

            frame3 = cur_frame[ROI_start[1]:ROI_end[1], ROI_start[0]:ROI_end[0]]
            frame3 = cv2.resize(frame3, frame_size, interpolation=cv2.INTER_AREA)

            # 检测球
            if(detect_ball(frame1, frame2, frame3, render, ROI_start, ROI_end, cur_frame)):
                # 如果是对局的第一次检测到球，则从此时开始计数
                if out_of_game:
                    count = 0
                    out_of_game = False
                    start_frame = max(1, frame_count - int(fps * 0.7))
                    # 如果开始点早于之前的末尾，则合并这一段
                    # if len(annotations) > 0 and start_frame < annotations[-1][1]:
                    #     should_skip = True
                detect_count += 1

            frame1, frame2 = frame2, frame3  # 更新帧

            count += 1
            frame_count += 1

            if render and cv2.waitKey(5) & 0xFF == 27:
                break

            # 更新tqdm描述信息
            pbar.set_description(f"Processing record {frame_count}/{total_fps}")
            pbar.update(1)

            if progress is not None:
                progress(frame_count / total_fps, desc=f"第{img_idx}个视频处理中...  正在生成切片序列 {frame_count}/{total_fps}")

    # print(annotations)

    if render:
        cv2.destroyAllWindows()

    return annotations

if __name__ == '__main__':
    video_path = "video/IMG_1747.mov"
    output_path = "output/sample_output_1.mp4"

    ROI = ((600, 0), (1600, 900))
    # ROI = ((400, 0), (1550, 900))

    cap = cv2.VideoCapture(video_path)
    annotations = start(cap, True, ROI, 0)
    cap.release()
    print('开始导出。。。')
    # cut_and_concat_video(video_path, annotations, output_path)
