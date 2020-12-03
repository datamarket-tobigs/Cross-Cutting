import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
import random
import numpy as np
import time
from video_facial_landmarks_minmax import calculate_distance
from face_embedding import calculate_euclidean_distance
import cv2
import subprocess


ONE_FRAME_SEC = 0.03336666666666588 # 29.97002997002997fps의 역수! 한 프레임당 시간을 계싼해서 프레임 id만 알면 현재 시간 알수 있도록 함# 0.03336666666666588??
EYE_MIN_DIFF = 65 # 두 영상의 눈 크기 차이가 거리 이상이면, crossfade 전환 하지 않는다. 
TOTAL_MIN_DIFF = 200 # 두 영상의 눈 거리가 이 이상이면 전환 자체를 시도하지 않는다(엉뚱한데 옮겨가는거 피하기)
ROTATE_MAX = 7 # 각 도 차이가 이 값 이상이면, crossfade 전환하지 않는다.
WINDOW_TIME = 10 # WINDOW_TIME 초 안에서 최소 거리를 찾는다. 얼굴이 겹치는 부분이 없다면, WINDOW_TIME 만큼 자르고 radom으로 다음 영상을 재생한다.
PADDED_TIME = 3 # 최소 시간으로 영상을 자른 뒤 PADDED_TIME 만큼은 얼굴 거리를 계산하지 않는다.
# TRANSITION INFO
ZOOM_FRAME = 20 # 얼굴 확대하는 FRAME 수
CROSS_FRAME = 4 # CrossFade FRAME 수
ONE_ZOOM = 1.2 # 회전 확대 후 검은 비율을 줄이기 위해서 확대하는 비율
AGAIN_ZOOM = 1.15 # 영상이 확대가 불가능(영상 최대 크기 넘어감)할 때 한번 더 확대할 수 있는 비율. 한번 더 확대하고도 범위가 넘어가면, 그냥 아무 효과없이 전환한다.
PANELTY = 100
print('hyper parameter')
print(ONE_FRAME_SEC, EYE_MIN_DIFF, ROTATE_MAX, WINDOW_TIME, PADDED_TIME, ZOOM_FRAME, CROSS_FRAME, ONE_ZOOM, AGAIN_ZOOM)
TEST = False
TEST_TIME = 30

def distance(reference_clip, clip, use_face_panelty = False):
    # cv2 를 이용해서 최대 거리, 최소 시간, 거리, 각도, 눈 위치를 구한다.
    min_diff, min_time, info = calculate_distance(reference_clip, clip)
    
    if use_face_panelty:
        # 얼굴이 다른 경우에 penalty 주기!
        ref_frame = reference_clip.get_frame(min_time)
        frame = clip.get_frame(min_time)
        
        e_dist = calculate_euclidean_distance(ref_frame, frame)
        print("Face Panelty Applied With ", e_dist / 1.25 *penalty)
        min_diff += e_dist / 1.25 *penalty # 범위 0~1로 바꿔주기 위함

    return min_diff, min_time,\
        info['refer_length'], info['refer_degree'], \
        info['compare_length'], info['compare_degree'], \
        info['refer_point'], info['compare_point']

