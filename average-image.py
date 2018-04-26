#######################################################################
# use numpy to average camera images
#
# Author: Garry Morrison
# email: garry.morrison _at_ gmail.com
# Date: 26/4/2018
# Update: 26/4/2018
# Copyright: GPLv3
#
# Usage: python3 average-camera-images.py
#
#######################################################################

import numpy as np
import cv2

count = 20

cap = cv2.VideoCapture(0)

# create a list of first count frames:
img = [cap.read()[1] for i in range(count)]

# rotate images:
rot_img = [cv2.flip(i, -1) for i in img]

# convert all to float64:
float_img = [np.float64(i) for i in rot_img]

# find the average:
mean_img = float_img[0]
for k in range(1, count):
    mean_img += float_img[k]
mean_img /= count

# Convert back to uint8:
int_mean_img = np.uint8(np.clip(mean_img, 0, 255))

# show output:
cv2.imshow('initial', rot_img[0])
cv2.imshow('average', int_mean_img)

# save output:
cv2.imwrite('raw-image.png', rot_img[0])
cv2.imwrite('ave-image.png', int_mean_img)

# tidy up and quit:
cv2.waitKey(0)
cv2.destroyAllWindows()
