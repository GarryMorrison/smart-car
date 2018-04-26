#######################################################################
# image edge-enhance using opencv filter2D
#
# Author: Garry Morrison
# email: garry.morrison _at_ gmail.com
# Date: 26/4/2018
# Update: 26/4/2018
# Copyright: GPLv3
#
# Usage: python3 edge-enhance.py image.png
#
#######################################################################

import sys
import time
import numpy as np
import cv2

iterations = 10


def massage_pixel(x):
    if x < 0:
        x = 0
#    x *= 20
#    x *= 30
    x *= 3.5
    x = int(x)
    if x > 255:
        x = 255
    return 255 - x


def main(argv):
    filename = "ave-img.png"
    img_codec = cv2.IMREAD_COLOR
    if argv:
        filename = sys.argv[1]
        if len(argv) >= 2 and sys.argv[2] == "G":
            img_codec = cv2.IMREAD_GRAYSCALE

    src = cv2.imread(filename, img_codec)
    if src is None:
        print("Can't open image [" + filename + "]")
        print("Usage:")
        print("mat_mask_operations.py [image_path] [G -- grayscale]")
        return -1

    cv2.namedWindow("Input", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("Output", cv2.WINDOW_AUTOSIZE)
    cv2.imshow("Input", src)

    kernel = np.array([[1/16, 1/16, 1/16],
                       [1/16, 1/2, 1/16],
                       [1/16, 1/16, 1/16]], np.float32)  # kernel should be floating point type

    dst1 = cv2.filter2D(src, -1, kernel)
    # ddepth = -1, means destination image has depth same as input image

    # now do it iterations times:
    for _ in range(iterations - 1):
        dst1 = cv2.filter2D(dst1, -1, kernel)

    # now subtract original image:
    dst = cv2.subtract(dst1, src)

    # now massage the pixels:
    height, width, depth = dst.shape
    for i in range(0, height):
        for j in range(0, width):
            for k in range(0, depth):
                dst[i, j, k] = massage_pixel(dst[i, j, k])

    # now smooth once more:
    # dst = cv2.filter2D(dst, -1, kernel)

    cv2.imshow("Output", dst)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
