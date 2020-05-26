import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import random
import numpy as np
import time
from video_facial_landmarks import calculate_distance

def distance(reference_clip, clip):
    # ref_frames = np.array([frame for frame in reference_clip.iter_frames()]) / 255.0
    # frames = np.array([frame for frame in clip.iter_frames()]) / 255.0
    min_diff, min_idx = calculate_distance(reference_clip, clip)
    
    return min_diff, min_idx

def crosscut(videos_path="./video", option="random"):
    min_time = 1000.0
    audioclip = None
    extracted_clips_array = []
    #                0  1  2  3  4  5   6  7  8  9  10
    # start_times = [0, 4, 4, 0, 0, 1, 14, 0, 0, 0, 0]
    # VIDEO SONG START TIME ARRAY
    start_times = [0.5, 0.7, 0] # 노래 개수
    # start_times = [0,0,5] # 노래 개수

    # VIDEO ALIGNMENT -> SLICE START TIME
    for i in range(len(os.listdir(videos_path))):
        video_path = os.path.join(videos_path, sorted(os.listdir(videos_path))[i])
        print(video_path)
        clip = VideoFileClip(video_path)
        clip = clip.subclip(start_times[i], clip.duration) # 그냥 전체 영상을 시작점 맞게 자르기
        print(video_path, clip.fps, clip.duration)
        if min_time > clip.duration: # ?? 제일 작은거 기준으로 자르려는건가?? 근데 그러면 그 앞에건 이미 크지않나??
            audioclip = clip.audio
            min_time = clip.duration
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
        if option=="random" or next_t - cur_t <padded_time:
            random_video_idx = random.randint(0, len(extracted_clips_array)-1)
            clip = extracted_clips_array[random_video_idx].subclip(cur_t, next_t)
        # DISTANCE BASED METHOD
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
                # CALCULATE DISTANCE
                cur_d, plus_frame = distance(reference_clip_for_distance, clip_for_distance) 
                print(current_idx, video_idx, cur_d, cur_t + padded_time + plus_frame)
                if d > cur_d:
                    d = cur_d
                    min_idx = video_idx
                    next_frame = cur_t + padded_time + plus_frame # 바로 옮길 frame
                    next_clip = clip.subclip(0, padded_time+ plus_frame) # 그 바꿀 부분만 자르는 클립!
            # next_clip.write_videofile(str(t)+".mp4")
            current_idx = min_idx
            print("idx : {}".format(current_idx))
            # 해당하는 길이만큼 자르기
            clip = next_clip

        t = next_frame
        con_clips.append(clip)

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
