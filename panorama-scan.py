#######################################################################
# use the smart car to make a collection of images
# that can be stitched into a panorama
# well, that is the idea. The stitching part isn't working so great.
# eg, out of memory error, and then a divide by zero!
#
# stitching code here:
# https://github.com/cbuntain/stitcher
#
# alternately:
# https://www.pyimagesearch.com/2016/01/11/opencv-panorama-stitching/
#
# or maybe this:
# yup, looks like this one might actually work!
# though it is having out-of-memory errors on the raspberry pi
# so best to run this code elsewhere.
# https://kushalvyas.github.io/stitching.html
# https://github.com/kushalvyas/Python-Multiple-Image-Stitching
#
#
# Author: Garry Morrison
# email: garry.morrison _at_ gmail.com
# Date: 27/4/2018
# Update: 27/4/2018
# Copyright: GPLv3
#
# Usage:
#    set car in appropriate location
#    then run: python3 panorama-scan.py dest_dir
#
#######################################################################

import numpy as np
import time
import sys
import cv2
import os


# try to set up smbus:
# (this will only work on the raspberry pi, so if it fails we drop back to dummy mode)
try:
    import smbus
    smbus_address = 0x18  # default address
    bus = smbus.SMBus(1)
    bus.open(1)
    have_smbus = True
except ImportError:
    print('failed to import smbus, dummy mode on')
    have_smbus = False


# set up camera:
cap = cv2.VideoCapture(0)

# number of images to average over:
count = 20
# count = 1

# panorama settings:
min_angle = 0
max_angle = 180
step_angle = 5


# define IO constants:
CMD_SERVO1 = 0
CMD_SERVO2 = 1
CMD_SERVO3 = 2
CMD_SERVO4 = 3
SERVO_MAX_PULSE_WIDTH = 2500
SERVO_MIN_PULSE_WIDTH = 500


def constrain(val, min_val, max_val):
    val = max(val, min_val)
    val = min(val, max_val)
    return val


def num_map(value, fromLow, fromHigh, toLow, toHigh):
    return (toHigh-toLow)*(value-fromLow) / (fromHigh-fromLow) + toLow


def write_reg(cmd, value):
    try:
        value = int(value)
        bus.write_i2c_block_data(smbus_address, cmd, [value >> 8, value & 0xff])
        time.sleep(0.001)
    except Exception as e:
        print('write_reg exception: %s' % e)


def write_servo(cmd, value):
    try:
        value = constrain(value, 0, 180)
        value = int(num_map(value, 0, 180, SERVO_MIN_PULSE_WIDTH, SERVO_MAX_PULSE_WIDTH))
        write_reg(cmd, value)
    except Exception as e:
        print('write_servo exception: %s' % e)


# assumes, for now, there is no movement at all while trying to take the average:
# hrmmm.. still has ghost effect. Need to filter using image-simm()
def create_average_camera_image(count):
    # let the camera warm up to current angle:
    time.sleep(10)

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

    return int_mean_img


def image_simm(im1, im2):
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


def create_simm_average_camera_image(count):
    # let the camera warm up to current angle:
    time.sleep(10)

    # create a list of first count frames:
    img = [cap.read()[1] for i in range(count)]

    # rotate images:
    rot_img = [cv2.flip(i, -1) for i in img]

    # convert all to float64:
    float_img = [np.float64(i) for i in rot_img]

    # find average of similar images:
    mean_img = float_img[0]
    i = 1
    for k in range(1, count):
        tmp_img = float_img[k]
        r = image_simm(mean_img, tmp_img)
        if r > 0.80:
            mean_img += tmp_img
            i += 1
    mean_img /= i

    # find the average:
    #mean_img = float_img[0]
    #for k in range(1, count):
    #    mean_img += float_img[k]
    #mean_img /= count

    # Convert back to uint8:
    int_mean_img = np.uint8(np.clip(mean_img, 0, 255))

    return int_mean_img


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('please provide a destination directory for the images')
        sys.exit(-1)
    dest_dir = sys.argv[1]

    # check if dest_dir exists, if not create it:
    if not os.path.exists(dest_dir):
        print("Creating " + dest_dir + " directory.")
        os.makedirs(dest_dir)

    # panorama settings:
    # min_angle = 0
    # max_angle = 180
    # step_angle = 10
    for angle in range(min_angle, max_angle + step_angle, step_angle):
        angle = int(constrain(angle, 0, 180))
        print(angle)
        write_servo(CMD_SERVO2, angle)
        time.sleep(2)
        # img = create_average_camera_image(count)
        img = create_simm_average_camera_image(count)
        # cv2.imshow(str(angle), img)
        cv2.imwrite(dest_dir + '/' + str(angle) + '.png', img)

    # return camera to 90 degree point:
    write_servo(CMD_SERVO2, 90)

    # tidy up and quit:
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()