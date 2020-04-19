#%%
import requests
contents_length = 1

# 전체 길이 찾을 수 있게
while True:
    # url = f'https://naver-sbs-c.smartmediarep.com/smc/naver/adaptive/eng/S01_22000335770/2f7362732f75706c6f61642f3232302f30303333352f32323030303333353737306b5f76322e736d696c/0-0-0/content_2048000_{contents_length}.ts?solexpire=1587048639&solpathlen=130&soltoken=dbee156e41e74922cb86323eca442d26&soltokenrule=c29sZXhwaXJlfHNvbHBhdGhsZW58c29sdXVpZA==&soluriver=2&soluuid=22ce80c2-c758-4fd6-a855-bb4475bc3dd9'
    url = f'https://naver-sbs-c.smartmediarep.com/smc/naver/adaptive/eng/S01_22000335770/2f7362732f75706c6f61642f3232302f30303333352f32323030303333353737306b5f76322e736d696c/0-0-0/content_5120000_{contents_length}.ts?solexpire=1587308911&solpathlen=130&soltoken=cd685af8f4a67c9c2f20741349420889&soltokenrule=c29sZXhwaXJlfHNvbHBhdGhsZW58c29sdXVpZA==&soluriver=2&soluuid=2d586286-dd4a-4019-920d-3ee81cb20bea'
    r = requests.get(url, allow_redirects=True)
    if r.status_code==404:
        contents_length = contents_length -1 #애는 쓸모 없는 애니까
        break
    open(f'contents_{contents_length}.ts', 'wb').write(r.content)
    contents_length = contents_length + 1
    
# %%
# https://trac.ffmpeg.org/wiki/Concatenate
import subprocess
concat_files = [f'contents_{i}.ts'for i in range(1,contents_length+1)]
concat_str = '|'.join(concat_files)
subprocess.getoutput(f'ffmpeg -i "concat:{concat_str}" -c copy output.ts')
