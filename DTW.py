from __future__ import print_function
import numpy as np
import librosa
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

path1 = './audio/ohmygirl1.wav'
path2 = './audio/ohmygirl2.wav'
x_1, fs = librosa.load(path1)
x_2, fs = librosa.load(path2)


if(len(x_1)>len(x_2)):
    temp = x_1
    x_1 = x_2
    x_2 = x_1
  
#DTW
path = fastdtw(x_1, x_2)[1]
B_ = []
for i in range(len(x_1)):
    B_.append(x_1[path[i][1]])
print("distance: ", euclidean(x_1, B_))

librosa.output.write_wav('./test0_0.wav', x_1[11:], fs)
librosa.output.write_wav('./test0_1.wav', x_2, fs)
librosa.output.write_wav('./test1_0.wav', x_1, fs)
librosa.output.write_wav('./test1_1.wav', x_2[11:], fs)