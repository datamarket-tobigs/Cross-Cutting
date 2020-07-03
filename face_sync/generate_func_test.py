import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import random
import numpy as np
import time
from video_facial_landmarks import calculate_distance

ONE_FRAME_SEC = 0.033
second_start_point_max = (0,0)

def distance(reference_clip, clip):
    # ref_frames = np.array([frame for frame in reference_clip.iter_frames()]) / 255.0
    # frames = np.array([frame for frame in clip.iter_frames()]) / 255.0
    min_diff, min_idx, frist_length, first_degree, second_length, second_degree, first_start_point, second_start_point = calculate_distance(reference_clip, clip)
    
    return min_diff, min_idx, frist_length, first_degree, second_length, second_degree, first_start_point, second_start_point

def resize_func(t):
    if t < 3:
        return 1 + 0.5*t  # Zoom-in.
    elif 3 <= t <= 5:
        return 1 + 0.5*3  # Stay.
    else: # 5 < t
        return 1  # Zoom-out.

def scroll(get_frame, t):
    """
    This function returns a 'region' of the current frame.
    The position of this region depends on the time.
    """
    
    frame = get_frame(t)
    print(frame.shape)
    print(t)
    calced_width = int((720-int(t*50))*1280 /720) # 비율 맞춰서 자르기
    
    frame_region = frame[int(t*50):720,:calced_width]
    # frame_region = frame.crop(x1=1.5,y1=110,x2=400,y2=810)
    return frame_region

class Moving:
    def __init__(self,second_start_point):
        self.second_start_point = second_start_point
    def __call__(self, get_frame, t):
        # any process you want
        frame = get_frame(t)
        if len(self.second_start_point)==0:
            print('---------------------')
            return frame
        else:
            # 얘를 center로 만들어서 줄여버리자!!
            cur_w = self.second_start_point[0]
            cur_h = self.second_start_point[1]
            print(cur_w,cur_h)
            w_ratio = self.second_start_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
            h_ratio = self.second_start_point[1]/720 # 그 비율만큼 위쪽 마이너스
            width_dist = abs(int(cur_w - 640))
            height_dist = abs(int(cur_h - 360))
            print(w_ratio, h_ratio)
            # w1, w2 = int(cur_w - width_dist * w_ratio), int(cur_w + width_dist *(1-w_ratio)) ## 이걸 범위로 하면 안되네!!! 생각해보니까(dist 만큼만 잘라질거 아냐)
            # h1, h2 = int(cur_h - height_dist * h_ratio), int(cur_h + height_dist *(1-h_ratio))

            # 16:9 비율
            w1, w2 = int(cur_w - 1120 * w_ratio), int(cur_w + 1120 *(1-w_ratio))
            h1, h2 = int(cur_h - 630 * h_ratio), int(cur_h + 630 *(1-h_ratio))

            frame_region = frame[h1:h2,w1:w2]
            return frame_region


def moving(get_frame, t):
    print(t)
    ### 여기 함수는 다 만들어지고 나서 실행됨(그러므로 전역변수로 현재 position을 저장해도, 제일 마지막 position으로 전체가 돌아가는 문제가 생김)
    ### dict 로 만들어서 저장해야할듯!
    frame = get_frame(t)
    if len(second_start_point)==0:
        print('---------------------')
        calced_width = int((720-int(t*50))*1280 /720) # 비율 맞춰서 자르기
    
        frame_region = frame[int(t*50):720,:calced_width]
        return frame_region
    else:
        # 얘를 center로 만들어서 줄여버리자!!
        cur_w = second_start_point[0]
        cur_h = second_start_point[1]
        print(cur_w,cur_h)
        w_ratio = second_start_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
        h_ratio = second_start_point[1]/720 # 그 비율만큼 위쪽 마이너스
        width_dist = abs(int(cur_w - 640))
        height_dist = abs(int(cur_h - 360))
        w1, w2 = int(cur_w - width_dist * w_ratio), int(cur_w + width_dist *(1-w_ratio))
        h1, h2 = int(cur_h - height_dist * h_ratio), int(cur_h + height_dist *(1-h_ratio))

        cur_w = 350
        cur_h = 132
        w1, w2 = int(cur_w - 640 * w_ratio), int(cur_w + 640 *(1-w_ratio))
        h1, h2 = int(cur_h - 360 * h_ratio), int(cur_h + 360 *(1-h_ratio))

        # w1, w2 = max(int(cur_w - 368),0), min(int(cur_w + 640),1280)
        # h1, h2 = max(int(cur_h - 180),0), min(int(cur_h + 180),720)

        frame_region = frame[h1:h2,w1:w2]
        return frame_region
    