# Moving = 더 작은 쪽에서 하는 것!
# Rotate 할 때 빈 자리 메꾸기 위해서 기본적으로 ONE_ZOOM 만큼 확대하기!
class Moving:
    def __init__(self,small_point, big_point, ratio, transition_dir, rotate_degree, default_zoom = 1):
        self.small_point = small_point[0] # 왼쪽 눈
        self.big_point = big_point[0] # 왼쪽 눈
        self.ratio = ratio # 확대비율
        self.transition_dir = transition_dir # 점점 커질건지(small_to_big), 작아질건지(big_to_small), 그대로 둘건지(same)
        self.rotate_degree = rotate_degree # 이동해야 하는 각도
        self.default_zoom = default_zoom
    def __call__(self, get_frame, t):
        frame = get_frame(t)
        if len(self.small_point)==0: # 얼굴이랄게 없을때
            return frame
        else:
            # ratio만큼 영상을 키운다(더 작은 영상이 더 큰 영상 사이즈에 맞춤)
            img_cv = cv2.resize(frame,(int(round(1280 * self.ratio * self.default_zoom)),int(round(720 * self.ratio * self.default_zoom))))
            cur_w = self.small_point[0] * self.ratio * self.default_zoom
            cur_h = self.small_point[1] * self.ratio * self.default_zoom

            if self.transition_dir == 'small_to_big':
                cur_degree = self.rotate_degree*(t/ONE_FRAME_SEC)/ZOOM_FRAME # 0에서 rotate_degree까지
            elif self.transition_dir == 'big_to_small': 
                cur_degree = self.rotate_degree*(ZOOM_FRAME-t/ONE_FRAME_SEC)/ZOOM_FRAME
            else: 
                cur_degree = self.rotate_degree

            # width height 순서
            M = cv2.getRotationMatrix2D((cur_w, cur_h), cur_degree, 1.0)
            img_cv = cv2.warpAffine(img_cv, M, (int(round(1280 * self.ratio * self.default_zoom)),int(round(720 * self.ratio * self.default_zoom))))
            zoom_frame = np.asarray(img_cv)

            # 더 큰 부분과 위치가 같아저야 하는것이므로 더 큰 포인트의 위치 비율을 계산한다.
            w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
            h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
            
            # 혹시 사이즈가 넘어가면 사이즈를 self.default_zoom 만큼 한번 더 크게 해보기(너무 딱 맞춰서 확대하려고 하지말구!)
            # ! 여기선 self.default_zoom 뺀 상태로 확대해야 한다(그래야 원하는 크기로 잘리지)
            w1, w2 = int(round(cur_w - 1280 * self.ratio * w_ratio)), int(round(cur_w + 1280 * self.ratio  *(1-w_ratio)))
            h1, h2 = int(round(cur_h - 720 * self.ratio * h_ratio)), int(round(cur_h + 720 * self.ratio *(1-h_ratio)))
            if h1>=0 and h2<=int(round(720 * self.ratio * self.default_zoom)) and w1>=0 and w2 <=int(round(1280 * self.ratio * self.default_zoom)):
                # 시간초에 따라서 바뀌어야 함!
                zoom_w_size, zoom_h_size =  1280 * self.ratio*self.default_zoom, 720 * self.ratio*self.default_zoom 
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                # 16:9 비율 유지하면서 이동할 위치에 ratio만큼 자르기!
                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔는지 체크
                if h1>=0 and h2<=int(round(720 * self.ratio * self.default_zoom)) and w1>=0 and w2 <=int(round(1280 * self.ratio * self.default_zoom)):
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    frame_region = frame
                return frame_region
            else:
                # 딱 한번 확대 기회를 주자!
                img_cv = cv2.resize(zoom_frame, dsize=(0, 0),fx= self.default_zoom * AGAIN_ZOOM, fy= self.default_zoom * AGAIN_ZOOM) # AGAIN_ZOOM 만큼 확대하기
                zoom_frame = np.asarray(img_cv)
                cur_w = self.small_point[0] * self.ratio * self.default_zoom * AGAIN_ZOOM
                cur_h = self.small_point[1] * self.ratio * self.default_zoom * AGAIN_ZOOM

                w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
                h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
                
                zoom_w_size, zoom_h_size =  1280 * self.ratio * self.default_zoom * AGAIN_ZOOM, 720 * self.ratio * self.default_zoom * AGAIN_ZOOM
                # 시간초에 따라서 바뀌어야 함!
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    # print(W_real, H_real, "W real H real")
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔을때!
                if h1>=0 and h2<=int(round(720 * self.ratio*self.default_zoom *AGAIN_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio*self.default_zoom *AGAIN_ZOOM)):
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    frame_region = frame
                return frame_region


