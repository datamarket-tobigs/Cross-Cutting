from torchvision import models
import numpy as np
import torch
import os
from moviepy.editor import VideoFileClip

SKIP_FRAME_RATE = 10
MINIMAX_FRAME = 4
# 함수에서 documentaiton 읽기
model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
model.eval()
os.environ['KMP_DUPLICATE_LIB_OK']='True'

def extract_boxes(reference_clip, compare_clip):
    clips = [reference_clip, compare_clip]
    clips_frame_info = []
    for clip in clips:
        i = 0
        every_frame_info = []
        # loop over the frames from the video stream
        while True:
            i+=SKIP_FRAME_RATE # 1초에 60 fps가 있으므로 몇개는 skip해도 될거 같음!
            if (i*1.0/clip.fps)> clip.duration:
                break

            frame = clip.get_frame(i*1.0/clip.fps)
            frame = frame/255 # image, and should be in ``0-1`` range.
            frame = np.transpose(frame, (2,0,1)) #  HWC -> CHW(그 위치에 몇차원 애를 넣을거냔?)
            x = [torch.from_numpy(frame).float()]
            # label list https://github.com/tensorflow/models/blob/master/research/object_detection/data/mscoco_label_map.pbtxt
            predictions = model(x)
            prediction= predictions[0]
            each_box_list = zip(prediction['boxes'].tolist(), prediction['labels'].tolist(), prediction['scores'].tolist())
            # 0.95 정도 올려야 까맣게 보이는 관중이 없어짐!
            filtered_box_list = filter(lambda x: x[1]==1 and x[2] >= 0.95, each_box_list)
            filtered_center_dot_list = list(map(lambda x: [(x[0][0]+x[0][2])/2, (x[0][1]+x[0][3])/2], filtered_box_list))
            # x좌표로 정렬하기(대형이 가로로 늘어져 있다고 가정하고 순서대로 정렬)
            sorted_dot_list = sorted(filtered_center_dot_list, key = lambda x: x[0])
            every_frame_info.append(sorted_dot_list) # 프레임별 정보
        
        clips_frame_info.append(np.array(every_frame_info)) # 각 영상별로 붙이기

    return clips_frame_info

def calculate_pose_distance(reference_clip, compare_clip):
    clips_frame_info = extract_boxes(reference_clip, compare_clip) # 모든 프레임마다 길이 계산해줌

    min_size = min(len(clips_frame_info[0]),len(clips_frame_info[1]))
    
    dist_arr = list()
    # Calculate distance (by frame)
    for i in range(min_size):
        if len(clips_frame_info[0][i])>0 and len(clips_frame_info[1][i])>0: # 둘다 있으면
            # x축 값이 가장 가까운걸로 찾고 그거랑 비교(어차피 대형이 중요한거니까)
            ref_frame_dots = clips_frame_info[0][i] # 해당 frame의 정보
            compare_frame_dots = clips_frame_info[1][i] # 해당 frame의 정보
            min_dot_num = min(len(ref_frame_dots), len(compare_frame_dots)) # reference 기준으로 계산할거양
            penalty = ((reference_clip.w **2 + reference_clip.h**2)**0.5) * abs(len(ref_frame_dots)-len(compare_frame_dots)) # 개수가 다를때 주는 패널티
            total_diff = penalty
            for dot_idx in range(min_dot_num):
                ref_frame_dots[dot_idx] and compare_frame_dots[dot_idx]
                total_diff += ((ref_frame_dots[dot_idx][0] - compare_frame_dots[dot_idx][0])**2 + (ref_frame_dots[dot_idx][1] - compare_frame_dots[dot_idx][1])**2)**0.5
            dist_arr.append(total_diff)
        else:
            dist_arr.append(None)

    # Minimize max distance in (minimax_frames) frames
    min_diff = np.float('Inf')
    min_idx = 0 
    max_dist = []
    for i in range(min_size-(MINIMAX_FRAME-1)):
        if None in dist_arr[i:i+MINIMAX_FRAME]:
            max_dist.append(None)
        else:
            tmp_max = np.max(dist_arr[i:i+MINIMAX_FRAME])
            max_dist.append(tmp_max)
            if min_diff > tmp_max:
                min_diff = tmp_max
                min_idx = i

    # return distance, second, additional_info
    return min_diff, (min_idx*SKIP_FRAME_RATE)/reference_clip.fps, {}