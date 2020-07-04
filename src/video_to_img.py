import cv2
import os

video_dir = "sub_clips/"

def video_to_frames(video, path_output_dir, i):
    # extract frames from a video and save to directory as 'x.png' where 
    # x is the frame index
    vidcap = cv2.VideoCapture(video)
    count = 0
    while vidcap.isOpened():
        success, image = vidcap.read()
        if success:
            if count % 30 == 0:
                cv2.imwrite(os.path.join(path_output_dir, '%d video %d.png') % (i, count), image)
            count += 1
        else:
            break
    cv2.destroyAllWindows()
    vidcap.release()


for i in range(24):
    os.makedirs('img/' + str(i * 10) + "-" + str((i+1) * 10))
    video_path = 'img/' + str(i * 10) + "-" + str((i+1) * 10)
    for j in range(6):
        video_name = video_dir + str(i * 10) + "-" + str((i+1) * 10) + "/"+ str(i * 10) + " " + str(j)
        video_to_frames(video_name + '.mp4', video_path, j)
    print("finish" + str(i*10) + "folder")
