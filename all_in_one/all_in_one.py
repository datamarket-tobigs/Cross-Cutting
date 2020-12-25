import os
import random
import datetime
import argparse
import time
import argparse
import numpy as np

from torchvision import models
import torch.nn as nn
import torch
import random

import dlib
import cv2
import imutils
from imutils.video import VideoStream
from imutils import face_utils
from moviepy.editor import *
from moviepy.editor import VideoFileClip, concatenate_videoclips



##############################################
#                                            #
#               generate stagemix            #
#                                            #
##############################################
class RandomDistance:
    def distance(self, reference_clip, compare_clip, args):
        dur_end = min(reference_clip.duration, compare_clip.duration)
        return random.randrange(1,100), min(dur_end, random.randrange(3,7)), {}

class FaceDistance:
    def __init__(self, shape_predictor_path):
        self.skip_frame_rate = 4 # 'the number of frames to skip'
        self.minimax_frames = 5 # 'the number of frames to minimax distance'
        # https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/
        self.shape_predictor = shape_predictor_path

    def extract_landmark(self, reference_clip, compare_clip):
        self.clips =[reference_clip, compare_clip]

        # face detect
        detector = dlib.get_frontal_face_detector()
        # face landmark
        predictor = dlib.shape_predictor(self.shape_predictor)

        # reference, compare 영상의 landmark 추출하기
        clips_frame_info = []
        for clip in self.clips:
            i=0
            every_frame_info= []
            # for every frame
            while True:
                frame = clip.get_frame(i*1.0/clip.fps)
                i+=self.skip_frame_rate # skip frames
                if (i*1.0/clip.fps)> clip.duration:
                    break
                
                # resizing width & convert to gray scale
                frame = imutils.resize(frame, width=800)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # face rect detect
                rects = detector(gray, 0)

                # if there is face recognized
                if len(rects)>0:
                    # find the largest face rect
                    max_width = 0
                    max_rect = None
                    for rect in rects:
                        if int(rects[0].width()) > max_width:
                            max_rect = rect
                    # face landmark coordinate: (x, y)
                    shape = predictor(gray, max_rect)
                    shape = face_utils.shape_to_np(shape)
                    every_frame_info.append(shape)
                else:
                    every_frame_info.append([])
        
            clips_frame_info.append(np.array(every_frame_info))

        cv2.destroyAllWindows()
        return clips_frame_info

    def get_all_frame_distance(self, clips_frame_info, min_size):
        dist_arr = []
        # Calculate distance by frame
        for i in range(min_size-1):
            if len(clips_frame_info[0][i])>0 and len(clips_frame_info[1][i+1])>0: # 얼굴 둘다 있으면
                # 두 영상에서 눈의 거리(왼쪽 눈 끼리, 오른쪽 눈 끼리)
                l = 36 # 왼쪽 눈 왼쪽 끝
                r = 45 # 오른쪽 눈3 오른쪽 끝
                left_eye = ((clips_frame_info[0][i][l][0] - clips_frame_info[1][i+1][l][0])**2 + (clips_frame_info[0][i][l][1] - clips_frame_info[1][i+1][l][1])**2)**0.5
                right_eye = ((clips_frame_info[0][i][r][0] - clips_frame_info[1][i+1][r][0])**2 + (clips_frame_info[0][i][r][1] - clips_frame_info[1][i+1][r][1])**2)**0.5
                total_diff = left_eye + right_eye
                dist_arr.append(total_diff)
            else:
                dist_arr.append(None)
        return dist_arr

    def distance(self, reference_clip, compare_clip, args):
        time.sleep(2.0)
        clips_frame_info = self.extract_landmark(reference_clip, compare_clip) # 모든 프레임마다 길이 계산해줌
        min_size = min(len(clips_frame_info[0]),len(clips_frame_info[1]))
        dist_arr = self.get_all_frame_distance(clips_frame_info, min_size)
        clips =[reference_clip,compare_clip]

        # Minimize max distance in (minimax_frames) frames
        minimax_frames = self.minimax_frames
        min_diff = np.float('Inf')
        min_idx = 0
        max_dist = []
        for i in range(min_size - (minimax_frames - 1)): # 해당 frame "이전과 이후"에 frame들 확인
            start_minmax_idx = 0 if (i - minimax_frames)<0 else i - minimax_frames
            if (None in dist_arr[start_minmax_idx :i + minimax_frames]):
                max_dist.append(None)
            else:
                tmp_max = np.max(dist_arr[start_minmax_idx:i + minimax_frames])
                max_dist.append(tmp_max)
                if min_diff > tmp_max:
                    min_diff = tmp_max
                    min_idx = i
        
        # return distance, second, additional_info
        return min_diff, (min_idx*self.skip_frame_rate)/self.clips[0].fps, {}

