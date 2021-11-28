#!/usr/bin/env python3
import time
import platform

from ant.core import driver
from ant.core import node

from usb.core import find

from StrideSensorTx import StrideSensorTx
from SpeedCadenceSensorRx import SpeedCadenceSensorRx
from config import DEBUG, LOG, NETKEY, STRIDE_SENSOR_ID, STRIDE_SENSOR_TYPE, SPEED_SENSOR_ID

antnode = None
speed_sensor = None
stride_sensor = None

strides = 0
distance = 0

def stop_ant():
    if speed_sensor:
        print("Closing speed sensor")
        speed_sensor.close()
        speed_sensor.unassign()
    if stride_sensor:
        print("Closing power meter")
        stride_sensor.close()
        stride_sensor.unassign()
    if antnode:
        print("Stopping ANT node")
        antnode.stop()

pywin32 = False
if platform.system() == 'Windows':
    def on_exit(sig, func=None):
        stop_ant()
    try:
        import win32api
        win32api.SetConsoleCtrlHandler(on_exit, True)
        pywin32 = True
    except ImportError:
        print("Warning: pywin32 is not installed, use Ctrl+C to stop")

try:
    devs = find(find_all=True, idVendor=0x0fcf)
    for dev in devs:
        if dev.idProduct in [0x1008, 0x1009]:
            # If running on the same PC as the receiver app (with two identical sticks)
            # the first stick may be already claimed, so continue trying
            stick = driver.USB2Driver(log=LOG, debug=DEBUG, idProduct=dev.idProduct, bus=dev.bus, address=dev.address)
            try:
                stick.open()
            except:
                continue
            stick.close()
            break
    else:
        print("No ANT devices available")
        exit()

    antnode = node.Node(stick)
    print("Starting ANT node")
    antnode.start()
    key = node.Network(NETKEY, 'N:ANT+')
    antnode.setNetworkKey(0, key)

    print("Starting speed sensor")
    try:
        # Create the speed sensor object and open it
        speed_sensor = SpeedCadenceSensorRx(antnode, SENSOR_TYPE, SPEED_SENSOR_ID & 0xffff)
        speed_sensor.open()
    except Exception as e:
        print("speed_sensor error: " + repr(e))
        speed_sensor = None

    print("Starting stride sensor with ANT+ ID " + repr(STRIDE_SENSOR_ID))
    try:
        # Create the stride sensor object and open it
        stride_sensor = StrideSensorTx(antnode, STRIDE_SENSOR_ID)
        stride_sensor.open()
    except Exception as e:
        print("stride_sensor error: " + repr(e))
        stride_sensor = None

    stopped = True
    print("Main wait loop")
    while True:
        try:
            time.sleep(.25)
            # Read data from ThreadmillSpeed
            kms_per_rev = 0.15 / 1000.0
            speed_kmh = speed_sensor.revsPerSec * 3600 * kms_per_rev
            speed_mps = speed * 0.278
            
            # Write data to StrideSensor
            strides += 180 / 60 / 4
            distance += speed_mps / 4
            strideSensor.update(strides, distance, speed_mps)

        except (KeyboardInterrupt, SystemExit):
            stop_ant()
            break

except Exception as e:
    print("Exception: " + repr(e))
finally:
    if not pywin32:
        stop_ant()
