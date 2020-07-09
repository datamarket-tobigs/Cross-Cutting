import os
from moviepy.editor import VideoFileClip
import numpy as np
import time


def distance(reference_clip, clip):
    ref_frames = np.array([frame for frame in reference_clip.iter_frames()]) / 255.0
    frames = np.array([frame for frame in clip.iter_frames()]) / 255.0
    print(frames.shape)
    return np.mean(np.abs(ref_frames - frames))


def crosscut(videos_path="./video"):
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

    for video_idx in range(len(extracted_clips_array)):
        t = 0
        while t <= int(min_time):
            # 10 sec.
            cur_t = t
            next_t = min(t + 10, min_time)

            clip = extracted_clips_array[video_idx].subclip(cur_t, next_t)
            clip.write_videofile(str(t) + " " + str(video_idx) + ".mp4")
            t = next_t


start_time = time.time()
crosscut(videos_path="./video")
end_time = time.time()

print(end_time - start_time)