def moving2(get_frame, t):
    """
    This function returns a 'region' of the current frame.
    The position of this region depends on the time.
    """
    frame = get_frame(t)
    if len(second_start_point)==0:
        print('---------------------')
        return frame
    else:
        # print(second_start_point)
        # print(second_start_point[0],second_start_point[1])
        cur_w = second_start_point[0]
        cur_h = second_start_point[1]
        width_dist = abs(int(cur_w - 500))
        height_dist = abs(int(cur_h - 250))
        print(height_dist, width_dist)
        dir = 0
        # 왼쪽 위 1, 오른쪽 위 2, 오른쪽 아래 3, 왼쪽 아래 4
        # 지금 상태에선 4초만에 이동?
        # fps = 29.9700299700299 frame/sec -> 1 frame = 0.033sec
        # 크기 줄일 땐 반대편을 줄여야 함
        one_frame_speed_w= height_dist/4/0.033
        one_frame_speed_h = width_dist/4/0.033
        # 줄고 0에서 시작, 늘고 끝애서 빼면서 시작
        if cur_w > 500 and cur_h > 250:
            dir = 3 # width 줄고 height 늘고
            frame_region = frame[max(height_dist, int(t*one_frame_speed_h)):,:max(1280-width_dist,1280-int(t*one_frame_speed_w))]
        elif cur_w < 500 and cur_h > 250:
            dir = 4 # width 늘고 height 늘고
            frame_region = frame[:max(720-height_dist, 720-int(t*one_frame_speed_h)),:max(1280-width_dist,1280-int(t*one_frame_speed_w))]
        elif cur_w > 500 and cur_h < 250:
            dir = 2 # width 늘고 height 줄고
            frame_region = frame[:max(720-height_dist, 720-int(t*one_frame_speed_h)),max(width_dist,int(t*one_frame_speed_w)):]
        elif cur_w < 500 and cur_h < 250:
            dir = 1 # width 줄고 height 줄고
            frame_region = frame[max(height_dist, int(t*one_frame_speed_h)):,max(width_dist,int(t*one_frame_speed_w)):]
        print('dir----'+str(dir))
        # calced_height = int()
        # 4 frame안에 이동해야 한다고 생각하자!
        # calced_width = int((720-int(t*50))*1280 /720) # 비율 맞춰서 자르기
        # frame_region = frame[height_dist:,width_dist:]
        
        # frame_region = frame.crop(x1=1.5,y1=110,x2=400,y2=810)
        return frame_region

