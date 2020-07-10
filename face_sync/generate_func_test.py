import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
import random
import numpy as np
import time
from video_facial_landmarks import calculate_distance
import cv2


ONE_FRAME_SEC = 0.03336666666666588 # 29.97002997002997fps의 역수! # 0.03336666666666588??
EYE_MIN_DIFF = 30 # 워워워~ 예에에
WINDOW_TIME = 10
PADDED_TIME = 3 # 얼굴이 클로즈업 된게 있으면 계속 클로즈업 된 부분만 찾으므로 3초정도 띄어준다.
ZOOM_FRAME =20 # 얼굴 확대할때  시간
CROSS_FRAME = 4 #얼굴 스르르 시간
ONE_ZOOM = 1.5 # 회전할 때 검은 부분 최대한 줄이기 위해서 확대하는 비율 일단 안씀
AGAIN_ZOOM = 1.15
ROTATE_MAX = 7

# init
compare_point_max = [(0,0),(0,0)]
refer_point_max = [(0,0),(0,0)]
refer_length_max = 0
compare_length_max = 0
refer_degree_max = 0
compare_degree_max = 0

def distance(reference_clip, clip):
    # ref_frames = np.array([frame for frame in reference_clip.iter_frames()]) / 255.0
    # frames = np.array([frame for frame in clip.iter_frames()]) / 255.0
    min_diff, min_idx, refer_length, refer_degree, compare_length, compare_degree, refer_point, compare_point = calculate_distance(reference_clip, clip)
    
    return min_diff, min_idx, refer_length, refer_degree, compare_length, compare_degree, refer_point, compare_point

class Moving4:
    def __init__(self,small_point, big_point, ratio, transition_dir, rotate_degree):
        self.small_point = small_point[0]
        self.big_point = big_point[0]
        self.ratio = ratio
        self.transition_dir = transition_dir
        self.rotate_degree = -1 *rotate_degree
    def __call__(self, get_frame, t):
        # any process you want
        frame = get_frame(t)
        if len(self.small_point)==0:
            return frame
        else:
            # !! ratio가 더 커져야 한다-> 역수
            img_cv = cv2.resize(frame,(int(round(1280 * self.ratio)),int(round(720 * self.ratio))))
            cur_w = self.small_point[0] * self.ratio
            cur_h = self.small_point[1] * self.ratio

            # width height 순서가 바뀜.
            cur_degree = self.rotate_degree*(ZOOM_FRAME-t/ONE_FRAME_SEC)/ZOOM_FRAME
            M = cv2.getRotationMatrix2D((cur_w, cur_h), cur_degree, 1.0)
            img_cv = cv2.warpAffine(img_cv, M, (int(round(1280 * self.ratio)),int(round(720 * self.ratio))))
            zoom_frame = np.asarray(img_cv)
            # 얘를 center로 만들어서 줄여버리자!!
            print(self.small_point[0], self.small_point[1], '-- prev cord')
            print(self.ratio, 'ratio')

            # 이동할 애 기준으로 만들어야 함!(이게 조 ㅁ다른 포인트!!!)
            w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
            h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
            print(t,'------------------------t')
            # 혹시 사이즈가 넘어가면 사이즈를 한번 더 크게 해보기(너무 딱 맞춰서 확대하려고 하지말구!)
            w1, w2 = int(round(cur_w - 1280 * self.ratio * w_ratio)), int(round(cur_w + 1280 * self.ratio  *(1-w_ratio)))
            h1, h2 = int(round(cur_h - 720 * self.ratio * h_ratio)), int(round(cur_h + 720 * self.ratio *(1-h_ratio)))
            if h1>=0 and h2<=int(round(720 * self.ratio)) and w1>=0 and w2 <=int(round(1280 * self.ratio)):
                # 시간초에 따라서 바뀌어야 함!
                zoom_w_size, zoom_h_size =  1280 * self.ratio, 720 * self.ratio 
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    print('----------small to big')
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    print(W_real, H_real, "W real H real")
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    # 이거계산할 때 진짜 운이 좋아서 잘 되는거다 ZOOM_FRAME 1초 t/ONE_FRAME_SEC 0.033 -> 30개 하면 0.99~1초. 그래서 1쯤 되어서 확대가 잘 되는거
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                # 16:9 비율
                print(cur_w, cur_h,'cur info')
                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔을때!
                print(w1, w2, h1, h2,'infooo')
                if h1>=0 and h2<=int(round(720 * self.ratio)) and w1>=0 and w2 <=int(round(1280 * self.ratio)):
                    print('---------cutteddddd')
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    print('-----NOT AVAIL NOT AVAIL')
                    frame_region = frame
                return frame_region
            else:
                # 딱 한번 확대 기회를 주자!
                img_cv = cv2.resize(zoom_frame, dsize=(0, 0),fx=AGAIN_ZOOM, fy=AGAIN_ZOOM) # AGAIN_ZOOM 만큼 확대하기
                zoom_frame = np.asarray(img_cv)
                cur_w = self.small_point[0] * self.ratio * AGAIN_ZOOM
                cur_h = self.small_point[1] * self.ratio * AGAIN_ZOOM

                # 이동할 애 기준으로 만들어야 함!(이게 조 ㅁ다른 포인트!!!)
                w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
                h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
                
                # 사이즈 자체는 확대하지 않아야 한다!!
                zoom_w_size, zoom_h_size =  1280 * self.ratio, 720 * self.ratio 
                # 시간초에 따라서 바뀌어야 함!
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    print('----------small to big')
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    print(W_real, H_real, "W real H real")
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                # 16:9 비율
                print(cur_w, cur_h,'cur info')
                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔을때!
                print(w1, w2, h1, h2,'infooo')
                if h1>=0 and h2<=int(round(720 * self.ratio*AGAIN_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio*AGAIN_ZOOM)):
                    print('---------cutteddddd')
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    print('-----NOT AVAIL NOT AVAIL')
                    frame_region = frame
                return frame_region

