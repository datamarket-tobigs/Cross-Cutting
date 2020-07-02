from src.fastRCNN_model import fast_RCNN_model

img_dir = "../img/"
subclip_dir = [str(i*10)+"-"+str((i+1)*10)+"/" for i in range(23)]
video_num = [str(i) + " video " for i in [0, 1, 4, 5]]
frame_num = [str(i*10)+".png" for i in range(27)]
file = img_dir + subclip_dir[0] + video_num[0] + frame_num[0]

model = fast_RCNN_model()

model.write_file_name(file_name=file)
box_id, box_score, box_val = model.run_model()

box_val = box_val[0]
print(box_val.getitem)