def crosscut(videos_path="./video", option="random"):
    global second_start_point 
    global second_start_point
    min_time = 1000.0
    min_idx = 0
    audioclip = None
    extracted_clips_array = []
    #                0  1  2  3  4  5   6  7  8  9  10
    # start_times = [0, 4, 4, 0, 0, 1, 14, 0, 0, 0, 0]
    # VIDEO SONG START TIME ARRAY
    start_times = [0.3, 1, 0] # 노래 개수
    # start_times = [0,0,5] # 노래 개수

    # VIDEO ALIGNMENT -> SLICE START TIME
    for i in range(len(os.listdir(videos_path))):
        video_path = os.path.join(videos_path, sorted(os.listdir(videos_path))[i])
        clip = VideoFileClip(video_path)
        clip = clip.subclip(start_times[i], clip.duration) # 그냥 전체 영상을 시작점 맞게 자르기
        print(video_path, clip.fps, clip.duration)
        if min_time > clip.duration: # ?? 제일 작은거 기준으로 자르려는건가?? 근데 그러면 그 앞에건 이미 크지않나??
            audioclip = clip.audio
            min_time = clip.duration
            min_idx = i
            print(video_path, clip.fps, clip.duration)
        extracted_clips_array.append(clip)
    print(len(extracted_clips_array))

    con_clips = []
    t = 0
    current_idx = 0
    window_time = 10
    padded_time = 3 # 얼굴이 클로즈업 된게 있으면 계속 클로즈업 된 부분만 찾으므로 3초정도 띄어준다.
    # GENERATE STAGEMIX
    # CONCAT SUBCLIP 0~ MIN DURATION CLIP TIME
    while t <= int(min_time):
        # 10 sec.
        cur_t = t
        next_t = min(t+window_time, min_time) # 마지막은 window초보다 작은초일수도 있으니
        next_frame =  min(t+window_time, min_time) # 제일 비슷한 영상을 못찾으면 그냥 window초 넘어갈수 있다

        # RANDOM BASED METHOD
        if option=="random":
            random_video_idx = random.randint(0, len(extracted_clips_array)-1)
            clip = extracted_clips_array[random_video_idx].subclip(cur_t, next_t)
        # 제일 마지막 영상은 그냥 원래 영상 붙이기
        elif min_time - cur_t < padded_time:
            clip = extracted_clips_array[min_idx].subclip(cur_t, min_time)
        else:
            # 지금 현재 영상!
            reference_clip = extracted_clips_array[current_idx].subclip(cur_t, next_t)
            d = 5000000
            # ! 같은 영상 나올수도 있는 문제
            min_idx = random.randint(0, len(extracted_clips_array)-1) # inf가 있을수도 있어서 random하게
            for video_idx in range(len(extracted_clips_array)):
                if video_idx == current_idx:
                    continue
                # 10초간 영상 확인
                clip = extracted_clips_array[video_idx].subclip(cur_t, next_t) 
                
                # 이미 확인한 앞부분은 무시해야 함!!(! 첫번째 영상은 3초는 무조건 안겹치는 문제 있음)
                # !! ㅜㅜ 제일 좋은 얼굴 부분 놓칠수도 있을듯!
                reference_clip_for_distance = reference_clip.subclip(padded_time, window_time)
                clip_for_distance = clip.subclip(padded_time, window_time)
                # CALCULATE DISTANCE between reference_clip_for_distance, clip_for_distance(같은초에서 최선의 거리 장면 찾기)
                cur_d, plus_frame, frist_length, first_degree, second_length, second_degree, first_start_point, second_start_point = distance(reference_clip_for_distance, clip_for_distance) 
                
                print(current_idx, video_idx, cur_d, cur_t + padded_time + plus_frame)
                print(frist_length, first_degree, second_length, second_degree)
                if d > cur_d:
                    d = cur_d
                    min_idx = video_idx
                    next_frame = cur_t + padded_time + plus_frame # 바로 옮길 frame
                    next_clip = clip.subclip(0, padded_time+ plus_frame) # 그 바꿀 부분만 자르는 클립!
                    second_start_point_max = second_start_point

            current_idx = min_idx
            print("idx : {}".format(current_idx))
            # 해당하는 길이만큼 자르기
            clip = next_clip

        # 여기서 편집하기
        if t>0:# 첫장면은 확대따윈 없다!
            clip_front = clip.subclip(0,ONE_FRAME_SEC*50) # 그 바꿀 부분만 자르는 클립!
            # clip_front = clip_front.fl(scroll)
            # clip_front = clip_front.resize((1280,720))
            con_clips.append(clip_front)
            clip_middle = clip.subclip(ONE_FRAME_SEC*50,-1*ONE_FRAME_SEC*50) # 그 바꿀 부분만 자르는 클립!
        else:
            clip_middle = clip.subclip(0,-1*ONE_FRAME_SEC*50) # 그 바꿀 부분만 자르는 클립!

        print(clip.duration,'0000000duration---------')
        clip_back = clip.subclip(clip.duration-(ONE_FRAME_SEC*50),clip.duration)
        # clip_back = clip_back.fl(moving)
        clip_back = clip_back.fl(Moving(second_start_point_max))
        clip_back = clip_back.resize((1280,720))
        t = next_frame
        con_clips.append(clip_middle)
        con_clips.append(clip_back)

    final_clip = concatenate_videoclips(con_clips)

    if audioclip !=None:
        print("Not None")
        final_clip.audio = audioclip

    final_clip.write_videofile("random.mp4")
    return final_clip

start_time = time.time()
crosscut(videos_path="./video", option="norandom")
end_time = time.time()

print(end_time - start_time)
# 그냥 1 frame으로 총 작업하는데 2688.1366200447083
# 4 frame  576.5337190628052
