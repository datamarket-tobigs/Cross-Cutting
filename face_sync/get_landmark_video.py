# import the necessary packages
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip
from imutils import face_utils
import imutils
import time
import dlib
import cv2
import numpy as np

# Landmarking on video & return gif(default)/video form
def landmarking_video(video_path, out_name, toVideo=False):

	# Load video
    video = VideoFileClip(video_path)

    # Load detector & landmarker
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    time.sleep(3.0)
    print("준비완료")

    # Landmarking
    output = []
    # for i in range(int(video.duration*video.fps)) :
    for i in range(50, 550) :
        if i % 50 == 0:
            print(str(i)+'번째 frame 찍는중...')
        # get a frame
        frame = video.get_frame(i / video.fps)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detect face
        rects = detector(gray, 0)
        if len(rects) > 0:
            # landmarking all face
            for rect in rects:
                shape = predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)
                (x, y, w, h) = face_utils.rect_to_bb(rect)
                # loop over the coordinates of facial landmark
                for (x,y) in shape:
                    cv2.circle(frame, (x,y), 2, (0,0,255), -1)
        
        # append a frame
        output.append(frame)
    print("모든 frame 처리 완료")

    # convert to video/gif
    clips = [ImageClip(m).set_duration(1/video.fps) for m in output]
    concat_clip = concatenate_videoclips(clips, method='compose')
    if toVideo:
        concat_clip.write_videofile(out_name, fps=video.fps)
    else:
        concat_clip.write_gif(out_name, fps=video.fps)
    print("생성 완료")
        



if __name__ == '__main__':

    path = 'video path'
    out_name = "output name"
    landmarking_video(path, out_name, False)

    print("Success landmarking video!")


