from sewar.full_ref import ssim, psnr
import cv2
import os

class evaluation():
    def __init__(self, img_dir):
        self.img_dir = img_dir
        self.method = os.listdir(img_dir)
        self.ssim_result = []
        self.psnr_result = []

    def save_to_txt(self, result, f_name):
        f = open(f_name + '.txt', 'w')
        f.write(result)
        f.close()

    def calculate_ssim_psnr(self, img1, img2):
        self.input1 = cv2.imread(img1)
        self.input2 = cv2.imread(img2)

        self.ssim_result.append(ssim(self.input1, self.input2))
        self.psnr_result.append(psnr(self.input1, self.input2))

    def run(self):
        for method in self.method:
            self.singer_list = os.listdir(self.img_dir + '/' + method)
            for singer in self.singer_list:
                print("final dir: " + self.img_dir + '/' + method + '/' + singer)

a = evaluation('img/')
a.run()