# 이건 사이즈가 안맞아서 한번 더 확대 했을때 다른 쪽 영상을 처리하는 Class
# ForceZoom = 더 큰쪽에서 하는 것!!
class ForceZoom:
    def __init__(self,small_point, big_point, ratio, transition_dir, default_zoom = 1):
        self.small_point = small_point[0]
        self.big_point = big_point[0]
        self.ratio = ratio
        self.transition_dir = transition_dir 
        self.default_zoom = default_zoom
        # 여긴 큰 부분 영상 처리하는 것이므로 rotation은 필요없다.
    def __call__(self, get_frame, t):
        # any process you want
        frame = get_frame(t)
        if len(self.small_point)==0:
            return frame
        else:
            print('--------------------- DO FORCE ZOOM')
            img_cv = cv2.resize(frame,(int(round(1280 *self.default_zoom * self.ratio)),int(round(720 *self.default_zoom* self.ratio))))
            zoom_frame = np.asarray(img_cv)
            cur_w = self.small_point[0] *self.default_zoom * self.ratio
            cur_h = self.small_point[1] *self.default_zoom * self.ratio
            # 이동할 애 기준으로 만들어야 함!
            w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
            h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
            
            w1, w2 = int(round(cur_w - 1280 * self.ratio * w_ratio)), int(round(cur_w + 1280 * self.ratio  *(1-w_ratio)))
            h1, h2 = int(round(cur_h - 720 * self.ratio * h_ratio)), int(round(cur_h + 720 * self.ratio *(1-h_ratio)))

            # 확대될 사이즈도 확인(Force ZOOM 이 가능했었니? az = again zoom) - 확대 되었을때만 Force Zoom 하면 되니까!
            cur_w_az = self.small_point[0] *self.default_zoom * self.ratio * AGAIN_ZOOM
            cur_h_az = self.small_point[1] *self.default_zoom * self.ratio * AGAIN_ZOOM
            w1_az, w2_az = int(round(cur_w_az - 1280 * self.ratio * w_ratio)), int(round(cur_w_az + 1280 * self.ratio  *(1-w_ratio)))
            h1_az, h2_az = int(round(cur_h_az - 720 * self.ratio * h_ratio)), int(round(cur_h_az + 720 * self.ratio *(1-h_ratio)))
            
            # 원래건 안되고(not) 확대되는건 되어야 함!! (원래게 되었으면 확대를 안했겠지? 확대가 안되면 그냥 뒀겠지?)
            if not( h1>=0 and h2<=int(round(720 * self.ratio*self.default_zoom)) and w1>=0 and w2 <=int(round(1280 * self.ratio*self.default_zoom))) and \
               h1_az>=0 and h2_az<=int(round(720 * self.ratio*self.default_zoom*AGAIN_ZOOM)) and w1_az>=0 and w2_az<=int(round(1280 * self.ratio*AGAIN_ZOOM*self.default_zoom)):
                # 사이즈가 넘어가서 확대를 했었다면, 나는 처음부터 다시 시작하자!
                img_cv = cv2.resize(frame, dsize=(0, 0),fx=self.default_zoom * AGAIN_ZOOM, fy=self.default_zoom * AGAIN_ZOOM) # AGAIN_ZOOM 만큼 확대하기
                zoom_frame = np.asarray(img_cv)
                cur_w = self.big_point[0] * self.default_zoom * AGAIN_ZOOM
                cur_h = self.big_point[1] * self.default_zoom * AGAIN_ZOOM

                w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
                h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
                
                zoom_w_size, zoom_h_size =  1280 * self.default_zoom  * AGAIN_ZOOM, 720  * self.default_zoom * AGAIN_ZOOM
                # 시간초에 따라서 바뀌어야 함!
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    # 사이즈가 더 커지면, 다시 resize할떄 작아짐. 그래서 처음에는 작은 사이즈에서 큰 사이즈로 가면, resize후엔 확대 후 축소한는거 같음
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720


                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))

                if h1>=0 and h2<=int(round(720 * self.ratio*self.default_zoom*AGAIN_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio*self.default_zoom*AGAIN_ZOOM)):
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    frame_region = frame
                return frame_region
            else: # 그런 경우 아니었으면 self.default_zoom 만 하고 return
                # 사이즈가 넘어가서 확대를 했었다면, 나는 처음부터 다시 시작하자!
                # 이때는 그냥 한번 확대해주자!
                img_cv = cv2.resize(frame, dsize=(0, 0),fx=self.default_zoom, fy=self.default_zoom) # AGAIN_ZOOM 만큼 확대하기
                zoom_frame = np.asarray(img_cv)
                cur_w = self.big_point[0] * self.default_zoom 
                cur_h = self.big_point[1] * self.default_zoom

                # 이동할 애 기준으로 만들어야 함!
                w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
                h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
                
                zoom_w_size, zoom_h_size =  1280 * self.default_zoom, 720  * self.default_zoom
                # 시간초에 따라서 바뀌어야 함!
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    # 사이즈가 더 커지면, 다시 resize할떄 작아짐. 그래서 처음에는 작은 사이즈에서 큰 사이즈로 가면, resize후엔 확대 후 축소한는거 같음
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔을때!
                if h1>=0 and h2<=int(round(720 * self.ratio*self.default_zoom)) and w1>=0 and w2 <=int(round(1280 * self.ratio*self.default_zoom)):
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    frame_region = frame
                return frame_region


 