class PoseDistance:
    def __init__(self):
        self.SKIP_FRAME_RATE = 10
        self.MINIMAX_FRAME = 4
        # 함수에서 documentaiton 읽기
        self.model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
        self.model.eval()
        os.environ['KMP_DUPLICATE_LIB_OK']='True'

    def extract_boxes(self, reference_clip, compare_clip):
        self.clips = [reference_clip, compare_clip]
        clips_frame_info = []
        for clip in self.clips:
            i = 0
            every_frame_info = []
            # loop over the frames from the video stream
            while True:
                i+=self.SKIP_FRAME_RATE # 1초에 60 fps가 있으므로 몇개는 skip해도 될거 같음!
                if (i*1.0/clip.fps)> clip.duration:
                    break

                frame = clip.get_frame(i*1.0/clip.fps)
                frame = imutils.resize(frame, width=640)
                frame = frame/255 # image, and should be in ``0-1`` range.
                frame = np.transpose(frame, (2,0,1)) #  HWC -> CHW(그 위치에 몇차원 애를 넣을거냔?)
                x = [torch.from_numpy(frame).float()]
                # label list https://github.com/tensorflow/models/blob/master/research/object_detection/data/mscoco_label_map.pbtxt
                predictions = self.model(x)
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

    def get_all_frame_distance(self, clips_frame_info, min_size):
        dist_arr = list()
        # Calculate distance (by frame)
        for i in range(min_size):
            if len(clips_frame_info[0][i])>0 and len(clips_frame_info[1][i])>0: # 둘다 있으면
                # x축 값이 가장 가까운걸로 찾고 그거랑 비교(어차피 대형이 중요한거니까)
                ref_frame_dots = clips_frame_info[0][i] # 해당 frame의 정보
                compare_frame_dots = clips_frame_info[1][i] # 해당 frame의 정보
                min_dot_num = min(len(ref_frame_dots), len(compare_frame_dots)) # reference 기준으로 계산할거양
                dot_num_diff = abs(len(ref_frame_dots)- len(compare_frame_dots))
                penalty = ((self.clips[0].w **2 + self.clips[0].h**2)**0.5) * abs(len(ref_frame_dots)-len(compare_frame_dots)) # 개수가 다를때 주는 패널티
                total_diff = penalty * dot_num_diff
                for dot_idx in range(min_dot_num):
                    total_diff += ((ref_frame_dots[dot_idx][0] - compare_frame_dots[dot_idx][0])**2 + (ref_frame_dots[dot_idx][1] - compare_frame_dots[dot_idx][1])**2)**0.5
                dist_arr.append(total_diff)
            else:
                dist_arr.append(None)
        return dist_arr

    def distance(self, reference_clip, compare_clip, args):
        clips_frame_info = self.extract_boxes(reference_clip, compare_clip) # 모든 프레임마다 길이 계산해줌
        min_size = min(len(clips_frame_info[0]),len(clips_frame_info[1]))
        dist_arr = self.get_all_frame_distance(clips_frame_info, min_size)  

        # Minimize max distance in (minimax_frames) frames
        min_diff = np.float('Inf')
        min_idx = 0 
        max_dist = []
        for i in range(min_size-(self.MINIMAX_FRAME-1)):
            if None in dist_arr[i:i+self.MINIMAX_FRAME]:
                max_dist.append(None)
            else:
                tmp_max = np.max(dist_arr[i:i+self.MINIMAX_FRAME])
                max_dist.append(tmp_max)
                if min_diff > tmp_max:
                    min_diff = tmp_max
                    min_idx = i

        # return distance, second, additional_info
        return min_diff, (min_idx*self.SKIP_FRAME_RATE)/reference_clip.fps, {}

class FeatureExtractor(nn.Module):
    def __init__(self, model):
        super(FeatureExtractor, self).__init__()
        self.features = nn.Sequential(
            *list(model.children())[:-1] # models?
        )

    def forward(self, x):
        x = self.features(x)
        return x

class FeatureDistance:
    def __init__(self):
        r3d_model = models.video.r3d_18(pretrained=True)
        self.model = FeatureExtractor(r3d_model)
        
    def distance(self, reference_clip, compare_clip, args):
        ref_frames = []
        frames = []
        for t in range(0, 10, 1):
            ref_frames.append(cv2.resize(reference_clip.get_frame(t) / 255.0, (108, 192)))
            frames.append(cv2.resize(compare_clip.get_frame(t) / 255.0, (108, 192)))

        ref_frames = torch.from_numpy(np.array(ref_frames).reshape(-1, 3, 10, 108, 192)).float()
        frames = torch.from_numpy(np.array(frames).reshape(-1, 3, 10, 108, 192)).float()

        ref_feature = self.model(ref_frames)
        feature = self.model(frames)

        ret = ref_feature - feature
        return np.mean(np.abs(ret.detach().numpy())), reference_clip.duration, {}



