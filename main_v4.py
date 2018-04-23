#######################################################################
# my smart car pygame interface for the raspberry pi
#
# based on the original Freenove code here:
# https://github.com/Freenove/Freenove_Three-wheeled_Smart_Car_Kit_for_Raspberry_Pi/
#
# Author: Garry Morrison
# email: garry.morrison _at_ gmail.com
# Date: 13/4/2018
# Update: 23/4/2018
# Copyright: GPLv3
#
# Usage:
#   Log into the raspberry pi with VNC or XRDP
#   open a terminal
#   run: python3 main_v4.py
#
#######################################################################

import pygame
import sys
import time

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

pygame.init()

# set the desired image/camera size here, and the buttons/sliders will auto adjust to the right positions
# camera_size = (320, 240)
camera_size = (640, 480)
# camera_size = (800, 600)               # works with my new camera, but is slow to update, and makes the GUI slow too.
cx = camera_size[0]
cy = camera_size[1]

# update the image every 25 main event loops:
# we are trying to make the GUI more responsive
# another option is threading, but that depends on if the slow speed is the camera or VNC.
camera_frequency = 25


# try to set up the camera:
# (again, this will only work on the raspberry pi, so if it fails we drop back to a static image)
try:
    import pygame.camera
    pygame.camera.init()
    camera_list = pygame.camera.list_cameras()
    if not camera_list:
        have_camera = False
    else:
        # cam = pygame.camera.Camera(camera_list[0], (320, 240))
        cam = pygame.camera.Camera(camera_list[0], camera_size)
        cam.start()
        cs = cam.get_size()
        print('camera size: %s' % str(cs))
        have_camera = True
except ImportError:
    print('failed to find a camera')
    have_camera = False


# define some colours:
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (200, 200, 200)
GREY2 = (180, 180, 180)
GREY3 = (100, 100, 100)
# RED = (200, 0, 0)
BRIGHT_RED = (255, 0, 0)
GREEN = (0, 200, 0)
BRIGHT_GREEN = (0, 255, 0)
# BLUE = (0, 0, 200)
BRIGHT_BLUE = (0, 0, 255)
ORANGE = (200, 100, 50)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
TRANS = (1, 1, 1)

# define some display constants:
# display_width = 710
# display_height = 560
display_width = 710 - 320 + cx
display_height = 560 - 240 + cy

background_color = WHITE

# define IO constants:
CMD_SERVO1 = 0
CMD_SERVO2 = 1
CMD_SERVO3 = 2
CMD_SERVO4 = 3
CMD_PWM1 = 4
CMD_PWM2 = 5
CMD_DIR1 = 6
CMD_DIR2 = 7
CMD_BUZZER = 8
CMD_IO1 = 9
CMD_IO2 = 10
CMD_IO3 = 11
CMD_SONIC = 12
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
        # value = int(num_map(value, 0, 180, 500, 2500))
        value = constrain(value, 0, 180)
        value = int(num_map(value, 0, 180, SERVO_MIN_PULSE_WIDTH, SERVO_MAX_PULSE_WIDTH))
        write_reg(cmd, value)
    except Exception as e:
        print('write_servo exception: %s' % e)


# initial button and slider code from here:
# http://www.dreamincode.net/forums/topic/401541-buttons-and-sliders-in-pygame/

