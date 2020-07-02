from moviepy.editor import *
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import random

def random_crosscut(videos_path="./video", content_name="ohmygirl", videotype=".mp4"):
    clips_array = []
    min_time = 1000.0
    audioclip = None
    for i in range(len(os.listdir(videos_path))):
        video_path = os.path.join(videos_path, content_name+str(i+1)+videotype)
        clip = VideoFileClip(video_path)
        clips_array.append(clip)
        if min_time > clip.duration:
            audioclip = clip.audio
            min_time = clip.duration
    extracted_clips_array = []
    for clip in clips_array:
        clip = clip.subclip(clip.duration - min_time, clip.duration)
        extracted_clips_array.append(clip)
        print(clip.duration)

    con_clips = []
    t = 0
    while t <= int(min_time):
        cur_t = t
        next_t = min(t + random.randint(3, 9), min_time)
        random_video_idx = random.randint(0, len(extracted_clips_array)-1)
        clip = extracted_clips_array[random_video_idx].subclip(cur_t, next_t)
        # clip.write_videofile(str(cur_t)+".mp4")
        t = next_t
        con_clips.append(clip)
    final_clip = concatenate_videoclips(con_clips)
    if audioclip !=None:
        print("None")
        # final_clip.set_audio(audioclip=audioclip)
    final_clip.write_videofile("random.mp4")

    return final_clip

random_crosscut(videos_path="./video", content_name="ohmygirl")