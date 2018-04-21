import sys
import time

import smbus

if len(sys.argv) < 2:
    pwm_blue = 5
else:
    pwm_blue = int(sys.argv[1])

CMD_IO1 = 9
CMD_IO2 = 10
CMD_IO3 = 11


def dimmer(pwm, cmd):
    smbus_address = 0x18  # default address
    bus = smbus.SMBus(1)
    bus.open(1)

    start_time = time.time()
    bus.write_i2c_block_data(smbus_address, CMD_IO1, [0, 0])
    bus.write_i2c_block_data(smbus_address, CMD_IO1, [0, 1])

    bus.write_i2c_block_data(smbus_address, CMD_IO2, [0, 0])
    bus.write_i2c_block_data(smbus_address, CMD_IO2, [0, 1])

    bus.write_i2c_block_data(smbus_address, CMD_IO3, [0, 0])
    bus.write_i2c_block_data(smbus_address, CMD_IO3, [0, 1])
    end_time = time.time()
    delta_time = end_time - start_time
    print(delta_time)

    while True:
        if pwm > 0:
            bus.write_i2c_block_data(smbus_address, cmd, [0, 0])
        for pwm_counter in range(10):
            if pwm_counter < pwm:
                time.sleep(delta_time/6)
            else:
                bus.write_i2c_block_data(smbus_address, cmd, [0, 1])


dimmer(pwm_blue, CMD_IO3)
