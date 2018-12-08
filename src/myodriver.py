from src.public.myohw import *
from src.myo import Myo
from src.bluetooth import Bluetooth
from src.data_handler import DataHandler


class MyoDriver:
    """
    Responsible for myo connections and messages.
    """
    def __init__(self, config):
        self.config = config
        print("OSC Address: " + str(self.config.OSC_ADDRESS))
        print("OSC Port: " + str(self.config.OSC_PORT))
        print()

        self.data_handler = DataHandler(self.config)
        self.bluetooth = Bluetooth(self.config.MESSAGE_DELAY)

        self.myos = []

        self.myo_to_connect = None
        self.scanning = False
        self.connected = False

        # Add handlers for expected events
        self.set_handlers()

    def receive(self):
        self.bluetooth.receive()

    def handle_discover(self, e, payload):
        """
        Handler for ble_evt_gap_scan_response event.
        """
        if self.scanning and not self.myo_to_connect:
            self.print_status("Device found", payload['sender'])
            if payload['data'].endswith(bytes(Final.myo_id)):
                if not self._has_paired_with(payload['sender']):
                    self.myo_to_connect = Myo(payload['sender'])
                    self.print_status("Myo found", self.myo_to_connect.address)
                    self.print_status()
                    self.scanning = False

    def _has_paired_with(self, address):
        for m in self.myos:
            if m.address == address:
                return True
        return False

    def handle_connect(self, e, payload):
        """
        Handler for ble_rsp_gap_connect_direct event.
        """
        if not payload['result'] == 0:
            raise RuntimeError

    def handle_disconnect(self, e, payload):
        """
        Handle for ble_evt_connection_disconnected event.
        """
        self.print_status("Disconnected:", payload)

    def handle_connection_status(self, e, payload):
        """
        Handler for ble_evt_connection_status event.
        """
        if payload['address'] == self.myo_to_connect.address and payload['flags'] == 5:
            # self.print_status("Connection status: ", payload)
            self.connected = True
            self.myo_to_connect.set_id(payload['connection'])
            self.print_status("Connected with id", self.myo_to_connect.connection_id)

    def handle_attribute_value(self, e, payload):
        """
        Handler for EMG events, expected as a ble_evt_attclient_attribute_value event with handle 43, 46, 49 or 52.
        """
        emg_handles = [
            ServiceHandles.EmgData0Characteristic,
            ServiceHandles.EmgData1Characteristic,
            ServiceHandles.EmgData2Characteristic,
            ServiceHandles.EmgData3Characteristic
        ]
        imu_handles = [
            ServiceHandles.IMUDataCharacteristic
        ]
        myo_handles = [
            ServiceHandles.DeviceName,
            ServiceHandles.FirmwareVersionCharacteristic,
            ServiceHandles.BatteryCharacteristic
        ]
        if payload['atthandle'] in emg_handles:
            self.data_handler.handle_emg(payload)
        elif payload['atthandle'] in imu_handles:
            self.data_handler.handle_imu(payload)
        else:
            for myo in self.myos:
                myo.handle_attribute_value(payload)
            if payload['atthandle'] not in myo_handles:
                self.print_status(e, payload)

    def set_handlers(self):
        """
        Set handlers for relevant events.
        """
        self.bluetooth.add_scan_response_handler(self.handle_discover)
        self.bluetooth.add_connect_response_handler(self.handle_connect)
        self.bluetooth.add_attribute_value_handler(self.handle_attribute_value)
        self.bluetooth.add_disconnected_handler(self.handle_disconnect)
        self.bluetooth.add_connection_status_handler(self.handle_connection_status)

    def disconnect_all(self):
        """
        Stop possible scanning and close all connections.
        """
        self.bluetooth.disconnect_all()

    def add_myo_connection(self):
        """
        Procedure for connection with the Myo Armband. Scans, connects, disables sleep and starts EMG stream.
        """
        # Discover
        self.print_status("Scanning")
        self.bluetooth.gap_discover()

        # Await response
        self.scanning = True
        while self.myo_to_connect is None:
            self.bluetooth.receive()

        # End gap
        self.bluetooth.end_gap()

        # Direct connection
        self.print_status("Connecting to", self.myo_to_connect.address)
        self.bluetooth.direct_connect(self.myo_to_connect.address)

        # Await response
        while self.myo_to_connect.connection_id is None or not self.connected:
            self.receive()

        # Notify successful connection with self.print_status and vibration
        self.print_status("Connection successful. Setting up...")
        self.print_status()
        self.bluetooth.send_vibration_short(self.myo_to_connect.connection_id)

        # Disable sleep
        self.bluetooth.disable_sleep(self.myo_to_connect.connection_id)

        self.myos.append(self.myo_to_connect)
        print("Myo ready", self.myo_to_connect.connection_id, self.myo_to_connect.address)
        print()
        self.myo_to_connect = None
        self.scanning = False
        self.connected = False

    def get_info(self):
        """
        Send read attribute messages and await answer.
        """
        if len(self.myos):
            self.print_status("Getting myo info")
            self.print_status()
            for myo in self.myos:
                self.bluetooth.read_device_name(myo.connection_id)
                self.bluetooth.read_firmware_version(myo.connection_id)
                self.bluetooth.read_battery_level(myo.connection_id)
            while not self._myos_ready():
                self.receive()
            print("Myo list:")
            for myo in self.myos:
                print(" - " + str(myo))
            print()

    def _myos_ready(self):
        """
        :return: True if every myo has its data set, False otherwise.
        """
        for m in self.myos:
            if not m.ready():
                return False
        return True

    def run(self):
        """
        Main. Disconnects possible connections and starts as many connections as needed.
        :param myo_amount: amount of myos to detect before EMG/IMU stream starts.
        """
        self.disconnect_all()
        while len(self.myos) < self.config.MYO_AMOUNT:
            print("*** Connecting myo " + str(len(self.myos) + 1) + " out of " + str(self.config.MYO_AMOUNT) + " ***")
            print()
            self.add_myo_connection()

    def print_status(self, *args):
        """
        Printer function for VERBOSE support.
        """
        if self.config.VERBOSE:
            print(*args)

    def deep_sleep_all(self):
        print("Turning off devices...")
        for m in self.myos:
            self.bluetooth.deep_sleep(m.connection_id)
        print("Disconnected.")

    def enable_data_all(self):
        """
        Start EMG/IMJ/Classifier data and subscribe to their corresponding characteristic.
        """
        for m in self.myos:
            self.bluetooth.enable_data(m.connection_id, self.config)
        if self.config.VERBOSE:
            print("Data enabled according to config for all devices.")
