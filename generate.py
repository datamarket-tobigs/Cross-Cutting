import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import random
import numpy as np
import time

def distance(reference_clip, clip):
    ref_frames = np.array([frame for frame in reference_clip.iter_frames()]) / 255.0
    frames = np.array([frame for frame in clip.iter_frames()]) / 255.0
    print(frames.shape)
    return np.mean(np.abs(ref_frames - frames))

def crosscut(videos_path="./video", option="random"):
    min_time = 1000.0
    audioclip = None
    extracted_clips_array = []
    #                0  1  2  3  4  5   6  7  8  9  10
    # start_times = [0, 4, 4, 0, 0, 1, 14, 0, 0, 0, 0]
    # VIDEO SONG START TIME ARRAY
    start_times = [0, 0, 5, 7.92, 0, 0]

    # VIDEO ALIGNMENT -> SLICE START TIME
    for i in range(len(os.listdir(videos_path))):
        video_path = os.path.join(videos_path, sorted(os.listdir(videos_path))[i])
        clip = VideoFileClip(video_path)
        clip = clip.subclip(start_times[i], clip.duration)
        if min_time > clip.duration:
            audioclip = clip.audio
            min_time = clip.duration
            print(video_path, clip.fps, clip.duration)
        extracted_clips_array.append(clip)
    print(len(extracted_clips_array))

    con_clips = []
    t = 0
    current_idx = 0

    # GENERATE STAGEMIX
    # CONCAT SUBCLIP 0~ MIN DURATION CLIP TIME
    while t <= int(min_time):
        # 10 sec.
        cur_t = t
        next_t = min(t+10, min_time)

        # RANDOM BASED METHOD
        if option=="random":
            random_video_idx = random.randint(0, len(extracted_clips_array)-1)
            clip = extracted_clips_array[random_video_idx].subclip(cur_t, next_t)
        # DISTANCE BASED METHOD
        else:
            reference_clip = extracted_clips_array[current_idx].subclip(cur_t, next_t)
            d = 5000000
            min_idx = 0
            for video_idx in range(len(extracted_clips_array)):
                if video_idx == current_idx:
                    continue
                clip = extracted_clips_array[video_idx].subclip(cur_t, next_t)
                # CALCULATE DISTANCE
                cur_d = distance(reference_clip, clip)
                print(current_idx, video_idx, cur_d)
                if d > cur_d:
                    d = cur_d
                    next_clip = clip
                    min_idx = video_idx
            # next_clip.write_videofile(str(t)+".mp4")
            current_idx = min_idx
            print("idx : {}".format(current_idx))
            clip = next_clip

        t = next_t
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