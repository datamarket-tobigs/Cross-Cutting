import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import numpy as np
# from video_to_img import *
from generate_subclips_all import generate_subclips

class generate_pose_detection():

    def __init__(self):
        self.video_dir = "../video/"
        self.video_list = []
        self.edit_time = []
        self.selected_video = []
        self.subclip_list = []
        self.subclip_model = generate_subclips()
        self.full_video_list = []
        self.start_times = start_times = [13.0, 1.5, 0.5, 0.5, 1.0, 0.5, 1.0, 6.5, 0, 0.5] ## 시작 시간

    def generate_subclips(self, video_dir):
        self.subclip_model.crosscut("../video") ## 영상 경로 넣기

    def write_edit_time_and_video(self, edit_point_list, edit_video_list):
        self.edit_time = edit_point_list
        self.selected_video = edit_video_list

    def make_full_video(self):
        self.subclip_model.edit_video_sink(self.video_dir)
        self.full_video_list = self.subclip_model.get_extracted_clip_list()

    def generate_mixed_video(self):
        start_time = 0
        video_idx = 0

        for i in range(len(self.edit_time)):
            self.subclip_list.append(self.full_video_list[video_idx].subclip(start_time, start_time + self.edit_time[i]))
            self.subclip_list.append(self.full_video_list[self.selected_video[i]].subclip(start_time + self.edit_time[i], start_time + 10))
            video_idx = self.selected_video[i]
            start_time += 10

        final_clip = concatenate_videoclips(self.subclip_list)
        final_clip.write_videofile("pose_detection_mixed_video.mp4")

    def run(self):
        self.make_full_video()
        # print(type(self.full_video_list[0]))
        result = [[2, 2],
                  [1, 1],
                  [7, 2],
                  [1, 1],
                  [2, 5],
                  [0, 9]]

        time_list = list(np.array(result)[:, 0])
        video_list = list(np.array(result)[:, 1])

        self.write_edit_time_and_video(time_list, video_list)
        self.generate_mixed_video()


if __name__ == "__main__":
    pose_detection = generate_pose_detection()
    pose_detection.run()