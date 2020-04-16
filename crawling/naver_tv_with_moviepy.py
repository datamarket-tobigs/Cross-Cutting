#%%
import requests
contents_length = 1

# 전체 길이 찾을 수 있게
while True:
    url = f'https://naver-sbs-c.smartmediarep.com/smc/naver/adaptive/eng/S01_22000335770/2f7362732f75706c6f61642f3232302f30303333352f32323030303333353737306b5f76322e736d696c/0-0-0/content_2048000_{contents_length}.ts?solexpire=1587048639&solpathlen=130&soltoken=dbee156e41e74922cb86323eca442d26&soltokenrule=c29sZXhwaXJlfHNvbHBhdGhsZW58c29sdXVpZA==&soluriver=2&soluuid=22ce80c2-c758-4fd6-a855-bb4475bc3dd9'
    r = requests.get(url, allow_redirects=True)
    if r.status_code==404:
        contents_length = contents_length -1 #애는 쓸모 없는 애니까
        break
    open(f'contents_{contents_length}.ts', 'wb').write(r.content)
    contents_length = contents_length + 1

# %%
from moviepy.editor import VideoFileClip, concatenate_videoclips
contents_list = []
for idx in range(1, contents_length+1):
    contents_list.append(VideoFileClip(f"contents_{idx}.ts"))

final_clip = concatenate_videoclips(contents_list)
final_clip.write_videofile("my_concatenation.mp4")

# %%
