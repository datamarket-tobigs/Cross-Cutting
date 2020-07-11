import os
from moviepy.editor import VideoFileClip

class generate_subclips():
    def __init__(self):
        self.start_times = [13.0, 1.5, 0.5, 0.5, 1.0, 0.5, 1.0, 6.5, 0, 0.5]
        self.min_time = 1000.0
        self.extracted_clips_array = []

    def edit_video_sink(self, videos_path):
        audioclip = None
        #                0  1  2  3  4  5   6  7  8  9  10
        # VIDEO SONG START TIME ARRAY
        # VIDEO ALIGNMENT -> SLICE START TIME

        for i in range(len(os.listdir(videos_path))):
            video_path = os.path.join(videos_path, sorted(os.listdir(videos_path))[i])
            clip = VideoFileClip(video_path)
            clip = clip.subclip(self.start_times[i], clip.duration)
            self.extracted_clips_array.append(clip)
        # print(len(extracted_clips_array))


    def make_subclips(self):
        for i in range(6):
            os.mkdir("subclips/" + str(i * 10))

        for video_idx in range(len(self.extracted_clips_array)):
            print("make subclip...")
            t = 0
            while t <= 60:
                # 10 sec.
                cur_t = t
                next_t = min(t + 10, self.min_time)

                clip = self.extracted_clips_array[video_idx].subclip(cur_t, next_t)
                # clip.write_videofile("subclips/" + str(video_idx * 10) + "/" + str(t) + " " + str(video_idx) + ".mp4")
                t = next_t

    def get_extracted_clip_list(self):
        return self.extracted_clips_array
