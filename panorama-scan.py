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
# so best to run the stitch code elsewhere.
# https://kushalvyas.github.io/stitching.html
# https://github.com/kushalvyas/Python-Multiple-Image-Stitching
#
#
# Author: Garry Morrison
# email: garry.morrison _at_ gmail.com
# Date: 27/4/2018
# Update: 29/4/2018
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
# import cv2
import os
import pygame


# beep to indicated start and end of panorama-scan:
beep = True


# try to set up smbus:
# (this will only work on the raspberry pi)
try:
    import smbus
    smbus_address = 0x18  # default address
    bus = smbus.SMBus(1)
    bus.open(1)
    have_smbus = True
except ImportError:
    print('failed to import smbus')
    sys.exit(-1)


# set up camera using opencv:
# now deprecated, instead we are using pygame, since it is installed by default on the raspberry pi.
# cap = cv2.VideoCapture(0)

# start up pygame:
pygame.init()

# set the desired camera size here:
# camera_size = (320, 240)
camera_size = (640, 480)

# camera controls:
hflip = True
vflip = True

# try to set up the camera using pygame:
try:
    import pygame.camera
    pygame.camera.init()
    camera_list = pygame.camera.list_cameras()
    if not camera_list:
        print('failed to find a camera')
        sys.exit(-1)
    else:
        cam = pygame.camera.Camera(camera_list[0], camera_size)
        cam.start()
        cs = cam.get_size()
        print('camera size: %s' % str(cs))
except ImportError:
    print('failed to find a camera')
    sys.exit(-1)

# number of images to average over:
count = 20
# count = 1

# sleep time, in seconds, between changing angle and taking a photo:
SLEEP_TIME = 1

# min similarity for image to be considered valid during image averaging:
IMAGE_SIMILARITY = 0.75

# panorama settings:
min_angle = 0
max_angle = 180
step_angle = 5


# define IO constants:
CMD_SERVO1 = 0
CMD_SERVO2 = 1
CMD_SERVO3 = 2
CMD_SERVO4 = 3
CMD_BUZZER = 8
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
# NB: opencv version. ie, we haven't written a pygame version of this function.
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


# returns the image similarity of two images:
# 1 for exact match,
# 0 for completely distinct
# values in between otherwise
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


# this still has some minor ghosting!
def create_simm_average_camera_image(count):
    rot_img = []
    for _ in range(count):
        img = cam.get_image()
        img = pygame.transform.scale(img, camera_size)
        img = pygame.transform.flip(img, hflip, vflip)
        img = pygame.surfarray.array3d(img)
        rot_img.append(img)

    # convert all to float64:
    float_img = [np.float64(i) for i in rot_img]

    # find average of similar images:
    mean_img = float_img[-1]
    i = 1
    for k in range(1, count):
        tmp_img = float_img[k]
        # r = image_simm(float_img[0], tmp_img)
        r = image_simm(mean_img, tmp_img)
        if r > IMAGE_SIMILARITY:                  # currently 80% similarity. Maybe another value would work better?
            mean_img += tmp_img
            i += 1
    mean_img /= i
    print('we averaged %s images' % i)

    # Convert back to uint8:
    int_mean_img = np.uint8(np.clip(mean_img, 0, 255))

    # convert back to pygame surface:
    frame = pygame.surfarray.make_surface(int_mean_img)

    return frame


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('please provide a destination directory for the images')
        sys.exit(-1)
    dest_dir = sys.argv[1]

    # check if dest_dir exists, if not create it:
    if not os.path.exists(dest_dir):
        print("Creating " + dest_dir + " directory.")
        os.makedirs(dest_dir)

    # now find subdirectories:
    sub_dirs = [d for d in os.listdir(dest_dir) if os.path.isdir(dest_dir + '/' + d)]
    print('sub_dirs: %s' % sub_dirs)

    # find max integer named subdirectory:
    max_int_sub_dir = 0
    for d in sub_dirs:
        try:
            int_d = int(d)
            max_int_sub_dir = max(max_int_sub_dir, int_d)
        except ValueError as e:
            print('sub_dirs exception: %s' % e)
            pass

    # increment, to next empty slot:
    max_int_sub_dir += 1

    # finally, we have our full destination directory:
    dest_dir += '/' + str(max_int_sub_dir)

    # check if full dest_dir exists, if not create it:
    if not os.path.exists(dest_dir):
        print("Creating " + dest_dir + " directory.")
        os.makedirs(dest_dir)

    # test our directory selection code works, then exit:
    # sys.exit(0)

    # beep on startup:
    if beep:
        write_reg(CMD_BUZZER, 1000)
        time.sleep(0.2)
        write_reg(CMD_BUZZER, 0)

    # sleep 30s
    time.sleep(30)

    # warn about to start scan:
    if beep:
        write_reg(CMD_BUZZER, 2000)
        time.sleep(0.2)
        write_reg(CMD_BUZZER, 0)

    # sleep 5s
    time.sleep(5)

    # panorama settings:
    # min_angle = 0
    # max_angle = 180
    # step_angle = 5
    for angle in range(min_angle, max_angle + step_angle, step_angle):
        angle = int(constrain(angle, 0, 180))
        print('angle: %s' % angle)
        write_servo(CMD_SERVO2, 180 - angle)

        # let the camera warm up to current angle:
        time.sleep(SLEEP_TIME)
        img = create_simm_average_camera_image(count)
        ## cv2.imshow(str(angle), img)
        # cv2.imwrite(dest_dir + '/' + str(angle) + '.png', img)
        pygame.image.save(img, dest_dir + '/' + str(angle) + '.png')

    # return camera to 90 degree position:
    write_servo(CMD_SERVO2, 90)

    # beep on finish:
    if beep:
        write_reg(CMD_BUZZER, 1000)
        time.sleep(0.2)
        write_reg(CMD_BUZZER, 0)

    # tidy up and quit:
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
