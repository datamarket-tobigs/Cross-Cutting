# import the necessary packages
from moviepy.editor import VideoFileClip
import time
import os

# 프레임당 이미지로 저장
def video_to_image(video_path, save_dir, out_name):

	# Load video
    video = VideoFileClip(video_path)

    time.sleep(4)

    # Save frame as image
    for i in range(int(video.duration*video.fps)):
        temp_name = os.path.join(save_dir, out_name)
        temp_name += '_' + str(i) + '.jpeg'
        video.save_frame(temp_name, i/video.fps)
        if i % 50 == 0:
            print(str(i)+'번째 frame 저장중...')

    print('모든 프레임 저장 완료')
    
    return True



if __name__ == '__main__':

    video_path = './fifth_season9/fifth_season_landmark.mp4'
    save_dir = './fifth_season9'
    out_name = 'landmark_img'
    video_to_image(video_path, save_dir, out_name)
