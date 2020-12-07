import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import random
import numpy as np
import time
# from video_facial_landmarks_minmax import calculate_distance
from video_pose_landmarks import calculate_pose_distance

TEST = True
TEST_TIME = 20
INIT_NUM = float("Inf")
WINDOW_TIME = 10
PADDED_TIME = 4 # 얼굴이 클로즈업 된게 있으면 계속 클로즈업 된 부분만 찾으므로 3초정도 띄어준다.

# def distance(reference_clip, clip):
#     min_diff, min_idx, additional_info = calculate_distance(reference_clip, clip)
    
#     return min_diff, min_idx

def pose_distance(reference_clip, clip):
    min_diff, min_idx, additional_info = calculate_pose_distance(reference_clip, clip)
    
    return min_diff, min_idx

def crosscut(videos_path="./video", option="random"):
    min_time = 1000.0
    min_idx = 0
    audioclip = None
    extracted_clips_array = []

    video_num = len(os.listdir(videos_path))
    start_times = [0] * video_num # VIDEO ALIGNMENT -> SLICE START TIME

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

    
    if TEST: # test하면 일부분만 생성해서 빠르게 확인하기
        min_time = TEST_TIME
        audioclip = audioclip.set_duration(TEST_TIME)

    # GENERATE STAGEMIX
    # CONCAT SUBCLIP 0~ MIN DURATION CLIP TIME
    con_clips = []
    t = 3 # 초반 3초 INIT
    current_idx = 0 # INIT
    con_clips.append(extracted_clips_array[current_idx].subclip(0, min(t, int(min_time))))

    while t < min_time:
        # 10 sec.
        cur_t = t
        next_t = min(t+WINDOW_TIME, min_time) # 마지막은 window초보다 작은초일수도 있으니

        # RANDOM BASED METHOD
        if option=="random" or min(min_time,t + PADDED_TIME)==min_time:
            random_video_idx = random.randint(0, len(extracted_clips_array)-1)
            clip = extracted_clips_array[random_video_idx].subclip(cur_t, next_t)
            t = next_t
            con_clips.append(clip)
        else:
            # 지금 현재 영상!
            reference_clip = extracted_clips_array[current_idx].subclip(cur_t, next_t)
            d = INIT_NUM
            cur_clip = None
            # inf가 있을때는 이 idx로 설정됨!
            min_idx = (current_idx+1)%len(extracted_clips_array) 
            for video_idx in range(len(extracted_clips_array)):
                if video_idx == current_idx:
                    continue
                # 10초간 영상 확인
                clip = extracted_clips_array[video_idx].subclip(cur_t, next_t) 
                
                # 이미 확인한 앞부분은 무시해야 함!!(! 첫번째 영상은 3초는 무조건 안겹치는 문제 있음)
                # !! ㅜㅜ 제일 좋은 얼굴 부분 놓칠수도 있을듯!
                # CALCULATE DISTANCE
                cur_d, plus_frame = pose_distance(reference_clip, clip) 
                print(current_idx, video_idx, cur_d, cur_t + plus_frame)
                if d > cur_d:
                    d = cur_d
                    min_idx = video_idx
                    next_t = cur_t + plus_frame # 바로 옮길 frame
                    cur_clip = reference_clip.subclip(0, plus_frame)
                    # next_clip = clip.subclip(0, plus_frame) # 그 바꿀 부분만 자르는 클립!

            # 이번 clip : 10초 내에서 자르거나 10초 full append
            if cur_clip: # 계산이 가능하면
                clip = cur_clip # 현재 클립(바꾸면 가장 좋은 부분까지 잘린 현재 클립)
            else:
                clip = reference_clip # 현재 클립 10초 모두
            t = next_t
            con_clips.append(clip)

            # 다음 clip : padding 길이는 반드시 append
            # 뒤에 padding 데이터 더하기
            current_idx = min_idx # 바로 다음에 이어지면 가까운 거리로 연결되는 데이터
            print("idx : {}".format(current_idx))
            pad_clip = extracted_clips_array[current_idx].subclip(t, min(min_time,t+PADDED_TIME)) # min_time을 넘어가면 안됨!
            t = min(min_time,t + PADDED_TIME) # padding 된 시간 더하기
            con_clips.append(pad_clip)
            
    final_clip = concatenate_videoclips(con_clips)

    if audioclip !=None:
        print("Not None")
        final_clip.audio = audioclip

    final_clip.write_videofile("crosscut_fiesta.mp4")
    return final_clip

start_time = time.time()
crosscut(videos_path="./video", option="norandom")

end_time = time.time()

print(end_time - start_time)
