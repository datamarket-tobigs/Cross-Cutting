#%% 
### 데이터 위에 주석 두줄 삭제해야 잘 됨 
import os 

YTID = '_ouI0sPnUpA'

# %%
######### 음성 붙이기 시도
# 720p는 음성이 없는데 붙이는 시도 했는데 계속 오류나서 해결 중..
from pytube import YouTube
import moviepy.editor as mp # 음성 붙이기 위함

import subprocess
import os
error_list = []
current_dir = os.getcwd()
file_idx = 0
try:
    yt = YouTube(f'https://www.youtube.com/watch?v={YTID}')
    print(yt.streams.filter(file_extension='mp4',res='720p').all())
    vids = yt.streams.filter(file_extension='mp4',res='720p').all() 
    vids_360 = yt.streams.filter(file_extension='mp4',res='360p').all() 
    # [<Stream: itag="140" mime_type="audio/mp4" abr="128kbps" acodec="mp4a.40.2">, <Stream: itag="249" mime_type="audio/webm" abr="50kbps" acodec="opus">, <Stream: itag="250" mime_type="audio/webm" abr="70kbps" acodec="opus">, <Stream: itag="251" mime_type="audio/webm" abr="160kbps" acodec="opus">]
    vids[0].download(f'{current_dir}/720/')
    
    # 파일 이름 바꾸기(한글 이름이 안됨)
    subprocess.call(['mv',
        os.path.join(f'{current_dir}/720/',vids[0].default_filename),
        os.path.join(f'{current_dir}/720/',f'one_vid_{file_idx}.mp4')
    ])
    # 음성 붙이기
    ### Overwrite 안됨.
    vids_360[0].download(f'{current_dir}/360/')
    subprocess.call(['ffmpeg','-ss','0','-i',
        os.path.join(f'{current_dir}/360/',vids_360[0].default_filename),
        os.path.join(f'{current_dir}/360/',f'one_mp3_{file_idx}.mp3')
    ])
    # ffmpeg -ss (start time) -i (direct video link) -t (duration needed) -c:v copy -c:a copy (destination file
except Exception as ex:
    print('에러가 발생 했습니다', ex)
# ffmpeg -ss 10 -i kk.mp4 -t 30 a.mp3
# ffmpeg -i guitar1.mp4 guitar1.mp3

# %%
import subprocess
subprocess.getoutput(f'ffmpeg -i {current_dir}/720/one_vid_{file_idx}.mp4 -i {current_dir}/360/one_mp3_{file_idx}.mp3 -c copy output.mp4')

#%%
## Trial 720p 음악 없는거 오디오넣기 -> 안됨 ㅜㅜ
# https://github.com/Zulko/moviepy/issues/213
my_audioclip = mp.AudioFileClip(os.path.join(f'{current_dir}/360/','a.mp3'))
final_clip = mp.VideoFileClip(os.path.join(f'{current_dir}/720/',vids[0].default_filename))
final_clip = final_clip.set_audio(my_audioclip)

final_clip.set_duration(5).write_videofile("result.mp4")

