#%%
import requests

for idx in range(1, 21):
    # url = f'https://b01-kr-naver-vod.pstatic.net/navertv/c/read/v2/VOD_ALPHA/TVCAST_2017_01_20_3/261080qWM2BDXyzWWsdTIOMhjA_rmcvideo_1080P_1920_5120_192-00000{idx}.ts?_lsu_sa_=6025a5f6c15c6fd60ed4658364e50eb8ae9f3d18f3018f953f07cac0f79a36a55c256a316e35330d70503652d73fdba0dae633342219a51676e337002dcb4e7a5ef8e1bab168d1bc47d8940664b493c3bf4ef7671332cb8ba70eb6d2cb797cffd0f2b3289c6e197c5e098e6f866d5ba17e6c319aedc766a03d5cd9689c5537b9'
    # url = f'https://naver-mbc-h.smartmediarep.com/smc/naver/adaptive/eng/M01_TZ202004090001/2f6d62632f4174746163682f4d42432f564944454f2f543730303036472f434c49502f636c69705f545a3230323030343039303030315f32303230303430393030303235342e736d696c/0-0-0/content_5120000_{idx}.ts?solexpire=1586438868&solpathlen=197&soltoken=c30d6e412cd032b378dd07dfdb27d413&soltokenrule=c29sZXhwaXJlfHNvbHBhdGhsZW58c29sdXVpZA==&soluriver=2&soluuid=dcb6a588-bbba-4462-96de-e60e9434006a'
    url = f'https://naver-mbc-h.smartmediarep.com/smc/naver/adaptive/eng/M01_TZ202004090011/2f6d62632f4174746163682f4d42432f564944454f2f543730303036472f434c49502f636c69705f545a3230323030343039303031315f32303230303430393030333833302e736d696c/0-0-0/content_5120000_{idx}.ts?solexpire=1586479670&solpathlen=197&soltoken=052622bb2c1d995fb0d307b508d44c6f&soltokenrule=c29sZXhwaXJlfHNvbHBhdGhsZW58c29sdXVpZA==&soluriver=2&soluuid=cc588313-42bc-465f-9b5f-e5d7832cdd17'
    r = requests.get(url, allow_redirects=True)
    open(f'contents_{idx}.ts', 'wb').write(r.content)

# %%
# https://trac.ffmpeg.org/wiki/Concatenate
import subprocess
subprocess.getoutput('for f in ./*.ts; do echo "file \'$f\'" >> mylist.txt; done')
# %%
subprocess.getoutput('ffmpeg -f concat -safe 0 -i mylist.txt -c copy mergedfile.ts')
