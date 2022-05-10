from src.myodriver import MyoDriver
from src.config import Config
import serial
import getopt
import sys
from serial.tools.list_ports import comports

def main(argv):
    config = Config()
    port0 = comports()[1][0] #ACM0 -> left
    port1 = comports()[0][0] #ACM1 -> right
    print('port0: ', port0)
    print('port1: ', port1)
    
    left_upper = b'$\x92\xe2\x05\x17\xc5'
    left_lower = b'\xd8hr\x86\x02\xdd'
    right_upper = b'\xfc/\x84\x04\xeb\xf1'
    right_lower = b'.\x90Z\xf7\r\xe5'

    # if self.myo_to_connect.address == b'.\x90Z\xf7\r\xe5':
    #     self.myo_arm = 'right_lower'
    #     print('right_lower')
    # if self.myo_to_connect.address == b'\xfc/\x84\x04\xeb\xf1':
    #     self.myo_arm = 'right_upper'  
    #     print('right_upper')
    # if self.myo_to_connect.address == b'\xd8hr\x86\x02\xdd':
    #     self.myo_arm = 'left_lower'  
    #     print('left_lower')                        
    # if self.myo_to_connect.address == b'$\x92\xe2\x05\x17\xc5':
    #     self.myo_arm = 'left_upper'  
    #     print('left_upper') 
    
    
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
        myo_driver_left = MyoDriver(config, port0, left_upper, left_lower)
        myo_driver_right = MyoDriver(config, port1, right_upper, right_lower)

        # Connect
        myo_driver_left.run()
        myo_driver_right.run()

        if turnoff:
            # Turn off
            myo_driver_left.deep_sleep_all()
            myo_driver_right.deep_sleep_all()
            return

        if Config.GET_MYO_INFO:
            # Get info
            myo_driver_left.get_info()
            myo_driver_right.get_info()

        print("Ready for data.")
        print()

        # Receive and handle data
        while True:
            myo_driver_left.receive()
            myo_driver_right.receive()

    except KeyboardInterrupt:
        print("Interrupted.")

    except serial.serialutil.SerialException:
        print("ERROR: Couldn't open port. Please close MyoConnect and any program using this serial port.")

    finally:
        print("Disconnecting...")
        if myo_driver_left is not None:
            if Config.DEEP_SLEEP_AT_KEYBOARD_INTERRUPT:
                myo_driver_left.deep_sleep_all()
            else:
                myo_driver_left.disconnect_all()
        print("myo_driver_left Disconnected")
        
        if myo_driver_right is not None:
            if Config.DEEP_SLEEP_AT_KEYBOARD_INTERRUPT:
                myo_driver_right.deep_sleep_all()
            else:
                myo_driver_right.disconnect_all()
        print("myo_driver_right Disconnected")


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
