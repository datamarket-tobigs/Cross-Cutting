import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
import random
import numpy as np
import time
from video_facial_landmarks import calculate_distance

ONE_FRAME_SEC = 0.033
EYE_MIN_DIFF = 40 # 워워워~ 예에에
WINDOW_TIME = 10
PADDED_TIME = 3 # 얼굴이 클로즈업 된게 있으면 계속 클로즈업 된 부분만 찾으므로 3초정도 띄어준다.
ZOOM_FRAME =30 # 얼굴 확대할때  시간
CROSS_FRAME = 5 #얼굴 스르르 시간

# init
second_start_point_max = (0,0)
first_start_point_max = (0,0)
first_length_max = 0
second_length_max = 0
first_degree_max = 0
second_degree_max = 0

def distance(reference_clip, clip):
    # ref_frames = np.array([frame for frame in reference_clip.iter_frames()]) / 255.0
    # frames = np.array([frame for frame in clip.iter_frames()]) / 255.0
    min_diff, min_idx, refer_length, refer_degree, compare_length, compare_degree, refer_point, compare_point = calculate_distance(reference_clip, clip)
    
    return min_diff, min_idx, refer_length, refer_degree, compare_length, compare_degree, refer_point, compare_point

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
    def __init__(self,center_point, ratio, transition_dir):
        self.center_point = center_point
        self.ratio = ratio
        self.transition_dir = transition_dir
    def __call__(self, get_frame, t):
        # any process you want
        frame = get_frame(t)
        if len(self.center_point)==0:
            # print('---------------------')
            return frame
        else:
            # 얘를 center로 만들어서 줄여버리자!!
            cur_w = self.center_point[0]
            cur_h = self.center_point[1]
            # print(cur_w,cur_h)
            w_ratio = self.center_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
            h_ratio = self.center_point[1]/720 # 그 비율만큼 위쪽 마이너스
            width_dist = abs(int(cur_w - 640))
            height_dist = abs(int(cur_h - 360))
            # print(w_ratio, h_ratio)
            # w1, w2 = int(cur_w - width_dist * w_ratio), int(cur_w + width_dist *(1-w_ratio)) ## 이걸 범위로 하면 안되네!!! 생각해보니까(dist 만큼만 잘라질거 아냐)
            # h1, h2 = int(cur_h - height_dist * h_ratio), int(cur_h + height_dist *(1-h_ratio))

            # 시간초에 따라서 바뀌어야 함!
            if self.transition_dir == 'small_to_big':
                W_real = 1280 - (1280 - 1280 * self.ratio)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                H_real = 720 - (720 - 720 * self.ratio)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
            else:
                W_real = 1280 - (1280 - 1280 * self.ratio)*(ZOOM_FRAME - t/ONE_FRAME_SEC)/ZOOM_FRAME
                H_real = 720 - (720 - 720 * self.ratio)*(ZOOM_FRAME - t/ONE_FRAME_SEC)/ZOOM_FRAME

            # 16:9 비율
            w1, w2 = int(cur_w - W_real * w_ratio), int(cur_w + W_real *(1-w_ratio))
            h1, h2 = int(cur_h - H_real * h_ratio), int(cur_h + H_real *(1-h_ratio))

            frame_region = frame[h1:h2,w1:w2]
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
    check_tqdm = 1
    # GENERATE STAGEMIX
    # CONCAT SUBCLIP 0~ MIN DURATION CLIP TIME
    while t <= int(min_time):
        print(check_tqdm,'------------------------------------------------------------------')
        check_tqdm += 1
        # 10 sec.
        cur_t = t
        next_t = min(t+WINDOW_TIME, min_time) # 마지막은 window초보다 작은초일수도 있으니
        next_frame =  min(t+WINDOW_TIME, min_time) # 제일 비슷한 영상을 못찾으면 그냥 window초 넘어갈수 있다

        # RANDOM BASED METHOD
        if option=="random":
            random_video_idx = random.randint(0, len(extracted_clips_array)-1)
            clip = extracted_clips_array[random_video_idx].subclip(cur_t, next_t)
            t = next_frame
            con_clips.append(clip)
        else:
            # 지금 현재 영상!
            reference_clip = extracted_clips_array[current_idx].subclip(cur_t, next_t)
            d = 5000000
            # inf가 있을때는 이 idx로 설정됨!
            min_idx = (current_idx+1)%len(extracted_clips_array) 
            for video_idx in range(len(extracted_clips_array)):
                # 같은 영상 나올수도 있는 문제 해결
                if video_idx == current_idx:
                    continue
                # 10초간 영상 확인
                clip = extracted_clips_array[video_idx].subclip(cur_t, next_t) 
                
                # 이미 확인한 앞부분은 무시해야 함!!(! 첫번째 영상은 3초는 무조건 안겹치는 문제 있음)
                # !! ㅜㅜ 제일 좋은 얼굴 부분 놓칠수도 있을듯!
                # reference_clip_for_distance = reference_clip.subclip(PADDED_TIME, WINDOW_TIME)
                # clip_for_distance = clip.subclip(PADDED_TIME, WINDOW_TIME)
                # CALCULATE DISTANCE between reference_clip_for_distance, clip_for_distance(같은초에서 최선의 거리 장면 찾기)
                cur_d, plus_frame, frist_length, first_degree, second_length, second_degree, first_start_point, second_start_point = distance(reference_clip, clip) 
                print('from video:',current_idx, ' to video',video_idx, ' in distance ',cur_d, ' in sec ' ,cur_t + plus_frame)
                # print(frist_length, first_degree, second_length, second_degree)
                if d > cur_d:
                    d = cur_d
                    min_idx = video_idx
                    next_frame = cur_t + plus_frame # 바로 옮길 frame
                    cur_clip = reference_clip.subclip(0,plus_frame)
                    next_clip = clip.subclip(0, plus_frame) # 그 바꿀 부분만 자르는 클립!
                    second_start_point_max = second_start_point
                    first_start_point_max = first_start_point
                    first_length_max = frist_length # 이거에 맞춰서 확대 축소 해줄거야!
                    second_length_max = second_length # 이거에 맞춰 확대 축소 해줄거야!
                    first_degree_max = first_degree
                    second_degree_max = second_degree
            
            if d == 5000000: # 둘다 inf일떄,
                current_idx = min_idx # 바로 다음에 이어지면 가까운 거리로 연결되는 데이터
                clip = cur_clip # 현재 클립(바꾸면 가장 좋은 부분까지 잘린 현재 클립)
                t = next_frame
                con_clips.append(clip)
                # 뒤에 padding 데이터 더하기
                pad_clip = extracted_clips_array[current_idx].subclip(t, min(min_time,t+PADDED_TIME)) # min_time을 넘어가면 안됨!
                t = min(min_time,t + PADDED_TIME) # padding 된 시간 더하기
                con_clips.append(pad_clip)
            else:
                # (!! 현재 영상을 concat 하고 다음에 넣을 영상 idx를 저장해야 한다!)
                prev_idx = current_idx
                current_idx = min_idx # 바로 다음에 이어지면 가까운 거리로 연결되는 데이터
                print("next video idx : {}".format(current_idx))
                print(first_length_max, second_length_max, '----length max')
                clip = cur_clip # 현재 클립(바꾸면 가장 좋은 부분까지 잘린 현재 클립)
                # clip = next_clip ## 이건 직관적이지 않고 틀림 ㅜㅜ

                # 여기서 편집하기 -----------------------------------
                t = next_frame
                # 앞에 부분 자르기!(뒤 transition 제외)
                clip_front = clip.subclip(0,clip.duration-(ONE_FRAME_SEC*ZOOM_FRAME)) # 그 바꿀 부분만 자르는 클립!
                con_clips.append(clip_front)
                # # 뒤에 transition 부분 붙이기
                ### !! 너무 padding 이 마이너스로 되어있으면 그 이전 영상을 찾아서 넣나봄!!(그래서 툭툭 끊김) 그러므로 너무 크게 빼도 안되겠네
                clip_back = clip.subclip(clip.duration-(ONE_FRAME_SEC*ZOOM_FRAME),clip.duration)
                print(first_start_point_max, second_start_point_max,'----start point')
                ## resize
                if abs(second_length_max-first_length_max) < EYE_MIN_DIFF:
                    if second_length_max> second_length_max and second_length_max-first_length_max < EYE_MIN_DIFF:
                        clip_back = clip_back.fl(Moving(first_start_point_max,first_length_max/second_length_max,'small_to_big'))
                        clip_back = clip_back.resize((1280,720))
                    
                    # 거리가 적당히 작으면 cross fadein(앞에서 붙여줘야 자연스럽지!)
                    clip_back_not_fade = clip_back.subclip(0,clip_back.duration-ONE_FRAME_SEC*CROSS_FRAME)
                    clip_back_fade= clip_back.subclip(clip_back.duration-ONE_FRAME_SEC*CROSS_FRAME, clip_back.duration)
                    cross_clip = extracted_clips_array[current_idx].subclip(t-ONE_FRAME_SEC*CROSS_FRAME, t) # min_time을 넘어가면 안됨!
                    
                    clip_back_fade = CompositeVideoClip([clip_back_fade, cross_clip.crossfadein(ONE_FRAME_SEC*CROSS_FRAME)])
                    con_clips.append(clip_back_not_fade)
                    con_clips.append(clip_back_fade)
                else:
                    con_clips.append(clip_back)
                
                # con_clips.append(clip)
            
                # 뒤에 padding 데이터 더하기 -----------------------------
                pad_clip = extracted_clips_array[current_idx].subclip(t, min(min_time,t + PADDED_TIME)) # min_time을 넘어가면 안됨!
                pad_front = pad_clip.subclip(0,ONE_FRAME_SEC*ZOOM_FRAME) # 그 바꿀 부분만 자르는 클립!
                # 내가 작다면 내가 따라간다!
                if first_length_max> second_length_max and first_length_max-second_length_max < EYE_MIN_DIFF:
                    # 더 작아져야하쥐!(결국 확대?)
                    pad_front = pad_front.fl(Moving(second_start_point_max,second_length_max/first_length_max, 'big_to_small'))
                    pad_front = pad_front.resize((1280,720))
                    print('yooooooo')
                    # cross_clip = extracted_clips_array[prev_idx].subclip(t, t+ONE_FRAME_SEC*30) # min_time을 넘어가면 안됨!
                    # pad_front = CompositeVideoClip([clip_back, pad_front.crossfadein(ONE_FRAME_SEC*30)])
                con_clips.append(pad_front)
                pad_back = pad_clip.subclip(ONE_FRAME_SEC*ZOOM_FRAME,pad_clip.duration) # 그 바꿀 부분만 자르는 클립!
                t = min(min_time, t + PADDED_TIME) # padding 된 시간 더하기
                con_clips.append(pad_back)

    final_clip = concatenate_videoclips(con_clips)

    if audioclip !=None:
        final_clip.audio = audioclip

    final_clip.write_videofile("random.mp4")
    return final_clip

start_time = time.time()
crosscut(videos_path="./video", option="norandom")
end_time = time.time()

print(end_time - start_time, 'total Generation time')
# 그냥 1 frame으로 총 작업하는데 2688.1366200447083
# 4 frame  576.5337190628052