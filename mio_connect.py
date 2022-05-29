from src.myodriver import MyoDriver
from src.config import Config
import serial
import getopt
import sys
from serial.tools.list_ports import comports


def main(argv):
    config = Config()
    # port0 = comports()[3][0] #ACM0 -> left upper
    port1 = comports()[2][0] #ACM1 -> left lower
    port2 = comports()[1][0] #ACM2 -> right upper
    port3 = comports()[0][0] #ACM3 -> right lower
    # print('port0: ', port0)
    print('port1: ', port1)
    print('port2: ', port2)
    print('port3: ', port3)
    
    left_upper = b'$\x92\xe2\x05\x17\xc5'
    left_lower = b'\xd8hr\x86\x02\xdd'
    right_upper = b'\xfc/\x84\x04\xeb\xf1'
    right_lower = b'.\x90Z\xf7\r\xe5'

    # Get options and arguments
    try:
        opts, args = getopt.getopt(argv, 'hsn:a:p:v', ['help', 'shutdown', 'nmyo', 'address', 'port', 'verbose'])
    except getopt.GetoptError:
        sys.exit(2)
    turnoff = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_usage()
            sys.exit()
        elif opt in ('-s', '--shutdown'):
            turnoff = True
        elif opt in ("-n", "--nmyo"):
            config.MYO_AMOUNT = int(arg)
        elif opt in ("-a", "--address"):
            config.OSC_ADDRESS = arg
        elif opt in ("-p", "--port"):
            config.OSC_PORT = arg
        elif opt in ("-v", "--verbose"):
            config.VERBOSE = True

    # Run
    myo_driver = None
    try:
        # Init
        # myo_driver_0 = MyoDriver(config, port0, left_upper)
        myo_driver_1 = MyoDriver(config, port1, left_lower)
        myo_driver_2 = MyoDriver(config, port2, right_upper)
        myo_driver_3 = MyoDriver(config, port3, right_lower)

        # Connect
        # myo_driver_0.run()
        # myo_driver_0.get_info()
        print('run second!!!')
        myo_driver_1.run()
        myo_driver_1.get_info()
        print('run third!!!')
        myo_driver_2.run()
        myo_driver_2.get_info()
        print('run forth!!!')
        myo_driver_3.run()
        myo_driver_3.get_info()
        
        if turnoff:
            # Turn off
            print("turn off")
            # myo_driver_0.deep_sleep_all()
            myo_driver_1.deep_sleep_all()
            myo_driver_2.deep_sleep_all()
            myo_driver_3.deep_sleep_all()
            return

        # if Config.GET_MYO_INFO:
            # Get info
            myo_driver_0.get_info()
            myo_driver_1.get_info()

        print("Ready for data.")
        print()

        # Receive and handle data
        while True:
            # myo_driver_0.receive()
            myo_driver_1.receive()
            myo_driver_2.receive()
            myo_driver_3.receive()

    except KeyboardInterrupt:
        print("Interrupted.")

    except serial.serialutil.SerialException:
        print("ERROR: Couldn't open port. Please close MyoConnect and any program using this serial port.")

    finally:
        print("Disconnecting...")
        # if myo_driver_0 is not None:
        #     if Config.DEEP_SLEEP_AT_KEYBOARD_INTERRUPT:
        #         myo_driver_0.deep_sleep_all()
        #     else:
        #         myo_driver_0.disconnect_all()
        # print("left_upper Disconnected")
        
        if myo_driver_1 is not None:
            if Config.DEEP_SLEEP_AT_KEYBOARD_INTERRUPT:
                myo_driver_1.deep_sleep_all()
            else:
                myo_driver_1.disconnect_all()
        print("left_lower Disconnected")

        if myo_driver_2 is not None:
            if Config.DEEP_SLEEP_AT_KEYBOARD_INTERRUPT:
                myo_driver_2.deep_sleep_all()
            else:
                myo_driver_2.disconnect_all()
        print("right_upper Disconnected")

        if myo_driver_3 is not None:
            if Config.DEEP_SLEEP_AT_KEYBOARD_INTERRUPT:
                myo_driver_3.deep_sleep_all()
            else:
                myo_driver_3.disconnect_all()
        print("right_lower Disconnected")


def print_usage():
    message = """usage: python mio_connect.py [-h | --help] [-s | --shutdown] [-n | --nmyo <amount>] [-a | --address \
<address>] [-p | --port <port_number>] [-v | --verbose]

Options and arguments:
    -h | --help: display this message
    -s | --shutdown: turn off (deep_sleep) the expected amount of myos
    -n | --nmyo <amount>: set the amount of devices to expect
    -a | --address <address>: set OSC address
    -p | --port <port_number>: set OSC port
    -v | --verbose: get verbose output
"""
    print(message)


if __name__ == "__main__":
    main(sys.argv[1:])