def crosscut(videos_path="./video", option="random", use_face_panelty=False):
    subprocess.call(f'rm -rf {videos_path}/.DS_Store', shell=True)

    min_time = 1000.0
    min_idx = 0
    audioclip = None
    extracted_clips_array = []
    video_num = len(os.listdir(videos_path))
    start_times = [0] * video_num # VIDEO ALIGNMENT -> SLICE START TIME
    # init (refer 가 지금 현재 영상, compare가 비교하는 다음 영상)
    refer_point_min = [(0,0),(0,0)]
    compare_point_min = [(0,0),(0,0)]
    refer_length_min = 0
    compare_length_min = 0
    refer_degree_min = 0
    compare_degree_min = 0
    INIT_NUM = 5000000

    for i in range(len(os.listdir(videos_path))):
        video_path = os.path.join(videos_path, sorted(os.listdir(videos_path))[i]) # 순서가 뒤죽박죽 되지 않게!
        clip = VideoFileClip(video_path)
        clip = clip.subclip(start_times[i], clip.duration) # 영상 시작점을 맞추기 위해서 start_times 참조
        print(video_path, clip.fps, clip.duration)
        if min_time > clip.duration: # 제일 작은 영상 기준으로 길이 잡기
            audioclip = clip.audio
            min_time = clip.duration
            min_idx = i
        extracted_clips_array.append(clip)
    
    print(len(extracted_clips_array),' videos min idx is ', min_idx, ' time',min_time)

    con_clips = []
    t = 3
    current_idx = 0
    check_tqdm = 1
    
    con_clips.append(extracted_clips_array[current_idx].subclip(0, min(t, int(min_time)))) # 앞에서 시작점은 맞춰졌으므로 0부터 시작하면 된다!
    
    
    if TEST: # test하면 일부분만 생성해서 빠르게 확인하기
        CHECK_DURATION = TEST_TIME
        min_time = CHECK_DURATION
        audioclip = audioclip.set_duration(CHECK_DURATION)
    
    # GENERATE STAGEMIX
    # CONCAT SUBCLIP 0~ MIN DURATION CLIP TIME
    while t < min_time:
        print(check_tqdm,'------------------------------------------------------------------')
        check_tqdm += 1
        # 최대 WINDOW TIME만큼 영상을 generate 할 예정
        cur_t = t
        next_t = min(t+WINDOW_TIME, min_time) # 마지막은 window초보다 작은초일수도 있으니

        # RANDOM BASED METHOD
        if option=="random" or min(min_time,t + PADDED_TIME)==min_time: # 혹시 제일 마지막 영상이면 random으로 생성할 수도 있음!
            random_video_idx = random.randint(0, len(extracted_clips_array)-1)
            clip = extracted_clips_array[random_video_idx].subclip(cur_t, next_t)
            t = next_t
            con_clips.append(clip)
        else:
            reference_clip = extracted_clips_array[current_idx].subclip(cur_t, next_t) # 지금 현재 영상!
            d = INIT_NUM # init
            
            # 거리가 Inf일때는 있을때는 이 idx로 설정됨!
            # --------------------------------------------------------------
            # 최소거리 영상 찾고 편집 위한 정보 얻기 -------------------------------
            # --------------------------------------------------------------
            min_idx = (current_idx+1)%len(extracted_clips_array) 
            for video_idx in range(len(extracted_clips_array)):
                # 같은 영상 나올수도 있는 문제 해결
                if video_idx == current_idx:
                    continue
                # WINDOW_TIME초 간 영상 확인
                clip = extracted_clips_array[video_idx].subclip(cur_t, next_t) 
                
                # PADDING TIME이 들어가면 엄청 좋은 부분을 놓칠수도 있지만, 넣어야 계속해서 그 주변에서 전환되는 문제가 해결됨!
                # CALCULATE DISTANCE between reference_clip, compare_clip(같은초에서 최선의 거리 장면 찾기)
                cur_d, plus_frame, refer_length, refer_degree, compare_length, compare_degree, refer_point, compare_point = distance(reference_clip, clip, use_face_panelty=use_face_panelty) 
                print('from video:',current_idx, ' to video',video_idx, ' in distance ',cur_d, ' in sec ' ,cur_t + plus_frame, 'first deg ', refer_degree, 'second deg ', compare_degree, ' refer length ', refer_length, ' compare length', compare_length)
                
                if d > cur_d: # 최소 정보 찾기!
                    d = cur_d
                    min_idx = video_idx
                    next_t = cur_t + plus_frame # 바로 옮길 frame
                    cur_clip = reference_clip.subclip(0,plus_frame)
                    next_clip = clip.subclip(0, plus_frame) # 그 바꿀 부분만 자르는 클립!
                    compare_point_min = compare_point
                    refer_point_min = refer_point
                    refer_length_min = refer_length # 이거에 맞춰서 확대 축소 해줄거야!
                    compare_length_min = compare_length # 이거에 맞춰 확대 축소 해줄거야!
                    refer_degree_min = refer_degree
                    compare_degree_min = compare_degree
            
            if d == INIT_NUM or (not cur_clip): # 거리가 모두 inf일떄, cur_clip 자체가 비어있을때
                print("ALL DISTANCE INFINITE PROBLEM !!! --> APPEND NEXT INDEX VIDEO...")
                # current_idx는 다음으로 넘어간다!!!
                current_idx = min_idx # 다음에 재생될 idx
                clip = reference_clip # 현재 클립(여기는 거리가 Inf이므로 10초 전체가 잘려있다!)
                t = min(t+WINDOW_TIME, min_time) # 마지막은 window초보다 작은초일수도 있으니
                con_clips.append(clip)
                if t < min_time: # t가 이미 min_time을 넘었을땐 더할 필요도 없음!
                    # 뒤에 padding 데이터 더하기
                    pad_clip = extracted_clips_array[current_idx].subclip(t, min(min_time,t+PADDED_TIME)) # min_time을 넘어가면 안됨!
                    t = min(min_time,t + PADDED_TIME) # padding 된 시간 더하기
                    con_clips.append(pad_clip)
            else: 
                print("MIN DISTANCE VIDEO FOUND...!")
                # (!! 현재 영상을 concat 하고 다음에 넣을 영상 idx를 저장해야 한다!)
                prev_idx = current_idx
                current_idx = min_idx # 바로 다음에 이어지는 영상 index
                clip = cur_clip # 현재 클립(바꾸면 가장 좋은 부분까지 잘린 현재 클립)
                print("next video idx : {}".format(current_idx))
                print('----refer, compare length : ', refer_length_min, compare_length_min)
                print('----refer, compare point information : ', refer_point_min, compare_point_min)
                print('----refer, compare degree information : ', refer_degree_min, compare_degree_min)

                # 여기서 편집하기 -------------------------------------------------
                t = next_t
                # --------------------------------------------------------------
                # 1. Transition 전 영상 효과 없이 넣기 ------------------------------
                # --------------------------------------------------------------
                clip_front = clip.subclip(0,clip.duration-(ONE_FRAME_SEC*ZOOM_FRAME)) # 전환 효과 없이 들어갈 클립!
                con_clips.append(clip_front)

                # --------------------------------------------------------------
                # 2. Transition 영상 넣기(ZOOM_FRAME만큼) --------------------------
                # --------------------------------------------------------------
                clip_back = clip.subclip(clip.duration-(ONE_FRAME_SEC*ZOOM_FRAME),clip.duration)
                ## 해당 조건을 만족하면 resize및 transition 허용
                if abs(compare_length_min-refer_length_min) < EYE_MIN_DIFF and abs(compare_degree_min-refer_degree_min) < ROTATE_MAX and d < TOTAL_MIN_DIFF:
                    # 앞 영상이 더 작으면 Moving 함수를 실행해서 앞 영상 확대하기
                    if compare_length_min> refer_length_min:
                        clip_back = clip_back.fl(Moving(refer_point_min, compare_point_min, compare_length_min/refer_length_min,'small_to_big',refer_degree_min-compare_degree_min))
                        clip_back = clip_back.resize((1280,720))
                    else: # 뒤 영상이 더 작으면 ForceZoom을 통해서 사이즈 맞추기(self.default_zoom을 통해서 더 커지기 때문에)
                        clip_back = clip_back.fl(ForceZoom(compare_point_min, refer_point_min, refer_length_min/compare_length_min,'small_to_big'))
                        clip_back = clip_back.resize((1280,720))
                    
                    con_clips.append(clip_back)
                else:
                    con_clips.append(clip_back)
                
                # ---------------------------------------------------
                # 3. 다음 영상에 padding 데이터 더하기 ---------------------
                # ---------------------------------------------------
                pad_clip = extracted_clips_array[current_idx].subclip(t, min(min_time,t + PADDED_TIME)) # min_time을 넘어가면 안됨!
                # padding 데이터도 효과를 넣을지 안넣을지 판단!
                if abs(compare_length_min-refer_length_min) < EYE_MIN_DIFF and abs(compare_degree_min-refer_degree_min) < ROTATE_MAX and d < TOTAL_MIN_DIFF:
                    ### PAD FRONT ---------------
                    pad_front = pad_clip.subclip(0,ONE_FRAME_SEC*ZOOM_FRAME) # 그 바꿀 부분만 자르는 클립!
                    # 앞이 더 크고 뒤(pad_clip)가 작을 때
                    if refer_length_min> compare_length_min:
                        # pad_clip을 확대 해줘야 함
                        pad_front = pad_front.fl(Moving(compare_point_min, refer_point_min, refer_length_min/compare_length_min, 'big_to_small',compare_degree_min-refer_degree_min))
                        pad_front = pad_front.resize((1280,720))
                        # 앞 영상 연속해서 틀면서 cross fade!(이때는 앞 영상은 회전및 확대가 없으므로 그대로 재생!)
                        # !!!! 여기 잠깐 주석
                        # cross_clip = extracted_clips_array[prev_idx].subclip(t, t+ONE_FRAME_SEC*CROSS_FRAME) # min_time을 넘어가면 안됨!
                        # cross_clip = cross_clip.fl(ForceZoom(compare_point_min, refer_point_min, refer_length_min/compare_length_min, 'same')) # 여기서도 ForceZoom 필수!
                        # pad_front = CompositeVideoClip([pad_front, cross_clip.crossfadeout(ONE_FRAME_SEC*CROSS_FRAME)])
                        # !!! 주석 끝
                    else: # 앞이 더 작은 경우 
                        pad_front = pad_front.fl(ForceZoom(refer_point_min, compare_point_min , compare_length_min/refer_length_min, 'big_to_small'))
                        pad_front = pad_front.resize((1280,720))
                        # !!!! 여기 잠깐 주석
                        # cross_clip = extracted_clips_array[prev_idx].subclip(t, t+ONE_FRAME_SEC*CROSS_FRAME) # min_time을 넘어가면 안됨!
                        # cross_clip = cross_clip.fl(Moving(refer_point_min, compare_point_min, compare_length_min/refer_length_min, 'same',refer_degree_min-compare_degree_min))
                        # pad_front = CompositeVideoClip([pad_front, cross_clip.crossfadeout(ONE_FRAME_SEC*CROSS_FRAME)])
                        # !!! 주석 끝
                    con_clips.append(pad_front)
                    
                    ### PAD BACK ---------------
                    pad_back = pad_clip.subclip(ONE_FRAME_SEC*ZOOM_FRAME,pad_clip.duration) # 그 바꿀 부분만 자르는 클립!
                    t = min(min_time, t + PADDED_TIME) # padding 된 시간 더하기
                    con_clips.append(pad_back)
                else:
                    t = min(min_time, t + PADDED_TIME) # padding 된 시간 더하기
                    con_clips.append(pad_clip)

    # 영상 다 붙이기!
    final_clip = concatenate_videoclips(con_clips)
    if audioclip !=None:
        final_clip.audio = audioclip

    final_clip.write_videofile("video.mp4")
    return final_clip

start_time = time.time()

use_face_panelty = True # FacePanelty를 사용하면 Panelty값이 기본적으로 들어가니까 자연스러운 전환을 위해서는 역치값을 높여아 함
if use_face_panelty==True:
    EYE_MIN_DIFF += PANELTY 
    TOTAL_MIN_DIFF += PANELTY 
crosscut(videos_path="./video", option="norandom", use_face_panelty = False)
end_time = time.time()

print(end_time - start_time, 'total Generation time')
