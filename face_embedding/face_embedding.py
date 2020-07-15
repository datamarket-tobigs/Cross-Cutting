from PIL import Image
import numpy as np
from mtcnn.mtcnn import MTCNN
from keras_facenet import FaceNet


def extract_face_from_frame(frame, required_size=(160, 160)):
  detector = MTCNN() # face detector
  results = detector.detect_faces(frame) # detected face
  if results != []: ## if detected
    if len(results) == 1:
      idx = 0
    else:
      idx = np.argmax(results[x]['box'][0] for x in range(len(results)))
    x1, y1, width, height = results[idx]['box'] # bounding box 좌표 가져오기
    # deal with negative pixel index
    x1, y1 = abs(x1), abs(y1) # negative pixel index 처리
    x2, y2 = x1 + width, y1 + height
    face = frame[y1:y2, x1:x2] # 얼굴 좌표 뽑기
    img = Image.fromarray(face).resize(required_size) # required_size로 face size resizing
    face_array = np.asarray(img) # to array
  else:
    face_array = np.asarray([])
  return face_array

def calculate_euclidean_distance(ref_frame, frame):
  """
  128차원 embedding vector를 구하고 유클리드 거리 계산.

  - input
  reference_clip: VideoFileClip
  clip: VideoFileClip

  - output
  euclidean distance between two vector, clip의 마지막 frame return
  """
  # Get image as an numpy array
  #ref_frame = reference_clip.get_frame(reference_clip.reader.nframes/reference_clip.fps)
  #frame = clip.get_frame(clip.reader.nframes/clip.fps)

  # detection
  ref_frame_detected = extract_face_from_frame(ref_frame)
  frame_detected = extract_face_from_frame(frame)

  if (len(ref_frame_detected) == 0 or len(frame_detected) == 0): # 하나라도 얼굴이 감지되지 않는 경우
      return 100

  # feature extraction (embedding)
  ref_frame_detected = ref_frame_detected.reshape((1,)+ref_frame_detected.shape) # 모델 인풋 차원에 맞게 수정
  frame_detected = frame_detected.reshape((1,)+frame_detected.shape)


  embed_model = FaceNet()
  ref_frame_embed = embed_model.embeddings(ref_frame_detected)
  frame_embed = embed_model.embeddings(frame_detected)

  diff = ref_frame_embed - frame_embed
  euclidean_dist = np.sqrt(np.sum(np.multiply(diff, diff)))
  return euclidean_dist


def get_transition_point(reference_clip, clip):
    """
    returns the transition point in time and the distance at that time
    """
    skip_frame_rate = 2
    upper_lim = round(min(reference_clip.fps, clip.fps))
    distances = [calculate_euclidean_distance(reference_clip.get_frame(i*1.0/reference_clip.fps), clip.get_frame(i*1.0/clip.fps)) for i in range(0,upper_lim, skip_frame_rate)]
    transition_idx = np.argmin(distances)

    return transition_idx*2/clip.fps, distances[transition_idx]
