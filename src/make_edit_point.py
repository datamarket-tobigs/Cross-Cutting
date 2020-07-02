from src.fastRCNN_model import fast_RCNN_model

model = fast_RCNN_model()
file = "../img/0-10/5 video 210.png"
model.write_file_name(file_name=file)
a, b, c = model.run_model()
print(a)
model.visualize()