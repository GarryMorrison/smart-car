#######################################################################
# calculate similarity of two images
#
# Author: Garry Morrison
# email: garry.morrison _at_ gmail.com
# Date: 26/4/2018
# Update: 26/4/2018
# Copyright: GPLv3
#
# Usage: python3 image-simm.py image1.png image2.png
#
#######################################################################

import sys
import numpy as np
import cv2


def image_simm_unscaled(im1, im2):
    # convert all to float64:
    fim1 = np.float64(im1)
    fim2 = np.float64(im2)

    wf = np.sum(np.absolute(fim1))
    wg = np.sum(np.absolute(fim2))
    wfg = np.sum(np.absolute(fim1 - fim2))

    if wf == 0 and wg == 0:
        return 0
    return (wf + wg - wfg) / (2 * max(wf, wg))


def image_simm_scaled(im1, im2):
    # convert all to float64:
    fim1 = np.float64(im1)
    fim2 = np.float64(im2)

    s1 = np.sum(fim1)
    s2 = np.sum(fim2)

    if s1 == 0 or s2 == 0:
        return 0

    # wfg = sum(abs(f[k]/s1 - g[k]/s2) for k in range(the_len))
    wfg = np.sum(np.absolute(fim1 / s1 - fim2 / s2))

    return (2 - wfg) / 2


if __name__ == '__main__':
    img_codec = cv2.IMREAD_COLOR
    try:
        filename1 = sys.argv[1]
        filename2 = sys.argv[2]
        src1 = cv2.imread(filename1, img_codec)
        src2 = cv2.imread(filename2, img_codec)

    except:
        print("Can't open image's!")
        sys.exit(-1)

    r = image_simm(src1, src2)
    print('image simm:', str(r))

