from moviepy.editor import VideoFileClip

# 비디오에서 subclip을 얻는다
# output: mp4 or gif
def save_subclip(video_path, start_sec, end_sec, out_name, toGIF):

    # Load video
    video = VideoFileClip(video_path)

    # Get subclip
    clip = video.subclip(start_sec, min(end_sec, video.duration))

    # Save subclip
    if toGIF:
        clip.write_gif(out_name, fps=video.fps)
    else:
        clip.write_videofile(out_name)


    return clip


if __name__ == '__main__':
    
    # path와 시간, output이름, GIF/MP4 확장자 설정하기
    video_path = 'C:/Users/eunsun/tobigs/Cross-Cutting/face_sync/wannabe.mp4'
    start_sec = '17'
    end_sec = '18.8'
    out_name = 'wan_short_3'
    isGIF = True

    if isGIF:
        out_name += '.gif'
    else:
        out_name += '.mp4'
    
    
    save_subclip(video_path, float(start_sec), float(end_sec), out_name, isGIF)

