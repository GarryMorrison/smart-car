#######################################################################
# image edge-enhance using opencv filter2D
# with help from the code here:
# https://docs.opencv.org/master/d7/d37/tutorial_mat_mask_operations.html
#
# Author: Garry Morrison
# email: garry.morrison _at_ gmail.com
# Date: 26/4/2018
# Update: 4/5/2018
# Copyright: GPLv3
#
# Usage: python3 edge-enhance.py image.png
#
#######################################################################

import sys
import numpy as np
import cv2

iterations = 10


def massage_pixel(x):
    if x < 0:
        x = 0
#    x *= 20
    x *= 30
#    x *= 3.5
    x = int(x)
    if x > 255:
        x = 255
    return 255 - x


def main(argv):
    filename = "ave-img.png"
    img_codec = cv2.IMREAD_COLOR
    grayscale = False
    if argv:
        filename = sys.argv[1]
        if len(argv) >= 2 and sys.argv[2] == "--grayscale":
            img_codec = cv2.IMREAD_GRAYSCALE
            grayscale = True

    src = cv2.imread(filename, img_codec)
    if src is None:
        print("Can't open image [" + filename + "]")
        print("Usage:")
        print("edge-enhance.py image_path [--grayscale]")
        return -1

    cv2.namedWindow("Input", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("Output", cv2.WINDOW_AUTOSIZE)
    cv2.imshow("Input", src)

    kernel = np.array([[1/16, 1/16, 1/16],
                       [1/16, 1/2, 1/16],
                       [1/16, 1/16, 1/16]], np.float32)

    dst1 = cv2.filter2D(src, -1, kernel)
    # ddepth = -1, means destination image has depth same as input image

    # now do it iterations times:
    for _ in range(iterations - 1):
        dst1 = cv2.filter2D(dst1, -1, kernel)

    # now subtract original image:
    dst = cv2.subtract(dst1, src)

    # now massage the pixels:
    if grayscale:
        height, width = dst.shape
        for i in range(0, height):
            for j in range(0, width):
                dst[i, j] = massage_pixel(dst[i, j])
    else:
        height, width, depth = dst.shape
        for i in range(0, height):
            for j in range(0, width):
                for k in range(0, depth):
                    dst[i, j, k] = massage_pixel(dst[i, j, k])

    # now smooth once more:
    # dst = cv2.filter2D(dst, -1, kernel)

    cv2.imshow("Output", dst)

    # save the result:
    filename, ext = filename.rsplit('.', 1)
    if grayscale:
        filename = filename + "--edge-enhanced-" + str(iterations) + "--gray." + ext
    else:
        filename = filename + "--edge-enhanced-" + str(iterations) + "." + ext
    print('dest:', filename)

    # save output:
    cv2.imwrite(filename, dst)

    # tidy up and close:
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