# Rotate 할 때 빈 바리 메꾸기 위해서 기본적으로 확대하기!
class Moving5:
    def __init__(self,small_point, big_point, ratio, transition_dir, rotate_degree):
        self.small_point = small_point[0]
        self.big_point = big_point[0]
        self.ratio = ratio
        self.transition_dir = transition_dir
        self.rotate_degree = -1 *rotate_degree
    def __call__(self, get_frame, t):
        # any process you want
        frame = get_frame(t)
        if len(self.small_point)==0:
            return frame
        else:
            img_cv = cv2.resize(frame,(int(round(1280 * self.ratio * ONE_ZOOM)),int(round(720 * self.ratio * ONE_ZOOM))))
            cur_w = self.small_point[0] * self.ratio * ONE_ZOOM
            cur_h = self.small_point[1] * self.ratio * ONE_ZOOM

            # width height 순서가 바뀜.
            cur_degree = self.rotate_degree*(ZOOM_FRAME-t/ONE_FRAME_SEC)/ZOOM_FRAME
            M = cv2.getRotationMatrix2D((cur_w, cur_h), cur_degree, 1.0)
            img_cv = cv2.warpAffine(img_cv, M, (int(round(1280 * self.ratio * ONE_ZOOM)),int(round(720 * self.ratio * ONE_ZOOM))))
            zoom_frame = np.asarray(img_cv)
            # 얘를 center로 만들어서 줄여버리자!!
            # print(self.small_point[0], self.small_point[1], '-- prev cord')
            # print(self.ratio, 'ratio')

            # 이동할 애 기준으로 만들어야 함!(이게 조 ㅁ다른 포인트!!!)
            w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
            h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
            
            # 혹시 사이즈가 넘어가면 사이즈를 한번 더 크게 해보기(너무 딱 맞춰서 확대하려고 하지말구!)
            # ! 여기선 ONE_ZOOM 뺀 상태로 확대해야 한다(그래야 원하는 크기로 잘리지)
            w1, w2 = int(round(cur_w - 1280 * self.ratio * w_ratio)), int(round(cur_w + 1280 * self.ratio  *(1-w_ratio)))
            h1, h2 = int(round(cur_h - 720 * self.ratio * h_ratio)), int(round(cur_h + 720 * self.ratio *(1-h_ratio)))
            if h1>=0 and h2<=int(round(720 * self.ratio * ONE_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio * ONE_ZOOM)):
                # 시간초에 따라서 바뀌어야 함!
                zoom_w_size, zoom_h_size =  1280 * self.ratio, 720 * self.ratio 
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    # print(W_real, H_real, "W real H real")
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    # 이거계산할 때 진짜 운이 좋아서 잘 되는거다 ZOOM_FRAME 1초 t/ONE_FRAME_SEC 0.033 -> 30개 하면 0.99~1초. 그래서 1쯤 되어서 확대가 잘 되는거
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                # 16:9 비율
                # print(cur_w, cur_h,'cur info')
                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔을때!
                # print(w1, w2, h1, h2,'infooo')
                if h1>=0 and h2<=int(round(720 * self.ratio * ONE_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio * ONE_ZOOM)):
                    print('---------cutteddddd')
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    print('-----NOT AVAIL NOT AVAIL')
                    frame_region = frame
                return frame_region
            else:
                # 딱 한번 확대 기회를 주자!
                img_cv = cv2.resize(zoom_frame, dsize=(0, 0),fx= ONE_ZOOM * AGAIN_ZOOM, fy= ONE_ZOOM * AGAIN_ZOOM) # AGAIN_ZOOM 만큼 확대하기
                zoom_frame = np.asarray(img_cv)
                cur_w = self.small_point[0] * self.ratio * ONE_ZOOM * AGAIN_ZOOM
                cur_h = self.small_point[1] * self.ratio * ONE_ZOOM * AGAIN_ZOOM

                # 이동할 애 기준으로 만들어야 함!(이게 조 ㅁ다른 포인트!!!)
                w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
                h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
                
                # 사이즈 자체는 확대하지 않아야 한다!!
                zoom_w_size, zoom_h_size =  1280 * self.ratio, 720 * self.ratio 
                # 시간초에 따라서 바뀌어야 함!
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    # print(W_real, H_real, "W real H real")
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                # 16:9 비율
                # print(cur_w, cur_h,'cur info')
                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔을때!
                # print(w1, w2, h1, h2,'infooo')
                if h1>=0 and h2<=int(round(720 * self.ratio*ONE_ZOOM *AGAIN_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio*ONE_ZOOM *AGAIN_ZOOM)):
                    print('---------cutteddddd')
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    print('-----NOT AVAIL NOT AVAIL')
                    frame_region = frame
                return frame_region


