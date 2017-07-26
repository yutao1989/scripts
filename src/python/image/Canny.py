#! /usr/bin/python3

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import sys
import warnings
from scipy import signal
from scipy import misc
from collections import deque
from Constants import *

#Size of image
#y_length = len(img)
#x_length = len(img[0])
x_length = None
y_length = None

#Basic Util functions
def display(array):
    plt.imshow(array, cmap = plt.get_cmap('gray'))
    plt.show()

def sign(x):
    if x > 0:
        return 1
    if x == 0:
        return 0
    if x < 0:
        return -1

#Threshold for hysteresis
high_threshold = 140
low_threshold = 75

#==========================================================================#
#STEPS ONE and TWO -> Converts to a smooth Black and White image 

def isColor(img):
    if type(img[0][0]) is np.uint8:
        return False
    return True

def rgb2gray(rgb):
    if isColor(rgb):
        return np.dot(rgb[...,:3], [0.299, 0.587, 0.114])
    return rgb

def gaussianSmoothMask(array):
    Kernel = np.divide(gaussianSmoothMask_Kernel, 115.)
    return signal.convolve2d(array, Kernel, boundary='symm', mode='same')

#==========================================================================#


#==========================================================================#
#STEP THREE -> Calculates the gradient at each pixel. The scalar value of the
#gradient is stores in one array and the direction in another
def verticalEdges(array):
    return signal.convolve2d(array, vertical_sobel_mask,boundary='symm', mode='same')

def horizontalEdges(array):
    return signal.convolve2d(array, horizontal_sobel_mask,boundary='symm', mode='same')

''' It is important to remember here, that the horizontal sobel mask finds vertical gradients
and the vertical sobel mask finds horizontal gradients, so when inputting do not forget
to switch them'''
def computeDirection(verticalGradient, horizontalGradient):
    
    if (horizontalGradient == 0):
        slope = infinity * sign(verticalGradient)
    else:
        slope = verticalGradient/horizontalGradient


    if (slope <= smallSlope and slope >= -smallSlope):
        return W
    elif (slope > smallSlope and slope < bigSlope):
        return NE
    elif (slope < -smallSlope and slope > -bigSlope):
        return SE
    elif (slope >= bigSlope):
        return N
    else:
        return S

def combineGradients(vertical_edges, horizontal_edges):
    y_counter = 0
    gradient_array = np.zeros((y_length, x_length))
    direction_array = np.zeros((y_length, x_length, 2))
    while(y_counter < y_length):
        x_counter = 0
        while(x_counter < x_length):
            v_value = vertical_edges[y_counter][x_counter]
            h_value = horizontal_edges[y_counter][x_counter]
            gradient_array[y_counter][x_counter] = np.sqrt(v_value**2 + h_value**2)
            direction_array[y_counter][x_counter] = computeDirection(h_value, v_value)
            x_counter += 1
        y_counter += 1
    return gradient_array , direction_array

def computeGradients(array):
    vertical_edges = verticalEdges(array)
    horizontal_edges = horizontalEdges(array)
    return combineGradients(vertical_edges, horizontal_edges)

#==========================================================================#



#==========================================================================#
#STEP4 -> Suppresses pixels that are not their local maximum

def localMaximum(x, y, gradients, step):
    x_step = step[0]
    y_step = step[1]
    localValue = gradients[y][x]
    if (outOfBounds(x + x_step, y + y_step) or outOfBounds(x - x_step, y - y_step)):
        return False
    elif (localValue > gradients[y + y_step][x + x_step] and localValue > gradients[y - y_step][x -x_step]):
        return True
    return False

def outOfBounds(x, y):
    if (x < 0 or x >= x_length):
        return True
    elif (y < 0 or y >= y_length):
        return True
    return False


def nonMaximumSuppress(gradients, directions):
    suppressed_array = np.zeros((y_length, x_length))
    y_counter = 0
    while(y_counter < y_length):
        x_counter = 0
        while(x_counter < x_length):
            step = directions[y_counter][x_counter]
            if (localMaximum(x_counter, y_counter, gradients, step)):
                suppressed_array[y_counter][x_counter] = gradients[y_counter][x_counter]
            x_counter += 1
        y_counter += 1
    return suppressed_array
#==========================================================================#




#==========================================================================#
#STEP5 -> Hysteresis Thresholding: Connects gaps in edges and removes unwanted pixels

def hysteresisThreshold(array):
    determineThreshold(array)
    edgeConnected = connectEdge(array)
    final = finishImage(edgeConnected)
    return final

def connectEdge(array):
    y = 0
    while (y < y_length):
        x = 0
        while (x < x_length):
            coordinate = (x,y)
            if not coordinate in visited:
                value = array[y][x]
                if highValue(value):
                    array = visit(x, y, array)
            x += 1
        y += 1
    return array

def visit(x, y, array):
    if not outOfBounds(x, y):
        visited.add((x,y))
        array[y][x] = white
        fringe = deque([])
        for child in getChildren(x,y):
            fringe.appendleft(child)
        while not len(fringe) == 0:
            next = fringe.pop()
            nx = next[0]
            ny = next[1]
            value = array[ny][nx]
            if highValue(value):
                array[ny][nx] = white
                for child in getChildren(nx, ny):
                    fringe.appendleft(child)
            elif vibratingPixel(value):
                array[ny][nx] = white
                for child in getChildren(nx, ny):
                    fringe.appendleft(child)
    return array

def getChildren(x, y):
    children = []
    for dx, dy in Directions:
        newy = y + dy
        newx = x + dx
        newCoor = (newx,newy)
        if not outOfBounds(newx, newy) and not newCoor in visited:
            children += [newCoor]
            visited.add(newCoor)
    return children

def backgroundPixelRemove(value):
    if not value == white:
        return black
    return white

finishImage = np.vectorize(backgroundPixelRemove)

def vibratingPixel(value):
    if (value > low_threshold and value <= high_threshold):
        return True
    return False

def highValue(value):
    if (value > high_threshold):
        return True
    return False


''' A simpler thresholding function '''
def genThreshold(array):
    y = 0
    while (y < y_length):
        x = 0
        while (x < x_length):
            value = array[y][x]
            if highValue(value):
                array[y][x] = white
            else:
                array[y][x] = black
            x += 1
        y += 1
    return array

def determineThreshold(array):
    mean = np.mean(array)
    std = np.std(array)
    high_threshold = mean + std
    low_threshold = mean - std
#==========================================================================#

def performEdgeDetection(img):
    global y_length,x_length
    y_length = len(img)
    x_length = len(img[0])
    #Converts all images to Black and White
    img = rgb2gray(img) 

    # Smooths out noise in image   
    fuzzy = gaussianSmoothMask(img)

    #Calculates the gradients for each pixel in the image
    gradients, directions = computeGradients(fuzzy)

    #Suppresses all pixels that are not local maximums
    suppressed = nonMaximumSuppress(gradients, directions)

    #Connects gaps in edges and finishes up the look of the final image
    return hysteresisThreshold(suppressed)

if "__main__" == __name__:
    path = sys.argv[1]
    img = misc.imread(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        print("Note: Depending on the size of your image, this may take some time. ")
        display(performEdgeDetection(img))