class Crosscut:
    def __init__(self, dist_obj, video_path, output_path):
        self.videos_path = video_path # vieo"들"이 있는 path
        self.output_path = output_path
        self.min_time = 1000.0 # 가장 짧은 영상의 길이(INIT)
        video_num = len(os.listdir(self.videos_path))
        self.start_times = [0] * video_num
        self.window_time = 10
        self.padded_time = 4 # padding time
        self.dist_obj = dist_obj
        self.audioclip = None # 기준으로 사용할 audio
        self.extracted_clips_array = []
    
    def video_alignment(self):
        # VIDEO ALIGNMENT -> SLICE START TIME
        for i in range(len(os.listdir(self.videos_path))):
            video_path = os.path.join(self.videos_path, sorted(os.listdir(self.videos_path))[i])
            clip = VideoFileClip(video_path)
            clip = clip.subclip(self.start_times[i], clip.duration)
            if self.min_time > clip.duration:
                self.audioclip = clip.audio
                self.min_time = clip.duration
            self.extracted_clips_array.append(clip)
        print(f'LOGGER-- {len(self.extracted_clips_array)} Video Will Be Mixed')


    def generate_video(self):
        self.video_alignment()
        # CONCAT SUBCLIP 0~ MIN DURATION CLIP TIME
        extracted_clips_array = self.extracted_clips_array
        con_clips = [] # Staged Mixed Clip array
        t = 3 # 초반 3초 INIT
        current_idx = 0 # INIT
        
        con_clips.append(extracted_clips_array[current_idx].subclip(0, min(t, int(self.min_time)))) #초반 padding
        while t < int(self.min_time):
            # Cut 10 sec.
            cur_t = t
            next_t = min(t+self.window_time, self.min_time)

            reference_clip = extracted_clips_array[current_idx].subclip(cur_t, next_t)
            d = float("Inf")
            cur_clip = None
            min_idx = (current_idx+1)%len(extracted_clips_array) # 거리가 무한일 때 최소한 나는 선택하지 않도록 하기
            for video_idx in range(len(extracted_clips_array)):
                if video_idx == current_idx:
                    continue
                clip = extracted_clips_array[video_idx].subclip(cur_t, next_t) 
                
                cur_d, plus_frame, additional_info = self.dist_obj.distance(reference_clip, clip, {}) 
                print(current_idx, video_idx, cur_d, cur_t + plus_frame)
                if d > cur_d:
                    d = cur_d
                    min_idx = video_idx
                    next_t = cur_t + plus_frame # 바로 옮길 frame
                    cur_clip = reference_clip.subclip(0, plus_frame)
            if cur_clip: 
                clip = cur_clip 
            else:
                clip = reference_clip
            t = next_t
            con_clips.append(clip)

            # 다음 clip : padding 길이는 반드시 append
            current_idx = min_idx 
            print("idx : {}".format(current_idx))
            pad_clip = extracted_clips_array[current_idx].subclip(t, min(self.min_time,t+self.padded_time))
            t = min(self.min_time,t + self.padded_time)
            con_clips.append(pad_clip)

        final_clip = concatenate_videoclips(con_clips)

        if self.audioclip !=None:
            print("Not None")
            final_clip.audio = self.audioclip

        final_clip.write_videofile(self.output_path)
        return final_clip


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--video_path', default='./videos', help='videos directory path')
    parser.add_argument('--method', default='face', help='random, feature, face and pose (stagemix method)')
    parser.add_argument('--output_path', default='my_stagemix.mp4', help='save path of output "path/name.mp4" format')
    parser.add_argument('--shape_predictor_path', default='shape_predictor_68_face_landmarks.dat', help='path of "shape_predictor_68_face_landmarks.dat"-landmarks predictor')
    
    args = parser.parse_args()
    method = args.method # random, feature, landmark
    video_path = args.video_path
    output_path = args.output_path
    shape_predictor_path = args.shape_predictor_path

    print(output_path)
    # ~.py --method random
    if method == 'random':
        random_distance = RandomDistance()
        cross_cut = Crosscut(random_distance, video_path, output_path)
    elif method == 'face':
        face_distance = FaceDistance(shape_predictor_path)
        cross_cut = Crosscut(face_distance, video_path, output_path)
    elif method == 'pose':
        pose_distance = PoseDistance()
        cross_cut = Crosscut(pose_distance, video_path, output_path)
    elif method == 'feature':
        feature_distance = FeatureDistance()
        cross_cut = Crosscut(feature_distance, video_path, output_path)
    cross_cut.generate_video()