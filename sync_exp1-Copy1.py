from moviepy.editor import *
import librosa
import numpy as np
from pydub import AudioSegment
import os
from functools import partial


frame_stride = 512/44100

def check_sr(file_path = "./", content_name = "ohmygirl", audiotype = ".mp3"):
    file_list = [os.path.join(file_path, content_name+str(i+1)+audiotype) for i in range(len(os.listdir(file_path)))]
    for i, file in enumerate(file_list):
        print(f"{i}번째 파일 sample rate: {AudioSegment.from_mp3(file).frame_rate}")

def get_onset(audio_tuple, mode = "f"):
    """
    audio파일과 sr을 튜플 형태로 받음
    mode는 t (time) or f (frame)
    """
    audio = audio_tuple[0]
    sr = audio_tuple[1]
    onset_frames = librosa.onset.onset_detect(y=audio, sr=sr)
    if mode == "t":
        return librosa.frames_to_time(onset_frames, sr=sr)[0]
    else:
        return onset_frames[0]

def trim_origin(audio, sr):
    idx = get_onset((audio,sr))
    audio_mel = librosa.feature.melspectrogram(y = audio, sr = sr)
    return audio_mel[:, idx:]


def get_melspectrogram(audio, sr):
    return librosa.feature.melspectrogram(y=audio, sr=sr)


# 왜인지는 모르겠는데 직캠 영상은 melspectrogram의 max 값을 주고, 음원(뮤비 추출)은 medain 값으로 계산을 할 때 결과가 좋음



def get_matching_onset(audio_mel_from, audio_mel_to, sr = 44100):
    """
    origin 음성은 median으로 aggregation,
    target 음성은 max로 aggregation

    return 값은 매칭되는 t값을 리턴함 (in frame)

    잡음으로 인해 제대로 매칭이 안되는 영상들이 있으므로
    매칭 정확도는 어느 정도 포기하고 초반 5개 프레임 안에서 min 값을 리턴
    """
    audio_from = np.median(audio_mel_from, axis = 0)
    audio_to = np.max(audio_mel_to, axis = 0)
    matched = librosa.util.match_events(audio_from, audio_to)

    return librosa.frames_to_time(matched[:5].min(), sr = sr)

def trim_video(video, t_match, file_name):
    video.subclip(t_match, t_match+5).write_videofile(file_name)


def sync_main():

    file_list = [VideoFileClip(f"../data/ohmygirl{i+1}.mp4") for i in range(6)]

    # original 파일
    origin, sr_origin = librosa.load("ohmygirl_origin.mp3", sr = 44100)
    # 직캠 파일 (튜플 담은 리스트)
    audio_list = [librosa.load(f"ohmygirl{i+1}.mp3", sr = 44100) for i in range(6)] # 44100: check sr returned value

    origin_mel = trim_origin(origin, sr_origin)
    #mel_list = list(map(get_melspectrogram, video_list))
    mel_list = [get_melspectrogram(audio, sr) for (audio, sr) in video_list]

    get_matching_onset2 = partial(get_matching_onset, origin_mel)
    t_list = list(map(get_matching_onset2, mel_list))

    for i in range(len(t_list)):
        file_name = f"test{i}.mp4"
        trim_video(file_list[i], t_list[i], file_name)


sync_main()
