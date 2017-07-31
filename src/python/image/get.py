#! /usr/bin/python

import sys
sys.path.insert(0,'/usr/local/lib/python2.7/site-packages')
import cv2
from skimage import io

if "__main__" == __name__:
    img = io.imread("data/text2.jpg")
    border = 3
    for line in open("r.txt"):
        parts = [int(o) for o in line.strip().split(" ")]
        #img = cv2.rectangle(img,(parts[1],parts[2]),(parts[3],parts[4]),[255,0,255])
        img = cv2.rectangle(img,(parts[2]-border,parts[1]-border),(parts[4]+border,parts[3]+border),[255,0,255])
    io.imsave("data/get.jpg",img)
    #io.imshow(img)
    #io.show()