# 이건 사이즈가 안맞아서 한번 더 확대 했을때 다른 쪽 영상을 처리하는 Class
class ForceZoom:
    def __init__(self,small_point, big_point, ratio, transition_dir):
        self.small_point = small_point[0]
        self.big_point = big_point[0]
        self.ratio = ratio
        self.transition_dir = transition_dir
    def __call__(self, get_frame, t):
        # any process you want
        frame = get_frame(t)
        if len(self.small_point)==0:
            return frame
        else:
            print('--------------------- DO FORCE ZOOM')
            # !! ratio가 더 커져야 한다-> 역수
            img_cv = cv2.resize(frame,(int(round(1280 * self.ratio)),int(round(720 * self.ratio))))
            zoom_frame = np.asarray(img_cv)
            cur_w = self.small_point[0] * self.ratio
            cur_h = self.small_point[1] * self.ratio
            # 이동할 애 기준으로 만들어야 함!(이게 조 ㅁ다른 포인트!!!)
            w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
            h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
            
            # 혹시 사이즈가 넘어가면 사이즈를 한번 더 크게 해보기(너무 딱 맞춰서 확대하려고 하지말구!)
            w1, w2 = int(round(cur_w - 1280 * self.ratio * w_ratio)), int(round(cur_w + 1280 * self.ratio  *(1-w_ratio)))
            h1, h2 = int(round(cur_h - 720 * self.ratio * h_ratio)), int(round(cur_h + 720 * self.ratio *(1-h_ratio)))
            # 확대될 사이즈도 확인(Force ZOOM 이 가능했었니? az = again zoom)
            cur_w_az = self.small_point[0] * self.ratio * AGAIN_ZOOM
            cur_h_az = self.small_point[1] * self.ratio * AGAIN_ZOOM
            w1_az, w2_az = int(round(cur_w_az - 1280 * self.ratio * w_ratio)), int(round(cur_w_az + 1280 * self.ratio  *(1-w_ratio)))
            h1_az, h2_az = int(round(cur_h_az - 720 * self.ratio * h_ratio)), int(round(cur_h_az + 720 * self.ratio *(1-h_ratio)))
            # print(w1_az, w2_az, h1_az, h2_az, '== az info')
            # 앞에서 안되어도 되는걸로 만들어질수도 있음...확대되어도 안되면 넘어가야지!
            # 원래건 안되고(not) 확대되는건 되어야 함!! 
            if not( h1>=0 and h2<=int(round(720 * self.ratio)) and w1>=0 and w2 <=int(round(1280 * self.ratio))) and \
               h1_az>=0 and h2_az<=int(round(720 * self.ratio*AGAIN_ZOOM)) and w1_az>=0 and w2_az<=int(round(1280 * self.ratio*AGAIN_ZOOM)):
                # 사이즈가 넘어가서 확대를 했었다면, 나는 처음부터 다시 시작하자!
                img_cv = cv2.resize(frame, dsize=(0, 0),fx=AGAIN_ZOOM, fy=AGAIN_ZOOM) # AGAIN_ZOOM 만큼 확대하기
                zoom_frame = np.asarray(img_cv)
                cur_w = self.big_point[0] * AGAIN_ZOOM
                cur_h = self.big_point[1] * AGAIN_ZOOM

                # 이동할 애 기준으로 만들어야 함!(이게 조 ㅁ다른 포인트!!!)
                w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
                h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
                
                # 사이즈 자체는 확대하지 않아야 한다!!
                zoom_w_size, zoom_h_size =  1280 * AGAIN_ZOOM, 720 * AGAIN_ZOOM
                # 시간초에 따라서 바뀌어야 함!
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    # 이거계산할 때 진짜 운이 좋아서 잘 되는거다 ZOOM_FRAME 1초 t/ONE_FRAME_SEC 0.033 -> 30개 하면 0.99~1초. 그래서 1쯤 되어서 확대가 잘 되는거
                    # 사이즈가 더 커지면, 다시 resize할떄 작아짐. 그래서 처음에는 작은 사이즈에서 큰 사이즈로 가면, resize후엔 확대 후 축소한는거 같음
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                # 16:9 비율
                print(cur_w, cur_h,'cur info')
                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔을때!
                print(w1, w2, h1, h2,'infooo')
                if h1>=0 and h2<=int(round(720 * self.ratio*AGAIN_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio*AGAIN_ZOOM)):
                    print('---------cutteddddd')
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    print('-----NOT AVAIL NOT AVAIL')
                    frame_region = frame
                return frame_region
            else: # 그런 경우 아니었으면 확대 없이 return
                return frame

