import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import numpy as np

class generate_pose_detection():

    def __init__(self, edit_point_list, edit_video_list):
        self.video_dir = "../video/"
        self.video_list = sorted(os.listdir(self.video_dir)) ## write video dir here!
        self.edit_time = edit_point_list
        self.selected_video = edit_video_list
        self.subclip_list = []

    def generate_mixed_video(self):
        start_time = 0
        video_idx = 0

        for i in range(len(self.edit_time)):
            self.subclip_list.append(VideoFileClip(self.video_dir + self.video_list[video_idx]).subclip(start_time, start_time + self.edit_time[i]))
            self.subclip_list.append(VideoFileClip(self.video_dir + self.video_list[self.selected_video[i]]).subclip(start_time + self.edit_time[i], start_time + 10))
            video_idx = self.selected_video[i]
            start_time += 10

        final_clip = concatenate_videoclips(self.subclip_list)
        final_clip.write_videofile("pose_detection_mixed_video.mp4")


result = [[6, 1],
          [6, 0],
          [3, 2],
          [1, 0],
          [1, 1],
          [8, 0],
          [0, 1],
          [6, 0],
          [7, 1],
          [6, 3]]

time_list = list(np.array(result)[:, 0])
video_list = list(np.array(result)[:, 1])

generate = generate_pose_detection(time_list, video_list)
generate.generate_mixed_video()
# print(generate.video_list[video_list[0]])