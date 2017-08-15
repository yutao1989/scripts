#! /usr/bin/python3

from skimage import io
import numpy as np
from scipy import signal
import math

sqrt2 = math.sqrt(2)
horizontal_sobel_mask = np.array([[-1, 0, 1],
                                [-sqrt2, 0, sqrt2],
                                [-1, 0, 1]])
vertical_sobel_mask = horizontal_sobel_mask.transpose()
smallSlope = .414
bigSlope = 2.414

NW,N,NE,W,E,SW,S,SE = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
nbs = [NW,N,NE,W,E,SW,S,SE]

def convert_gray(img):
    if type(img[0][0]) == np.uint8:
        return img
    else:
        return np.dot(img[...,:3],[0.299, 0.587, 0.114])

def get_direction(slope, values):
    if slope < smallSlope:
        return values[0]
    elif slope > bigSlope:
        return values[2]
    else:
        return values[1]

def computeDirection(verticalGradient, horizontalGradient):
    if horizontalGradient == 0:
        return N if verticalGradient > 0 else (S if verticalGradient < 0 else (0, 0))
    elif verticalGradient == 0:
        return E if horizontalGradient > 0 else W
    else:
        triple = []
        if verticalGradient > 0:
            if horizontalGradient > 0:
                triple = [E,NE,N]
            else:
                triple = [W,NW,N]
        else:
            if horizontalGradient > 0:
                triple = [E,SE,S]
            else:
                triple = [W,SW,S]
        return get_direction(abs(verticalGradient/horizontalGradient), triple)

def outOfBounds(p,r):
    if isinstance(r,tuple):
        r = [(0,0),r]
    if (r[0][0] > p[0] or p[0] >= r[1][0]):
        return True
    elif (r[0][1] > p[1] or p[1] >= r[1][1]):
        return True
    return False

def localMaximum(p, gradients, step):
    localValue = gradients[p[0]][p[1]]
    shape = gradients.shape
    rate = .6
    if (outOfBounds((p[0]+step[0], p[1]+step[1]),shape) or outOfBounds((p[0]-step[0], p[1]-step[1]),shape)):
        return False
    elif localValue >= gradients[p[0]+step[0]][p[1]+step[1]] and localValue >= gradients[p[0]-step[0]][p[1]-step[1]]:
        if localValue*rate > gradients[p[0]+step[0]][p[1]+step[1]] or localValue*rate > gradients[p[0]-step[0]][p[1]-step[1]]:
            return True
        else:
            return False
    return False

def calc_gradient(img):
    hg = signal.convolve2d(img, horizontal_sobel_mask,boundary='symm', mode='same')
    vg = signal.convolve2d(img, vertical_sobel_mask,boundary='symm', mode='same')
    shape = img.shape
    directions = np.ndarray(shape+(2,))
    gradients = np.ndarray(shape)
    for i in range(shape[0]):
        for j in range(shape[1]):
            directions[i][j] = computeDirection(vg[i][j],hg[i][j])
            gradients[i][j] = math.sqrt(vg[i][j]**2+hg[i][j]**2)

    mxm = np.zeros(shape,"uint8")
    for i in range(shape[0]):
        for j in range(shape[1]):
            d = directions[i][j]
            if localMaximum((i,j),gradients, d):
                mxm[i][j] = 255
    show_img(mxm)
    return gradients,directions

def judge_sudoku(img,p,isMax=False):
    shape = img.shape
    lst = [(p,img[p[0]][p[1]])]
    for d in nbs:
        nx = p[0]+d[0]
        ny = p[1]+d[1]
        if not outOfBounds((nx,ny),shape):
            lst.append(((nx,ny),img[nx][ny]))
    lst.sort(key=lambda o:o[1])
    if abs(lst[0][1]-lst[-1][1]) > 150:
        sqs = 0
        sm = 0
        idx = 0
        v = 0
        #while idx < len(lst) and lst[idx][1] <= img[p[0]][p[1]]:
        while idx < len(lst) and v < 30:
            sqs += lst[idx][1]**2
            sm += lst[idx][1]
            idx += 1
            m = sm/idx
            v = sqs -2*sm*m+m**2
        if idx < 4:
            return True
        else:
            return False
    else:
        return False

def visit_img(img):
    shape = img.shape
    nmg = np.zeros(shape)
    for i in range(shape[0]):
        for j in range(shape[1]):
            if judge_sudoku(img,(i,j)):
                nmg[i][j] = 255
    return nmg

def detect_edge(fname):
    img = io.imread(fname)
    img = convert_gray(img)
    sub = img[92:136,130:170]
    #g,d = calc_gradient(sub)
    sub = visit_img(sub)
    #display_array(g)
    show_img(sub)

def display_array(array):
    print("\n".join(["\t".join([str(o2) for o2 in o1]) for o1 in array]))

def show_img(img,name=None):
    shape = img.shape
    nmg = np.ndarray(shape,"uint8")
    for i in range(shape[0]):
        for j in range(shape[1]):
            nmg[i][j] = int(img[i][j])
    if name is None:
        io.imshow(nmg)
        io.show()
    else:
        io.imsave(name,nmg)

if "__main__" == __name__:
    detect_edge("data/comic.jpg")