# 이건 사이즈가 안맞아서 한번 더 확대 했을때 다른 쪽 영상을 처리하는 Class
class ForceZoom2:
    def __init__(self,small_point, big_point, ratio, transition_dir):
        self.small_point = small_point[0]
        self.big_point = big_point[0]
        self.ratio = ratio
        self.transition_dir = transition_dir
    def __call__(self, get_frame, t):
        # any process you want
        frame = get_frame(t)
        if len(self.small_point)==0:
            return frame
        else:
            print('--------------------- DO FORCE ZOOM')
            # !! ratio가 더 커져야 한다-> 역수
            img_cv = cv2.resize(frame,(int(round(1280 *ONE_ZOOM * self.ratio)),int(round(720 *ONE_ZOOM* self.ratio))))
            zoom_frame = np.asarray(img_cv)
            cur_w = self.small_point[0] *ONE_ZOOM * self.ratio
            cur_h = self.small_point[1] *ONE_ZOOM * self.ratio
            # 이동할 애 기준으로 만들어야 함!(이게 조 ㅁ다른 포인트!!!)
            w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
            h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
            
            # 혹시 사이즈가 넘어가면 사이즈를 한번 더 크게 해보기(너무 딱 맞춰서 확대하려고 하지말구!)
            w1, w2 = int(round(cur_w - 1280 * self.ratio * w_ratio)), int(round(cur_w + 1280 * self.ratio  *(1-w_ratio)))
            h1, h2 = int(round(cur_h - 720 * self.ratio * h_ratio)), int(round(cur_h + 720 * self.ratio *(1-h_ratio)))

            # 확대될 사이즈도 확인(Force ZOOM 이 가능했었니? az = again zoom)
            cur_w_az = self.small_point[0] *ONE_ZOOM * self.ratio * AGAIN_ZOOM
            cur_h_az = self.small_point[1] *ONE_ZOOM * self.ratio * AGAIN_ZOOM
            w1_az, w2_az = int(round(cur_w_az - 1280 * self.ratio * w_ratio)), int(round(cur_w_az + 1280 * self.ratio  *(1-w_ratio)))
            h1_az, h2_az = int(round(cur_h_az - 720 * self.ratio * h_ratio)), int(round(cur_h_az + 720 * self.ratio *(1-h_ratio)))
            # print(w1_az, w2_az, h1_az, h2_az, '== az info')
            # 앞에서 안되어도 되는걸로 만들어질수도 있음...확대되어도 안되면 넘어가야지!
            # 원래건 안되고(not) 확대되는건 되어야 함!! 
            if not( h1>=0 and h2<=int(round(720 * self.ratio*ONE_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio*ONE_ZOOM))) and \
               h1_az>=0 and h2_az<=int(round(720 * self.ratio*ONE_ZOOM*AGAIN_ZOOM)) and w1_az>=0 and w2_az<=int(round(1280 * self.ratio*AGAIN_ZOOM*ONE_ZOOM)):
                # 사이즈가 넘어가서 확대를 했었다면, 나는 처음부터 다시 시작하자!
                img_cv = cv2.resize(frame, dsize=(0, 0),fx=ONE_ZOOM * AGAIN_ZOOM, fy=ONE_ZOOM * AGAIN_ZOOM) # AGAIN_ZOOM 만큼 확대하기
                zoom_frame = np.asarray(img_cv)
                cur_w = self.big_point[0] * ONE_ZOOM * AGAIN_ZOOM
                cur_h = self.big_point[1] * ONE_ZOOM * AGAIN_ZOOM

                # 이동할 애 기준으로 만들어야 함!(이게 조 ㅁ다른 포인트!!!)
                w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
                h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
                
                # 사이즈 자체는 확대하지 않아야 한다!!
                zoom_w_size, zoom_h_size =  1280 * ONE_ZOOM  * AGAIN_ZOOM, 720  * ONE_ZOOM * AGAIN_ZOOM
                # 시간초에 따라서 바뀌어야 함!
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    # 이거계산할 때 진짜 운이 좋아서 잘 되는거다 ZOOM_FRAME 1초 t/ONE_FRAME_SEC 0.033 -> 30개 하면 0.99~1초. 그래서 1쯤 되어서 확대가 잘 되는거
                    # 사이즈가 더 커지면, 다시 resize할떄 작아짐. 그래서 처음에는 작은 사이즈에서 큰 사이즈로 가면, resize후엔 확대 후 축소한는거 같음
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                # 16:9 비율
                # print(cur_w, cur_h,'cur info')
                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔을때!
                # print(w1, w2, h1, h2,'infooo')
                if h1>=0 and h2<=int(round(720 * self.ratio*ONE_ZOOM*AGAIN_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio*ONE_ZOOM*AGAIN_ZOOM)):
                    print('---------cutteddddd')
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    print('-----NOT AVAIL NOT AVAIL')
                    frame_region = frame
                return frame_region
            else: # 그런 경우 아니었으면 확대 없이 return
                # 사이즈가 넘어가서 확대를 했었다면, 나는 처음부터 다시 시작하자!
                # 이때는 그냥 한번 확대해주자!
                img_cv = cv2.resize(frame, dsize=(0, 0),fx=ONE_ZOOM, fy=ONE_ZOOM) # AGAIN_ZOOM 만큼 확대하기
                zoom_frame = np.asarray(img_cv)
                cur_w = self.big_point[0] * ONE_ZOOM 
                cur_h = self.big_point[1] * ONE_ZOOM

                # 이동할 애 기준으로 만들어야 함!(이게 조 ㅁ다른 포인트!!!)
                w_ratio = self.big_point[0]/1280 # 그 비율만큼 왼쪽 마이너스
                h_ratio = self.big_point[1]/720 # 그 비율만큼 위쪽 마이너스
                
                # 사이즈 자체는 확대하지 않아야 한다!!
                zoom_w_size, zoom_h_size =  1280 * ONE_ZOOM, 720  * ONE_ZOOM
                # 시간초에 따라서 바뀌어야 함!
                if self.transition_dir == 'small_to_big': # 앞에가 작고 뒤에가 큰거!
                    W_real = zoom_w_size - (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = zoom_h_size - (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                elif self.transition_dir == 'big_to_small': # 되려 시간이 지나면서 사이즈가 더 커져야 resize를 하면 더 넓은 부분이 나옴
                    # 이거계산할 때 진짜 운이 좋아서 잘 되는거다 ZOOM_FRAME 1초 t/ONE_FRAME_SEC 0.033 -> 30개 하면 0.99~1초. 그래서 1쯤 되어서 확대가 잘 되는거
                    # 사이즈가 더 커지면, 다시 resize할떄 작아짐. 그래서 처음에는 작은 사이즈에서 큰 사이즈로 가면, resize후엔 확대 후 축소한는거 같음
                    W_real = 1280 + (zoom_w_size - 1280)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                    H_real = 720 + (zoom_h_size- 720)*(t/ONE_FRAME_SEC)/ZOOM_FRAME
                else: # 'same' 그냥 큰 상태로 유지!
                    W_real = 1280
                    H_real = 720

                # 16:9 비율
                # print(cur_w, cur_h,'cur info')
                w1, w2 = int(round(cur_w - W_real * w_ratio)), int(round(cur_w + W_real *(1-w_ratio)))
                h1, h2 = int(round(cur_h - H_real * h_ratio)), int(round(cur_h + H_real *(1-h_ratio)))
                # 확대된 범위를 넘어갔을때!
                # print(w1, w2, h1, h2,'infooo')
                if h1>=0 and h2<=int(round(720 * self.ratio*AGAIN_ZOOM)) and w1>=0 and w2 <=int(round(1280 * self.ratio*AGAIN_ZOOM)):
                    print('---------cutteddddd')
                    frame_region = zoom_frame[h1:h2,w1:w2]
                else:
                    print('-----NOT AVAIL NOT AVAIL')
                    frame_region = frame
                return frame_region


class MovingInv:
    def __init__(self,small_point, big_point, ratio, transition_dir):
        self.small_point = small_point
        self.big_point = big_point
        self.ratio = ratio
        self.transition_dir = transition_dir
    def __call__(self, get_frame, t):
        # any process you want
        frame = get_frame(t)
        # AX = B
        A = np.array(self.small_point)
        B = np.array(self.big_point)
        A_inv = np.linalg.inv(A)
        X = A_inv@B # 변형시키는 식

        
        return changed_frame #변형된 frame

 
def crosscut(videos_path="./video", option="random"):
    min_time = 1000.0
    min_idx = 0
    audioclip = None
    extracted_clips_array = []
    #                0  1  2  3  4  5   6  7  8  9  10
    # start_times = [0, 4, 4, 0, 0, 1, 14, 0, 0, 0, 0]
    # VIDEO SONG START TIME ARRAY
    start_times = [0.3, 1, 0] # 노래 개수
    # start_times = [0,0,5] # 노래 개수

    # VIDEO ALIGNMENT -> SLICE START TIME
    for i in range(len(os.listdir(videos_path))):
        video_path = os.path.join(videos_path, sorted(os.listdir(videos_path))[i])
        clip = VideoFileClip(video_path)
        clip = clip.subclip(start_times[i], clip.duration) # 그냥 전체 영상을 시작점 맞게 자르기
        print(video_path, clip.fps, clip.duration)
        if min_time > clip.duration: # ?? 제일 작은거 기준으로 자르려는건가?? 근데 그러면 그 앞에건 이미 크지않나??
            audioclip = clip.audio
            min_time = clip.duration
            min_idx = i
            print(video_path, clip.fps, clip.duration)
        extracted_clips_array.append(clip)
    print(len(extracted_clips_array))

    con_clips = []
    t = 0
    current_idx = 0
    check_tqdm = 1
    # GENERATE STAGEMIX
    # CONCAT SUBCLIP 0~ MIN DURATION CLIP TIME
    while t <= int(min_time):
        print(check_tqdm,'------------------------------------------------------------------')
        check_tqdm += 1
        # 10 sec.
        cur_t = t
        next_t = min(t+WINDOW_TIME, min_time) # 마지막은 window초보다 작은초일수도 있으니
        next_frame =  min(t+WINDOW_TIME, min_time) # 제일 비슷한 영상을 못찾으면 그냥 window초 넘어갈수 있다

        # RANDOM BASED METHOD
        if option=="random":
            random_video_idx = random.randint(0, len(extracted_clips_array)-1)
            clip = extracted_clips_array[random_video_idx].subclip(cur_t, next_t)
            t = next_frame
            con_clips.append(clip)
        else:
            # 지금 현재 영상!
            reference_clip = extracted_clips_array[current_idx].subclip(cur_t, next_t)
            d = 5000000
            # inf가 있을때는 이 idx로 설정됨!
            min_idx = (current_idx+1)%len(extracted_clips_array) 
            for video_idx in range(len(extracted_clips_array)):
                # 같은 영상 나올수도 있는 문제 해결
                if video_idx == current_idx:
                    continue
                # 10초간 영상 확인
                clip = extracted_clips_array[video_idx].subclip(cur_t, next_t) 
                
                # 이미 확인한 앞부분은 무시해야 함!!(! 첫번째 영상은 3초는 무조건 안겹치는 문제 있음)
                # !! ㅜㅜ 제일 좋은 얼굴 부분 놓칠수도 있을듯!
                # reference_clip_for_distance = reference_clip.subclip(PADDED_TIME, WINDOW_TIME)
                # clip_for_distance = clip.subclip(PADDED_TIME, WINDOW_TIME)
                # CALCULATE DISTANCE between reference_clip_for_distance, clip_for_distance(같은초에서 최선의 거리 장면 찾기)
                cur_d, plus_frame, refer_length, refer_degree, compare_length, compare_degree, refer_point, compare_point = distance(reference_clip, clip) 
                print('from video:',current_idx, ' to video',video_idx, ' in distance ',cur_d, ' in sec ' ,cur_t + plus_frame, 'first deg ', refer_degree, 'second deg ', compare_degree)
                # print(refer_length, refer_degree, compare_length, compare_degree)
                if d > cur_d:
                    d = cur_d
                    min_idx = video_idx
                    next_frame = cur_t + plus_frame # 바로 옮길 frame
                    cur_clip = reference_clip.subclip(0,plus_frame)
                    next_clip = clip.subclip(0, plus_frame) # 그 바꿀 부분만 자르는 클립!
                    compare_point_max = compare_point
                    refer_point_max = refer_point
                    refer_length_max = refer_length # 이거에 맞춰서 확대 축소 해줄거야!
                    compare_length_max = compare_length # 이거에 맞춰 확대 축소 해줄거야!
                    refer_degree_max = refer_degree
                    compare_degree_max = compare_degree
            
            if d == 5000000: # 둘다 inf일떄,
                current_idx = min_idx # 바로 다음에 이어지면 가까운 거리로 연결되는 데이터
                clip = cur_clip # 현재 클립(바꾸면 가장 좋은 부분까지 잘린 현재 클립)
                t = next_frame
                con_clips.append(clip)
                # 뒤에 padding 데이터 더하기
                pad_clip = extracted_clips_array[current_idx].subclip(t, min(min_time,t+PADDED_TIME)) # min_time을 넘어가면 안됨!
                t = min(min_time,t + PADDED_TIME) # padding 된 시간 더하기
                con_clips.append(pad_clip)
            else:
                # refer_degree_max = refer_degree_max if refer_degree_max>=0 else 360-refer_degree_max
                # compare_degree_max = compare_degree_max if compare_degree_max>=0 else 360-compare_degree_max
                # (!! 현재 영상을 concat 하고 다음에 넣을 영상 idx를 저장해야 한다!)
                prev_idx = current_idx
                current_idx = min_idx # 바로 다음에 이어지면 가까운 거리로 연결되는 데이터
                print("next video idx : {}".format(current_idx))
                print(refer_length_max, compare_length_max, '----refer, compare length max')
                clip = cur_clip # 현재 클립(바꾸면 가장 좋은 부분까지 잘린 현재 클립)
                # clip = next_clip ## 이건 직관적이지 않고 틀림 ㅜㅜ

                # 여기서 편집하기 -----------------------------------
                t = next_frame
                # 앞에 부분 자르기!(뒤 transition 제외)
                clip_front = clip.subclip(0,clip.duration-(ONE_FRAME_SEC*ZOOM_FRAME)) # 그 바꿀 부분만 자르는 클립!
                con_clips.append(clip_front)
                # # 뒤에 transition 부분 붙이기
                ### !! 너무 padding 이 마이너스로 되어있으면 그 이전 영상을 찾아서 넣나봄!!(그래서 툭툭 끊김) 그러므로 너무 크게 빼도 안되겠네
                clip_back = clip.subclip(clip.duration-(ONE_FRAME_SEC*ZOOM_FRAME),clip.duration)
                print(refer_point_max, compare_point_max, '----start point')
                ## resize
                if abs(compare_length_max-refer_length_max) < EYE_MIN_DIFF and abs(compare_degree_max-refer_degree_max) < ROTATE_MAX:
                    if compare_length_max> refer_length_max and compare_length_max-refer_length_max < EYE_MIN_DIFF:
                        # clip_back = clip_back.fl(Moving2(refer_point_max, compare_point_max, refer_length_max/compare_length_max,'small_to_big'))
                        clip_back = clip_back.fl(Moving5(refer_point_max, compare_point_max, compare_length_max/refer_length_max,'small_to_big',compare_degree_max-refer_degree_max))
                        clip_back = clip_back.resize((1280,720))
                    else:
                        clip_back = clip_back.fl(ForceZoom2(compare_point_max, refer_point_max, refer_length_max/compare_length_max,'small_to_big'))
                        clip_back = clip_back.resize((1280,720))

                    clip_back_not_fade = clip_back.subclip(0,clip_back.duration-ONE_FRAME_SEC*CROSS_FRAME)
                    clip_back_fade= clip_back.subclip(clip_back.duration-ONE_FRAME_SEC*CROSS_FRAME, clip_back.duration)
                    cross_clip = extracted_clips_array[current_idx].subclip(t-ONE_FRAME_SEC*CROSS_FRAME, t) # min_time을 넘어가면 안됨!
                    # 뒤쪽이 확대되었따가 축소 되는 경우에는 cross fade 할 떄도 확대된 상태로 해야하니까!
                    # if refer_length_max> compare_length_max and refer_length_max-compare_length_max < EYE_MIN_DIFF:   
                    #     cross_clip = cross_clip.fl(Moving3(compare_point_max, refer_point_max, compare_length_max/refer_length_max, 'same'))
                    #     cross_clip = cross_clip.resize((1280,720))
                    # clip_back_fade = CompositeVideoClip([clip_back_fade, cross_clip.crossfadein(ONE_FRAME_SEC*CROSS_FRAME)])
                    con_clips.append(clip_back_not_fade)
                    con_clips.append(clip_back_fade)
                else:
                    con_clips.append(clip_back)
                
                # con_clips.append(clip)
            
                # 뒤에 padding 데이터 더하기 -----------------------------
                pad_clip = extracted_clips_array[current_idx].subclip(t, min(min_time,t + PADDED_TIME)) # min_time을 넘어가면 안됨!
                if abs(compare_length_max-refer_length_max) < EYE_MIN_DIFF and abs(compare_degree_max-refer_degree_max) < ROTATE_MAX:
                    pad_front = pad_clip.subclip(0,ONE_FRAME_SEC*ZOOM_FRAME) # 그 바꿀 부분만 자르는 클립!
                    # 앞이 더 크고 뒤가 작을 때
                    if refer_length_max> compare_length_max and refer_length_max-compare_length_max < EYE_MIN_DIFF:
                        # 더 작아져야하쥐!(결국 확대?)
                        # pad_front = pad_front.fl(Moving2(compare_point_max, refer_point_max, compare_length_max/refer_length_max, 'big_to_small'))
                        pad_front = pad_front.fl(Moving5(compare_point_max, refer_point_max, refer_length_max/compare_length_max, 'big_to_small',refer_degree_max-compare_degree_max))
                        pad_front = pad_front.resize((1280,720))
                        print('yooooooo')
                        # 앞에 영상 연속해서 틀기
                        cross_clip = extracted_clips_array[prev_idx].subclip(t, t+ONE_FRAME_SEC*CROSS_FRAME) # min_time을 넘어가면 안됨!
                        pad_front = CompositeVideoClip([pad_front, cross_clip.crossfadeout(ONE_FRAME_SEC*CROSS_FRAME)])
                    else: # 혹시 앞에서 크기가 안되어서 확대를 더 했다면?(실제 비율보다 AGAIN_ZOOM 만큼 확대했다면,)
                        pad_front = pad_front.fl(ForceZoom2(refer_point_max, compare_point_max , compare_length_max/refer_length_max, 'big_to_small'))
                        pad_front = pad_front.resize((1280,720))
                        cross_clip = extracted_clips_array[prev_idx].subclip(t, t+ONE_FRAME_SEC*CROSS_FRAME) # min_time을 넘어가면 안됨!
                        cross_clip = cross_clip.fl(Moving5(refer_point_max, compare_point_max, compare_length_max/refer_length_max, 'same',0))
                        pad_front = CompositeVideoClip([pad_front, cross_clip.crossfadeout(ONE_FRAME_SEC*CROSS_FRAME)])

                    con_clips.append(pad_front)
                    pad_back = pad_clip.subclip(ONE_FRAME_SEC*ZOOM_FRAME,pad_clip.duration) # 그 바꿀 부분만 자르는 클립!
                    t = min(min_time, t + PADDED_TIME) # padding 된 시간 더하기
                    # txt = TextClip(str(check_tqdm),  font='Amiri-regular',color='white', fontsize=24)
                    # pad_back = CompositeVideoClip([pad_back,txt])
                    con_clips.append(pad_back)
                else:
                    t = min(min_time, t + PADDED_TIME) # padding 된 시간 더하기
                    # txt = TextClip(str(check_tqdm),  font='Amiri-regular',color='white', fontsize=24)
                    # pad_clip = CompositeVideoClip([pad_clip,txt])
                    con_clips.append(pad_clip)

    final_clip = concatenate_videoclips(con_clips)

    if audioclip !=None:
        final_clip.audio = audioclip

    final_clip.write_videofile("random.mp4")
    return final_clip

start_time = time.time()
crosscut(videos_path="./video", option="norandom")
end_time = time.time()

print(end_time - start_time, 'total Generation time')
# 그냥 1 frame으로 총 작업하는데 2688.1366200447083
# 4 frame  576.5337190628052
