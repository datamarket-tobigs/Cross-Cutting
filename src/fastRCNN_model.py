import gluoncv
from matplotlib import pyplot as plt
from gluoncv import model_zoo, data, utils

class fast_RCNN_model():

    def __init__(self):
        self.model = model_zoo.get_model('faster_rcnn_resnet50_v1b_voc', pretrained=True)
        self.file_name = ""
        self.x = None
        self.orig_img = None
        self.box_ids, self.scores, self.bboxes = None, None, None

    def write_file_name(self, file_name):
        self.file_name = file_name
        # im_fname = "../img/0-10/5 video 210.png"

    def run_model(self):
        self.x, self.orig_img = data.transforms.presets.rcnn.load_test(self.file_name)
        self.box_ids, self.scores, self.bboxes = self.model(self.x)
        return self.box_ids, self.scores, self.bboxes

    def visualize(self):
        ax = utils.viz.plot_bbox(self.orig_img, self.bboxes[0], self.scores[0], self.box_ids[0], class_names = self.model.classes)
        plt.show()