import numpy as np
from fastRCNN_model import fast_RCNN_model

class make_edit_point():

    def __init__(self, start_video):
        self.img_dir = "../img/"
        self.subclip_dir = [str(i * 10) + "-" + str((i + 1) * 10) + "/" for i in range(23)]
        self.video_num = [str(i) + " video " for i in [0, 1, 4, 5]]
        self.frame_num = [str(i * 30) + ".png" for i in range(9)]
        self.model = fast_RCNN_model()
        self.next_start = start_video
        self.result = []

    def calculate_time_video(self):
        for period in self.subclip_dir:
            video_point = []
            start = self.next_start
            for f_num in self.frame_num:
                per_frame = []
                for v_num in self.video_num[:4]:
                    file_name = self.img_dir + period + v_num + f_num
                    # print(file_name)
                    self.model.write_file_name(file_name=file_name)
                    box_id, box_score, box_val = self.model.run_model()
                    point = np.sum(box_val) / 6000
                    per_frame.append(point.asnumpy()[0])
                video_point.append(per_frame)

            frame_similarity = []
            for i in range(len(video_point)):
                temp = []
                for j in range(len(video_point[i])):
                    if j != start:
                        temp.append(abs(video_point[i][start] - video_point[i][j]))
                    ## 자기 자신은 비교하지 않기 위해서 100 추가.
                    else:
                        temp.append(100)
                frame_similarity.append(temp)

            edit_point = frame_similarity.index(min(frame_similarity))
            next_video = frame_similarity[edit_point].index(min(frame_similarity[edit_point]))
            self.next_start = next_video
            # print("edit point: " + str(edit_point))
            # print("next_video: " + str(next_start))
            # print("____")
            r = [edit_point, next_video]
            self.result.append(r)

    def return_result(self):
        return self.result