class Button():
    def __init__(self, txt, location, action_down, action_up, bg=WHITE, fg=BLACK, size=(80, 30), font_name="Verdana", font_size=14):
        self.color = bg  # the static (normal) color
        self.bg = bg  # actual background color, can change on mouseover
        self.fg = fg  # text color
        self.size = size
 
        self.font = pygame.font.SysFont(font_name, font_size)
        self.txt = txt
        self.txt_surf = self.font.render(self.txt, 1, self.fg)
        self.txt_rect = self.txt_surf.get_rect(center=[s//2 for s in self.size])
 
        self.surface = pygame.surface.Surface(size)
        self.rect = self.surface.get_rect(center=location)
 
        self.call_back_down_ = action_down
        self.call_back_up_ = action_up
 
    def draw(self):
        self.mouseover()
 
        self.surface.fill(self.bg)
        pygame.draw.rect(self.surface, BLACK, [0, 0, self.size[0], self.size[1]], 1)
        self.surface.blit(self.txt_surf, self.txt_rect)
        screen.blit(self.surface, self.rect)
 
    def mouseover(self):
        self.bg = self.color
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            self.bg = GREY  # mouseover color
 
    def call_back_down(self):
        color = self.call_back_down_()
        if color is not None:
            self.color = color

    def call_back_up(self):
        color = self.call_back_up_()
        if color is not None:
            self.color = color


class Slider():
    def __init__(self, name, val, maxi, mini, xpos, ypos, action=None):
        self.val = val  # start value
        self.maxi = maxi  # maximum at slider position right
        self.mini = mini  # minimum at slider position left
        self.xpos = xpos - 50 # x-location on screen
        self.ypos = ypos - 20 # y-location on screen
        self.surf = pygame.surface.Surface((100, 50))
        self.hit = False  # the hit attribute indicates slider movement due to mouse interaction
        self.call_back = action

        self.font = pygame.font.SysFont("Verdana", 12)
        # font = pygame.font.SysFont("Trebuchet MS", 12)
        # self.txt_surf = font.render(name, 1, BLACK)
        self.txt_surf = self.font.render(str(self.val), 1, BLACK)
        self.txt_rect = self.txt_surf.get_rect(center=(50, 15))

        # Static graphics - slider background #
        # self.surf.fill((100, 100, 100))
        # pygame.draw.rect(self.surf, GREY, [0, 0, 100, 50], 3)
        # pygame.draw.rect(self.surf, ORANGE, [10, 10, 80, 10], 0)
        # pygame.draw.rect(self.surf, WHITE, [10, 30, 80, 5], 0)
        self.surf.fill(WHITE)
        # pygame.draw.rect(self.surf, WHITE, [0, 0, 100, 50], 3)
        # pygame.draw.rect(self.surf, ORANGE, [10, 10, 80, 10], 0)
        pygame.draw.rect(self.surf, GREY, [10, 30, 80, 5], 0)

        self.surf.blit(self.txt_surf, self.txt_rect)  # this surface never changes

        # dynamic graphics - button surface #
        self.button_surf = pygame.surface.Surface((20, 20))
        self.button_surf.fill(TRANS)
        self.button_surf.set_colorkey(TRANS)
        pygame.draw.circle(self.button_surf, BLACK, (10, 10), 6, 0)
        pygame.draw.circle(self.button_surf, ORANGE, (10, 10), 4, 0)

    def draw(self):
        """ Combination of static and dynamic graphics in a copy of
    the basic slide surface
    """
        # static
        surf = self.surf.copy()

        # dynamic
        # slider value:
        self.surf.fill(WHITE)
        # pygame.draw.rect(self.surf, WHITE, [0, 0, 100, 50], 3)
        pygame.draw.rect(self.surf, GREY, [10, 30, 80, 5], 0)
        self.txt_surf = self.font.render(str(int(self.val)), 1, BLACK)
        self.surf.blit(self.txt_surf, self.txt_rect)

        # slider button:
        pos = (10 + int((self.val - self.mini) / (self.maxi - self.mini) * 80), 33)
        self.button_rect = self.button_surf.get_rect(center=pos)
        surf.blit(self.button_surf, self.button_rect)
        self.button_rect.move_ip(self.xpos, self.ypos)  # move of button box to correct screen position

        # screen
        screen.blit(surf, (self.xpos, self.ypos))

    def move(self):
        """
    The dynamic part; reacts to movement of the slider button.
    """
        self.val = (pygame.mouse.get_pos()[0] - self.xpos - 10) / 80 * (self.maxi - self.mini) + self.mini
        if self.val < self.mini:
            self.val = self.mini
        if self.val > self.maxi:
            self.val = self.maxi
        if self.call_back is not None:
            self.call_back(self.val)


class ActiveMap():
    def __init__(self, name, width, val, maxi, mini, xpos, ypos, action=None):
        self.width = width
        self.val = val  # start value
        self.maxi = maxi  # maximum at slider position right
        self.mini = mini  # minimum at slider position left
        self.xpos = xpos  # x-location on screen
        self.ypos = ypos  # y-location on screen
        # self.surf = pygame.surface.Surface((100, 50))
        self.hit = False  # the hit attribute indicates slider movement due to mouse interaction
        self.call_back = action

        w = self.width
        s = w // 10  # step size
        c = w // 2  # center
        self.surface = pygame.surface.Surface((w + 50, w + 50))
        # self.rect = self.surface.get_rect()
        self.rect = pygame.Rect(xpos, ypos, xpos + w, ypos + w)
        # print(self.rect)
        self.surface.fill(WHITE)
        pygame.draw.rect(self.surface, GREY, [0, 0, w, w], 0)
        pygame.draw.rect(self.surface, BLACK, [0, 0, w, w], 1)
        pygame.draw.rect(self.surface, BLACK, [s, s, w - 2 * s, w - 2 * s], 1)
        pygame.draw.rect(self.surface, BLACK, [2 * s, 2 * s, w - 4 * s, w - 4 * s], 1)
        pygame.draw.rect(self.surface, BLACK, [3 * s, 3 * s, w - 6 * s, w - 6 * s], 1)
        pygame.draw.rect(self.surface, BLACK, [4 * s, 4 * s, w - 8 * s, w - 8 * s], 1)
        pygame.draw.line(self.surface, BLACK, (0, c), (w, c), 1)
        pygame.draw.line(self.surface, BLACK, (c, 0), (c, w), 1)

        # button surface:
        self.button_surf = pygame.surface.Surface((20, 20))
        self.button_surf.fill(TRANS)
        self.button_surf.set_colorkey(TRANS)
        pygame.draw.circle(self.button_surf, BLACK, (10, 10), 6, 0)
        pygame.draw.circle(self.button_surf, ORANGE, (10, 10), 4, 0)

        # define our font for the horizontal and vertical values:
        self.font = pygame.font.SysFont("Verdana", 16)

        # horizontal value surface:
        self.horizontal_surf = pygame.surface.Surface((20, 20))
        self.txt_surf_x = self.font.render(str(int(self.val[0])), 1, BLACK)
        self.txt_rect_x = self.txt_surf_x.get_rect(center=(self.width // 2, self.width + 20))

        # vertical value surface:
        self.vertical_surf = pygame.surface.Surface((20, 20))
        self.txt_surf_y = self.font.render(str(int(self.val[1])), 1, BLACK)
        self.txt_rect_y = self.txt_surf_y.get_rect(center=(self.width + 30, self.width // 2))

    def draw(self):
        # static
        surface = self.surface.copy()

        # current-location button:
        # num_map(value, fromLow, fromHigh, toLow, toHigh)
        xpos = num_map(self.val[0], 0, 180, 0, self.width)
        ypos = num_map(self.val[1], 0, 180, 0, self.width)
        self.button_rect = self.button_surf.get_rect(center=(xpos, ypos))
        surface.blit(self.button_surf, self.button_rect)
        self.button_rect.move_ip(self.xpos, self.ypos)  # move of button box to correct screen position

        # horizontal value:
        surface.blit(self.txt_surf_x, self.txt_rect_x)

        # vertical value:
        surface.blit(self.txt_surf_y, self.txt_rect_y)

        # screen
        screen.blit(surface, (self.xpos, self.ypos))

    def move(self):
        self.val[0] = num_map(pygame.mouse.get_pos()[0] - self.xpos, 0, self.width, 0, 180)
        self.val[1] = num_map(pygame.mouse.get_pos()[1] - self.ypos, 0, self.width, 0, 180)
        self.val[0] = int(constrain(self.val[0], 0, 180))
        self.val[1] = int(constrain(self.val[1], 0, 180))

        self.txt_surf_x = self.font.render(str(self.val[0]), 1, BLACK)
        self.txt_surf_y = self.font.render(str(self.val[1]), 1, BLACK)
        if self.call_back is not None:
            self.call_back(self.val)


# define our call-back functions:
def red_pressed():
    global is_red
    is_red = not is_red
    print('red!', flush=True)
    if is_red:
        if have_smbus:
            write_reg(CMD_IO1, 0)
        return RED
    if have_smbus:
        write_reg(CMD_IO1, 1)
    return GREY2


def red_released():
    pass


def green_pressed():
    global is_green
    is_green = not is_green
    print('green!', flush=True)
    if is_green:
        if have_smbus:
            write_reg(CMD_IO2, 0)
        return GREEN
    if have_smbus:
        write_reg(CMD_IO2, 1)
    return GREY2

def green_released():
    pass


def blue_pressed():
    global is_blue
    is_blue = not is_blue
    print('blue!', flush=True)
    if is_blue:
        if have_smbus:
            write_reg(CMD_IO3, 0)
        return BLUE
    if have_smbus:
        write_reg(CMD_IO3, 1)
    return GREY2


def blue_released():
    pass


def buzzer_pressed():
    print('buzzer %s!' % int(buzzer_freq.val), flush=True)
    if have_smbus:
        write_reg(CMD_BUZZER, buzzer_freq.val)


def buzzer_released():
    print('buzzer off!', flush=True)
    if have_smbus:
        write_reg(CMD_BUZZER, 0)


def forward_pressed():
    print('forward', str(int(10 * speed.val)), flush=True)
    if have_smbus:
        write_reg(CMD_DIR1, 1)
        write_reg(CMD_DIR2, 1)

        write_reg(CMD_PWM1, speed.val * 10 / 3)
        write_reg(CMD_PWM2, speed.val * 10 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 20 / 3)
        write_reg(CMD_PWM2, speed.val * 20 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 10)
        write_reg(CMD_PWM2, speed.val * 10)

def forward_released():
    print('stop!', flush=True)
    if have_smbus:
        write_reg(CMD_PWM1, 0)
        write_reg(CMD_PWM2, 0)

def backward_pressed():
    print('backward', str(int(10 * speed.val)), flush=True)
    if have_smbus:
        write_reg(CMD_DIR1, 0)
        write_reg(CMD_DIR2, 0)

        write_reg(CMD_PWM1, speed.val * 10 / 3)
        write_reg(CMD_PWM2, speed.val * 10 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 20 / 3)
        write_reg(CMD_PWM2, speed.val * 20 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 10)
        write_reg(CMD_PWM2, speed.val * 10)

def backward_released():
    print('stop!', flush=True)
    if have_smbus:
        write_reg(CMD_PWM1, 0)
        write_reg(CMD_PWM2, 0)

def left_pressed():
    print('left', flush=True)
    global state_servo_1
    state_servo_1 += turning_angle.val
    state_servo_1 = constrain(state_servo_1, 0, 180)
    current_angle.val = 180 - state_servo_1
    if have_smbus:
        # write_reg(CMD_SERVO1, num_map(state_servo_1, 0, 180, 500, 2500))
        write_servo(CMD_SERVO1, state_servo_1 + fine_servo_1.val)

def left_released():
    pass

def right_pressed():
    print('right', flush=True)
    global state_servo_1
    state_servo_1 -= turning_angle.val
    state_servo_1 = constrain(state_servo_1, 0, 180)
    current_angle.val = 180 - state_servo_1
    if have_smbus:
        # write_reg(CMD_SERVO1, num_map(state_servo_1, 0, 180, 500, 2500))
        write_servo(CMD_SERVO1, state_servo_1 + fine_servo_1.val)

def right_released():
    pass


def forward_left_pressed():
    print('forward left', str(int(10 * speed.val)), flush=True)
    if have_smbus:
        write_reg(CMD_DIR1, 1)
        write_reg(CMD_DIR2, 1)

        write_reg(CMD_PWM1, speed.val * 10 / 3)
        write_reg(CMD_PWM2, speed.val * 10 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 20 / 3)
        write_reg(CMD_PWM2, speed.val * 20 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 10)
        write_reg(CMD_PWM2, speed.val * 10)

    global state_servo_1
    state_servo_1 = current_angle.val + turning_angle.val
    state_servo_1 = constrain(state_servo_1, 0, 180)
    current_angle.val = 180 - state_servo_1
    if have_smbus:
        write_servo(CMD_SERVO1, state_servo_1 + fine_servo_1.val)

def forward_left_released():
    print('stop!', flush=True)
    current_angle.val = 90
    if have_smbus:
        write_reg(CMD_PWM1, 0)
        write_reg(CMD_PWM2, 0)
        write_servo(CMD_SERVO1, 90 + fine_servo_1.val)

def forward_right_pressed():
    print('forward right', str(int(10 * speed.val)), flush=True)
    if have_smbus:
        write_reg(CMD_DIR1, 1)
        write_reg(CMD_DIR2, 1)

        write_reg(CMD_PWM1, speed.val * 10 / 3)
        write_reg(CMD_PWM2, speed.val * 10 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 20 / 3)
        write_reg(CMD_PWM2, speed.val * 20 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 10)
        write_reg(CMD_PWM2, speed.val * 10)

    global state_servo_1
    state_servo_1 = current_angle.val - turning_angle.val
    state_servo_1 = constrain(state_servo_1, 0, 180)
    current_angle.val = 180 - state_servo_1
    if have_smbus:
        write_servo(CMD_SERVO1, state_servo_1 + fine_servo_1.val)

def forward_right_released():
    print('stop!', flush=True)
    current_angle.val = 90
    if have_smbus:
        write_reg(CMD_PWM1, 0)
        write_reg(CMD_PWM2, 0)
        write_servo(CMD_SERVO1, 90 + fine_servo_1.val)

def backward_left_pressed():
    print('backward left', str(int(10 * speed.val)), flush=True)
    if have_smbus:
        write_reg(CMD_DIR1, 0)
        write_reg(CMD_DIR2, 0)

        write_reg(CMD_PWM1, speed.val * 10 / 3)
        write_reg(CMD_PWM2, speed.val * 10 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 20 / 3)
        write_reg(CMD_PWM2, speed.val * 20 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 10)
        write_reg(CMD_PWM2, speed.val * 10)

    global state_servo_1
    state_servo_1 = current_angle.val + turning_angle.val
    state_servo_1 = constrain(state_servo_1, 0, 180)
    current_angle.val = 180 - state_servo_1
    if have_smbus:
        write_servo(CMD_SERVO1, state_servo_1 + fine_servo_1.val)

def backward_left_released():
    print('stop!', flush=True)
    current_angle.val = 90
    # current_angle.draw()
    if have_smbus:
        write_reg(CMD_PWM1, 0)
        write_reg(CMD_PWM2, 0)
        write_servo(CMD_SERVO1, 90 + fine_servo_1.val)

def backward_right_pressed():
    print('backward right', str(int(10 * speed.val)), flush=True)
    if have_smbus:
        write_reg(CMD_DIR1, 0)
        write_reg(CMD_DIR2, 0)

        write_reg(CMD_PWM1, speed.val * 10 / 3)
        write_reg(CMD_PWM2, speed.val * 10 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 20 / 3)
        write_reg(CMD_PWM2, speed.val * 20 / 3)
        time.sleep(0.07)

        write_reg(CMD_PWM1, speed.val * 10)
        write_reg(CMD_PWM2, speed.val * 10)

    global state_servo_1
    state_servo_1 = current_angle.val - turning_angle.val
    state_servo_1 = constrain(state_servo_1, 0, 180)
    current_angle.val = 180 - state_servo_1
    if have_smbus:
        write_servo(CMD_SERVO1, state_servo_1 + fine_servo_1.val)


def backward_right_released():
    print('stop!', flush=True)
    current_angle.val = 90
    if have_smbus:
        write_reg(CMD_PWM1, 0)
        write_reg(CMD_PWM2, 0)
        write_servo(CMD_SERVO1, 90 + fine_servo_1.val)


def cam_up_pressed():
    global state_servo_3
    state_servo_3 += step_slider.val
    state_servo_3 = constrain(state_servo_3, 0, 180)
    vertical.val = state_servo_3
    if have_smbus:
        # write_reg(CMD_SERVO3, num_map(state_servo_3, 0, 180, 500, 2500))
        write_servo(CMD_SERVO3, state_servo_3 + fine_servo_3.val)

def cam_up_released():
    pass

def cam_down_pressed():
    global state_servo_3
    state_servo_3 -= step_slider.val
    state_servo_3 = constrain(state_servo_3, 0, 180)
    vertical.val = state_servo_3
    if have_smbus:
        # write_reg(CMD_SERVO3, num_map(state_servo_3, 0, 180, 500, 2500))
        write_servo(CMD_SERVO3, state_servo_3 + fine_servo_3.val)

def cam_down_released():
    pass

def cam_home_pressed():
    global state_servo_2
    global state_servo_3
    state_servo_2 = 90
    state_servo_3 = 90
    horizontal.val = state_servo_2
    vertical.val = state_servo_3
    if have_smbus:
        # write_reg(CMD_SERVO2, num_map(90, 0, 180, 500, 2500))
        # write_reg(CMD_SERVO3, num_map(90, 0, 180, 500, 2500))
        write_servo(CMD_SERVO2, 90 + fine_servo_2.val)
        write_servo(CMD_SERVO3, 90 + fine_servo_3.val)

def cam_home_released():
    pass

def cam_left_pressed():
    global state_servo_2
    # state_servo_2 -= 10
    state_servo_2 -= step_slider.val
    state_servo_2 = constrain(state_servo_2, 0, 180)
    horizontal.val = state_servo_2
    if have_smbus:
        # write_reg(CMD_SERVO2, num_map(180 - state_servo_2, 0, 180, 500, 2500))
        write_servo(CMD_SERVO2, 180 - state_servo_2 - fine_servo_2.val)

def cam_left_released():
    pass

def cam_right_pressed():
    global state_servo_2
    # state_servo_2 += 10
    state_servo_2 += step_slider.val
    state_servo_2 = constrain(state_servo_2, 0, 180)
    horizontal.val = state_servo_2
    if have_smbus:
        # write_reg(CMD_SERVO2, num_map(180 - state_servo_2, 0, 180, 500, 2500))
        write_servo(CMD_SERVO2, 180 - state_servo_2 - fine_servo_2.val)

def cam_right_released():
    pass

def vertical_moved(val):
    global state_servo_3
    state_servo_3 = int(val)
    # print(state_servo_3)
    if have_smbus:
        # write_reg(CMD_SERVO3, num_map(state_servo_3, 0, 180, 500, 2500))
        write_servo(CMD_SERVO3, state_servo_3 + fine_servo_3.val)

def horizontal_moved(val):
    global state_servo_2
    state_servo_2 = int(val)
    if have_smbus:
        # write_reg(CMD_SERVO2, num_map(180 - state_servo_2, 0, 180, 500, 2500))
        write_servo(CMD_SERVO2, 180 - state_servo_2 - fine_servo_2.val)

def current_angle_moved(val):
    global state_servo_1
    state_servo_1 = int(val)
    if have_smbus:
        # write_reg(CMD_SERVO1, num_map(state_servo_1, 0, 180, 500, 2500))
        write_servo(CMD_SERVO1, state_servo_1 + fine_servo_1.val)


def map_moved(val):
    global state_servo_2
    global state_servo_3
    state_servo_2 = val[0]
    state_servo_3 = val[1]
    if have_smbus:
        write_servo(CMD_SERVO2, 180 - state_servo_2 - fine_servo_2.val)
        write_servo(CMD_SERVO3, 180 - state_servo_3 - fine_servo_3.val)


# def mousebuttondown():
#     pos = pygame.mouse.get_pos()
#     for button in buttons:
#         if button.rect.collidepoint(pos):
#             button.call_back_down()
#     for s in slides:
#         if s.button_rect.collidepoint(pos):
#             s.hit = True

# def mousebuttonup():
#     pos = pygame.mouse.get_pos()
#     for button in buttons:
#         if button.rect.collidepoint(pos):
#             button.call_back_up()
#     for s in slides:
#         s.hit = False


if __name__ == '__main__':
    # initialize screen:
    screen = pygame.display.set_mode((display_width, display_height))
    pygame.display.set_caption('Smart Car')
    screen.fill(background_color)

    # define initial state of LED colours:
    is_red = False
    is_green = False
    is_blue = True

    # define initial state of color buttons:
    button_red_color = GREY2
    button_green_color = GREY2
    button_blue_color = GREY2
    if is_red:
        button_red_color = RED
    if is_green:
        button_green_color = GREEN
    if is_blue:
        button_blue_color = BLUE

    # define state of servos:
    state_servo_1 = 90  # servo_1 is turning angle
    state_servo_2 = 90  # servo_2 is horizontal camera angle
    state_servo_3 = 90  # servo_3 is vertical camera angle

    # initialize the car:
    if have_smbus:
        # set servo's to initial state:
        # write_reg(CMD_SERVO1, num_map(state_servo_1, 0, 180, 500, 2500))
        # write_reg(CMD_SERVO2, num_map(state_servo_2, 0, 180, 500, 2500))
        # write_reg(CMD_SERVO3, num_map(state_servo_3, 0, 180, 500, 2500))
        write_servo(CMD_SERVO1, state_servo_1)
        write_servo(CMD_SERVO2, state_servo_2)
        write_servo(CMD_SERVO3, state_servo_3)

        # confirm buzzer off:
        # write_reg(CMD_BUZZER, 0)

        # flash LED's and buzz:
        for _ in range(2):
            write_reg(CMD_BUZZER, 2000)
            write_reg(CMD_IO1, 0)
            write_reg(CMD_IO2, 1)
            write_reg(CMD_IO3, 1)
            time.sleep(0.25)
            write_reg(CMD_BUZZER, 3000)
            write_reg(CMD_IO1, 1)
            write_reg(CMD_IO2, 0)
            write_reg(CMD_IO3, 1)
            time.sleep(0.25)
            write_reg(CMD_BUZZER, 4000)
            write_reg(CMD_IO1, 1)
            write_reg(CMD_IO2, 1)
            write_reg(CMD_IO3, 0)
            time.sleep(0.25)
            write_reg(CMD_BUZZER, 0)
            time.sleep(0.2)

        # set LED's:
        if is_red:
            write_reg(CMD_IO1, 0)
            button_red_color = RED
        else:
            write_reg(CMD_IO1, 1)
            button_red_color = GREY2

        if is_green:
            write_reg(CMD_IO2, 0)
            button_green_color = GREEN
        else:
            write_reg(CMD_IO2, 1)
            button_green_color = GREY2

        if is_blue:
            write_reg(CMD_IO3, 0)
            button_blue_color = BLUE
        else:
            write_reg(CMD_IO3, 1)
            button_blue_color = GREY2

    # insert smart car border:
    # surface = pygame.surface.Surface((324, 244))
    surface = pygame.surface.Surface((cx + 4, cy + 4))
    surface.fill(BLACK)
    screen.blit(surface, (0, 0))

    # insert smart car image or video if possible:
    if not have_camera:
        img = pygame.image.load('car_photo.jpg')  # if this fails, makes sure you have car_photo.jpg in your current directory
    else:
        if cam.query_image():
            img = cam.get_image()
    img = pygame.transform.scale(img, camera_size)
    screen.blit(img, (2, 2))

    # insert 'Servo Fine Tuning' text:
    font = pygame.font.SysFont('Verdana', 20)
    text_surf = font.render('Servo Fine Tuning', 1, BLACK)
    screen.blit(text_surf, (320 + 60 + 40 + 20 - 320 + cx, 15))

    # insert 'Car' text:
    text_surf = font.render('Car', 1, BLACK)
    screen.blit(text_surf, (145, 250 - 240 + cy))

    # insert 'Camera' text:
    text_surf = font.render('Camera', 1, BLACK)
    screen.blit(text_surf, (500 - 320 + cx, 250 - 240 + cy))


    # define our sliders:
    # our slider font:
    font = pygame.font.SysFont('Verdana', 12)

    # servo 1, 2, 3, 4:
    text_surf = font.render('Servo 1', 1, BLACK)
    screen.blit(text_surf, (320 + 60 + 40 + 20 - 320 + cx, 60))
    fine_servo_1 = Slider("Servo 1", 0, 10, -10, 540 - 320 + cx, 60)

    text_surf = font.render('Servo 2', 1, BLACK)
    screen.blit(text_surf, (320 + 60 + 40 + 20 - 320 + cx, 100))
    fine_servo_2 = Slider("Servo 2", 0, 10, -10, 540 - 320 + cx, 100)

    text_surf = font.render('Servo 3', 1, BLACK)
    screen.blit(text_surf, (320 + 60 + 40 + 20 - 320 + cx, 140))
    fine_servo_3 = Slider("Servo 3", 0, 10, -10, 540 - 320 + cx, 140)

    text_surf = font.render('Servo 4', 1, BLACK)
    screen.blit(text_surf, (320 + 60 + 40 + 20 - 320 + cx, 180))
    fine_servo_4 = Slider("Servo 4", 0, 10, -10, 540 - 320 + cx, 180)

    # turning angle:
    text_surf = font.render('Turning angle', 1, BLACK)
    screen.blit(text_surf, (18, 425 - 240 + cy))
    turning_angle = Slider("turning angle", 10, 30, 0, 160, 425 - 240 + cy)

    # current angle:
    text_surf = font.render('Current angle', 1, BLACK)
    screen.blit(text_surf, (18, 465 - 240 + cy))
    current_angle = Slider("current angle", 90, 180, 0, 160, 465 - 240 + cy, action=current_angle_moved)

    # speed:
    text_surf = font.render('Speed', 1, BLACK)
    screen.blit(text_surf, (60, 505 - 240 + cy))
    speed = Slider("speed", 50, 100, 0, 160, 505 - 240 + cy)

    # camera horizontal angle:
    # text_surf = font.render('Horizontal', 1, BLACK)
    # screen.blit(text_surf, (45 + 380, 425))
    # horizontal = Slider("horizontal", 90, 180, 0, 160 + 380, 425, action=horizontal_moved)

    # camera vertical angle:
    # text_surf = font.render('Vertical', 1, BLACK)
    # screen.blit(text_surf, (60 + 380, 465))
    # vertical = Slider("vertical", 90, 180, 0, 160 + 380, 465, action=vertical_moved)

    # step:
    # text_surf = font.render('Step', 1, BLACK)
    # screen.blit(text_surf, (320 + 60 + 40 + 20 + 15, 505))
    # step_slider = Slider("Step", 10, 45, 0, 540, 505)

    # buzzer slider:
    buzzer_freq = Slider("buzzer freq", 2000, 6000, 0, 60 + 320 - 320 + cx, 190)

    # define our list of sliders:
    slides = [buzzer_freq, fine_servo_1, fine_servo_2, fine_servo_3, fine_servo_4, turning_angle, current_angle, speed]
    # slides += [step_slider, horizontal, vertical]

    # define our buttons:
    button_red = Button("Red", (60 + 320 - 320 + cx, 30), red_pressed, red_released, bg=button_red_color, font_name="Segoe Print", font_size=16)
    button_green = Button("Green", (60 + 320 - 320 + cx, 70), green_pressed, green_released, bg=button_green_color, font_name="Segoe Print", font_size=16)
    button_blue = Button("Blue", (60 + 320 - 320 + cx, 110), blue_pressed, blue_released, bg=button_blue_color, font_name="Segoe Print", font_size=16)
    button_buzzer = Button("Buzzer", (60 + 320 - 320 + cx, 150), buzzer_pressed, buzzer_released, bg=GREY2, font_name="Segoe Print", font_size=16)

    button_forward = Button('FORWARD', (160, 300 - 240 + cy), forward_pressed, forward_released, bg = GREY2, size=(95, 30))
    button_backward = Button('BACKWARD', (160, 380 - 240 + cy), backward_pressed, backward_released, bg = GREY2, size=(95, 30))
    button_left = Button('LEFT', (60, 340 - 240 + cy), left_pressed, left_released, bg = GREY2, size=(95, 30))
    button_right = Button('RIGHT', (260, 340 - 240 + cy), right_pressed, right_released, bg = GREY2, size=(95, 30))

    button_forward_left = Button('FL', (60, 300 - 240 + cy), forward_left_pressed, forward_left_released, bg = GREY2, size=(95, 30))
    button_forward_right = Button('FR', (260, 300 - 240 + cy), forward_right_pressed, forward_right_released, bg = GREY2, size=(95, 30))
    button_backward_left = Button('BL', (60, 380 - 240 + cy), backward_left_pressed, backward_left_released, bg = GREY2, size=(95, 30))
    button_backward_right = Button('BR', (260, 380 - 240 + cy), backward_right_pressed, backward_right_released, bg = GREY2, size=(95, 30))

    # button_cam_up = Button('UP', (380 + 160, 300), cam_up_pressed, cam_up_released, bg = GREY2, size=(95, 30))
    # button_cam_down = Button('DOWN', (380 + 160, 380), cam_down_pressed, cam_down_released, bg = GREY2, size=(95, 30))
    # button_cam_home = Button('HOME', (380 + 160, 340), cam_home_pressed, cam_home_released, bg = GREY2, size=(95, 30))
    # button_cam_left = Button('LEFT', (380 + 60, 340), cam_left_pressed, cam_left_released, bg = GREY2, size=(95, 30))
    # button_cam_right = Button('RIGHT', (380 + 260, 340), cam_right_pressed, cam_right_released, bg = GREY2, size=(95, 30))

    # define our list of buttons:
    buttons = [button_red, button_green, button_blue, button_buzzer, button_forward, button_backward, button_left, button_right]
    # buttons += [button_cam_up, button_cam_down, button_cam_left, button_cam_right, button_cam_home]
    buttons += [button_forward_left, button_forward_right, button_backward_left, button_backward_right]

    # define our camera active map:
    camera_map = ActiveMap('camera', 230, [90, 90], 180, 0, 420 - 320 + cx, 285 - 240 + cy, map_moved)
    # camera_map = ActiveMap('camera', 230, [90, 90], 180, 0, 420 - 320 + cx, 285, map_moved)
    # camera_map.draw()

    # define our list of active maps:
    active_maps = [camera_map]

    # the event loop:
    camera_counter = 0
    while True:
        if camera_counter == 0:
            if have_camera:
                # start_time = time.time()
                if cam.query_image():
                    img = cam.get_image()
                    img = pygame.transform.scale(img, camera_size)
                    screen.blit(img, (2, 2))
                    pygame.display.flip()
                # end_time = time.time()
                # delta_time = end_time - start_time
                # print(delta_time)
        camera_counter += 1
        camera_counter %= camera_frequency
        print(camera_counter)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # stop camera:
                if have_camera:
                    cam.stop()
                # switch off LED's:
                if have_smbus:
                    write_reg(CMD_IO1, 1)
                    write_reg(CMD_IO2, 1)
                    write_reg(CMD_IO3, 1)
                # quit pygame:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # mousebuttondown()
                pos = pygame.mouse.get_pos()
                for button in buttons:
                    if button.rect.collidepoint(pos):
                        button.call_back_down()
                for s in slides:
                    if s.button_rect.collidepoint(pos):
                        s.hit = True
                for amap in active_maps:
                    # if amap.button_rect.collidepoint(pos):
                    if amap.rect.collidepoint(pos):
                        amap.hit = True

            elif event.type == pygame.MOUSEBUTTONUP:
                # mousebuttonup()
                pos = pygame.mouse.get_pos()
                for button in buttons:
                    if button.rect.collidepoint(pos):
                        button.call_back_up()
                for s in slides:
                    s.hit = False
                for amap in active_maps:
                    amap.hit = False

        # draw buttons:
        for button in buttons:
            button.draw()

        # move slides:
        for s in slides:
            if s.hit:
                s.move()

        # draw slides:
        for s in slides:
            s.draw()

        # move active map:
        for amap in active_maps:
            if amap.hit:
                amap.move()

        # draw active maps:
        for amap in active_maps:
            amap.draw()

        pygame.display.flip()
        pygame.time.wait(40)
