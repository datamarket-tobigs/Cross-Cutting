#%%
# USAGE
# python video_facial_landmarks.py --shape-predictor shape_predictor_68_face_landmarks.dat
# python video_facial_landmarks.py --shape-predictor shape_predictor_68_face_landmarks.dat --picamera 1

# 전체 참고 
# https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/

# import the necessary packages
from imutils.video import VideoStream
from moviepy.editor import VideoFileClip
from imutils import face_utils
import datetime
import argparse
import imutils
import time
import dlib
import cv2
import numpy as np

def calculate_distance(reference_clip, compare_clip):
	# construct the `argument parse and parse the arguments
	# ap = argparse.ArgumentParser()
	# ap.add_argument("-p", "--shape-predictor", required=True, default = "shape_predictor_68_face_landmarks.dat",
	# 	help="path to facial landmark predictor")
	# ap.add_argument("-r", "--picamera", type=int, default=-1,
	# 	help="whether or not the Raspberry Pi camera should be used")
	# args = vars(ap.parse_args())
	
	# initialize dlib's face detector (HOG-based) and then create
	# the facial landmark predictor
	print("[INFO] loading facial landmark predictor...")
	# 얼굴 자체를 인식하는 기능
	detector = dlib.get_frontal_face_detector()
	# face 안에 얼굴 인식하는 기능

	predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
	# predictor = dlib.shape_predictor(args["shape_predictor"])

	# vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
	# 비디오 출력 : https://076923.github.io/posts/Python-opencv-4/
	# https://docs.opencv.org/master/dd/d43/tutorial_py_video_display.html
	# capture = cv2.VideoCapture("cut_2.mp4")
	clips =[reference_clip,compare_clip]

	time.sleep(2.0)

	clips_frame_info = []
	for clip in clips:
		i=0
		every_frame_info= []
		# loop over the frames from the video stream
		while True:
			# grab the frame from the threaded video stream, resize it to
			# have a maximum width of 400 pixels, and convert it to
			# ret, frame = capture.read() # frame = numpy array임
			frame = clip.get_frame(i*1.0/clip.fps)
			i+=4 # 1초에 60 fps가 있으므로 몇개는 skip해도 될거 같음!
			if (i*1.0/clip.fps)> clip.duration:
				break
			# if not ret:
			# 	print("Error")
			# 	break
			
			# width 높이면 더 판별 잘되지만, computational power 높음
			# The benefit of increasing the resolution of the input image prior to face detection is that it may allow us to detect more faces in the imag
			frame = imutils.resize(frame, width=800)
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

			# detect faces in the grayscale frame
			# 얼굴 자체의 위치를 찾음
			rects = detector(gray, 0)

			if len(rects)>0:
				# 얼굴 개수만큼 loop
				max_width = 0
				max_rect = None
				# 얼굴 박스 제일 큰거 하나로
				for rect in rects:
					if int(rects[0].width()) > max_width:
						max_rect = rect
				# determine the facial landmarks for the face region, then
				# convert the facial landmark (x, y)-coordinates to a NumPy array
				shape = predictor(gray, max_rect)
				shape = face_utils.shape_to_np(shape)
				every_frame_info.append(shape)
			else:
				every_frame_info.append([])
			
		clips_frame_info.append(np.array(every_frame_info))

	cv2.destroyAllWindows()

	min_size = min(len(clips_frame_info[0]),len(clips_frame_info[1]))
	min_diff = float("inf")
	min_idx = 0
	for i in range(min_size):
		if len(clips_frame_info[0][i])>0 and len(clips_frame_info[1][i])>0: # 얼굴 둘다 있으면
			# 양쪽 눈
			left_eye = ((clips_frame_info[0][i][36][0] - clips_frame_info[1][i][36][0])**2 + (clips_frame_info[0][i][36][1] - clips_frame_info[1][i][36][1])**2)**0.5
			right_eye = ((clips_frame_info[0][i][45][0] - clips_frame_info[1][i][45][0])**2 + (clips_frame_info[0][i][45][1] - clips_frame_info[1][i][45][1])**2)**0.5
			total_diff = left_eye + right_eye
			if min_diff > total_diff:
				min_diff = total_diff
				min_idx = i
	
	return min_diff, min_idx
