import numpy as np

#Infinities used to compare slopes
negative_infinity = float("-inf")
infinity = float("inf")

#Slope constants used when calculating direction
smallSlope = .414
bigSlope = 2.414

#Color Constants
black = 0
white = 255

#Kernels used for convolutions
gaussianSmoothMask_Kernel = np.array([[2, 4,  5,  4,  2],
									  [4, 9,  12, 9,  4],
									  [5, 12, 15, 12, 5],
									  [4, 9,  12, 9,  4],
									  [2, 4,  5,  4,  2]])

vertical_sobel_mask = np.array([[-1, 0, 1],
								[-2, 0, 2],
								[-1, 0, 1]])

horizontal_sobel_mask = np.array([[-1, -2, -1],
								  [0,   0,  0],
								  [1,   2,  1]])

#A set of visited nodes that keeps BFS from looping infinitely
visited = set()

#Directions
S  = (0, -1)
SE = (1, -1)
E  = (1, 0)
NE = (1, 1)
N  = (0, 1)
NW = (-1, 1)
W  = (1, 0)
SW = (1, -1)

Directions = set([S, SE, E, NE, N, NW, W, SW])