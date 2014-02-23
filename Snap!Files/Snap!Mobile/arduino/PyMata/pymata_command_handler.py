__author__ = 'Copyright (c) 2013 Alan Yorinks All rights reserved.'

"""
Copyright (c) 2013-14 Alan Yorinks All rights reserved.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU  General Public
License as published by the Free Software Foundation; either
version 3 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import threading
import time


class PyMataCommandHandler(threading.Thread):
    """
    This class handles all data interchanges with Firmata
    The receive loop runs in its own thread.

    Messages to be sent to Firmata are queued through a deque to allow for priority
    messages to take precedence. The deque is checked within the receive loop for any
    outgoing messages.

    There is no blocking in either communications direction.

    There is blocking when accessing the data tables through the _data_lock
    """

    # the following defines are from Firmata.h

    # message command bytes (128-255/ 0x80- 0xFF)
    # from this client to firmata
    MSG_CMD_MIN = 0x80  # minimum value for a message from firmata
    REPORT_ANALOG = 0xC0  # enable analog input by pin #
    REPORT_DIGITAL = 0xD0  # enable digital input by port pair
    SET_PIN_MODE = 0xF4  # set a pin to INPUT/OUTPUT/PWM/etc
    START_SYSEX = 0xF0  # start a MIDI Sysex message
    END_SYSEX = 0xF7  # end a MIDI Sysex message
    SYSTEM_RESET = 0xFF  # reset from MIDI

    # messages from firmata
    DIGITAL_MESSAGE = 0x90  # send or receive data for a digital pin
    ANALOG_MESSAGE = 0xE0  # send or receive data for a PWM configured pin
    REPORT_VERSION = 0xF9  # report protocol version

    # user defined SYSEX commands
    # from this client
    ENCODER_CONFIG = 0x20  # create and enable encoder object
    TONE_PLAY = 0x5F  # play a tone at a specified frequency and duration
    SONAR_CONFIG = 0x60 # configure pins to control a Ping type sonar distance device

    # messages from firmata
    ENCODER_DATA = 0x21 # current encoder position data
    SONAR_DATA = 0x61 # distance data returned

    # standard Firmata sysex commands

    SERVO_CONFIG = 0x70     # set servo pin and max and min angles
    STRING_DATA = 0x71  #  a string message with 14-bits per char
    I2C_REQUEST = 0x76  # send an I2C read/write request
    I2C_REPLY = 0x77    # a reply to an I2C read request
    I2C_CONFIG = 0x78   # config I2C settings such as delay times and power pins
    REPORT_FIRMWARE = 0x79  # report name and version of the firmware
    SAMPLING_INTERVAL = 0x7A  # modify the sampling interval

    EXTENDED_ANALOG = 0x6F  # analog write (PWM, Servo, etc) to any pin
    PIN_STATE_QUERY = 0x6D  # ask for a pin's current mode and value
    PIN_STATE_RESPONSE = 0x6E  # reply with pin's current mode and value
    CAPABILITY_QUERY = 0x6B  # ask for supported modes and resolution of all pins
    CAPABILITY_RESPONSE = 0x6C  # reply with supported modes and resolution
    ANALOG_MAPPING_QUERY = 0x69  # ask for mapping of analog to pin numbers
    ANALOG_MAPPING_RESPONSE = 0x6A  # reply with analog mapping data


    # reserved values
    SYSEX_NON_REALTIME = 0x7E  # MIDI Reserved for non-realtime messages
    SYSEX_REALTIME = 0x7F  # MIDI Reserved for realtime messages


    # pin modes
    INPUT = 0x00 # pin set as input
    OUTPUT = 0x01 # pin set as output
    ANALOG = 0x02  # analog pin in analogInput mode
    PWM = 0x03  # digital pin in PWM output mode
    SERVO = 0x04  # digital pin in Servo output mode
    I2C = 0x06  # pin included in I2C setup
    ONEWIRE = 0x07 # possible future feature
    STEPPER = 0x08 # possible future feature
    TONE = 0x09  # Any pin in TONE mode
    ENCODER = 0x0a
    SONAR = 0x0b # Any pin in SONAR mode
    IGNORE = 0x7f

    # the following pin modes are not part of or defined by Firmata
    # but used by PyFirmata

    DIGITAL = 0x20

    # The response tables hold response information for all pins
    # Each table is a table of entries for each pin, which consists of the pin mode, and its last value from firmata



    # This is a table that stores analog pin modes and data
    # each entry represents ia mode (INPUT or OUTPUT), and its last current value
    analog_response_table = []

    # This is a table that stores digital pin modes and data
    # each entry represents  its mode (INPUT or OUTPUT, PWM, SERVO, ENCODER), and its last current value
    digital_response_table = []

    # The analog and digital latch tables  will store "latched" data for input pins.
    # If a pin is armed, the latest value will be stored and maintained until
    # the data is read, and the data is cleared from the latch and the latch rearmed.

    # The table consists of a list of lists  sized by the number of pins for the board. It is ordered by pin number
    # and each list entry contains a latch state, a value and a date stamp when latched.
    # An armed state = 0 and a latched state = 1

    # analog_latch_table entry = [latched_state, threshold_type, threshold_value, latched_data, time_stamp]
    # digital_latch_table_entry = [latched_state, threshold_type, latched_data, time_stamp]

    analog_latch_table = []
    digital_latch_table = []

    # index into latch tables
    LATCH_STATE = 0
    LATCHED_THRESHOLD_TYPE = 1

    ANALOG_LATCH_DATA_TARGET = 2
    ANALOG_LATCHED_DATA = 3
    ANALOG_TIME_STAMP = 4

    DIGITAL_LATCHED_DATA = 2
    DIGITAL_TIME_STAMP = 3


    #latch states
    LATCH_IGNORE = 0  # this pin will be ignored for latching
    LATCH_ARMED = 1  # When the next pin value change is received for this pin, if it matches the latch criteria
    # the data will be latched
    LATCH_LATCHED = 2  # data has been latched. Read the data to re-arm the latch

    # latch threshold types
    DIGITAL_LATCH_LOW = 0  # for digital pins
    DIGITAL_LATCH_HIGH = 1  # for digital pins
    ANALOG_LATCH_GT = 2  # greater than for analog
    ANALOG_LATCH_LT = 3  # less than for analog
    ANALOG_LATCH_GTE = 4  # greater than or equal to for analog
    ANALOG_LATCH_LTE = 5  # less than or equal to for analog


    # These values are indexes into the response table entries
    RESPONSE_TABLE_MODE = 0
    RESPONSE_TABLE_PIN_DATA_VALUE = 1

    # These values are the index into the data passed by _arduino and used to reassemble integer values
    MSB = 2
    LSB = 1

    # This is a map that allows the look up of command handler methods using a command as the key.
    # This is populated in the run method after the python interpreter sees all of the command handler method
    # defines (python does not have forward referencing)

    # The "key" is the command, and the value contains is a list containing the  method name and the number of
    # parameter bytes that the method will require to process the message (in some cases the value is unused)
    command_dispatch = {}

    # this deque is used by the methods that assemble messages to be sent to Firmata. The deque is filled outside of
    # of the message processing loop and emptied within the loop.
    command_deque = None

    # firmata version information - saved as a list - [major, minor]
    firmata_version = []

    # firmata firmware version information saved as a list [major, minor, file_name]
    firmata_firmware = []

    # a lock to protect the data tables when they are being accessed
    data_lock = None

    # total number of pins for the discovered board
    total_pins_discovered = 0

    # total number of analog pins for the discovered board
    number_of_analog_pins_discovered = 0

    # map of i2c addresses and associated data that has been read for that address
    i2c_map = {}

    # the active_sonar_map maps the sonar trigger pin number (the key) to the current data value returned
    active_sonar_map = {}

    def __init__(self, transport, command_deque, data_lock):
        """
        constructor for CommandHandler class
        @param transport: A reference to the communications port designator.
        @param command_deque:  A reference to a command deque.
        @param data_lock: A reference to a thread lock.
        """

        # this list contains the results of the last pin query
        self.last_pin_query_results = []

        # this stores the results of a capability request
        self.capability_query_results = []

        # this stores the results of an analog mapping query
        self.analog_mapping_query_results = []

        self.data_lock = data_lock
        self.transport = transport
        self.command_deque = command_deque

        self.total_pins_discovered = 0

        self.number_of_analog_pins_discovered = 0

        threading.Thread.__init__(self)
        self.daemon = True

    def auto_discover_board(self):
        """
        This method will allow up to 30 seconds for discovery (communicating with) an Arduino board
        and then will determine a pin configuration table for the board.
        @return: True if board is successfully discovered or False upon timeout
        """
        # get current time
        start_time = time.time()

        # wait for up to 30 seconds for a successful capability query to occur

        while len(self.analog_mapping_query_results) == 0:
            if time.time() - start_time > 30:
                return False
                # keep sending out a capability query until there is a response
            self.send_sysex(self.ANALOG_MAPPING_QUERY, None)
            time.sleep(.1)

        print "Board initialized in %d seconds" % (time.time() - start_time)

        for pin in self.analog_mapping_query_results:
            self.total_pins_discovered += 1
            # non analog pins will be marked as IGNORE
            if pin != self.IGNORE:
                self.number_of_analog_pins_discovered += 1

        print 'Total Number of Pins Detected = %d' % self.total_pins_discovered
        print 'Total Number of Analog Pins Detected = %d' % self.number_of_analog_pins_discovered

        # response table initialization
        # for each pin set the mode to input and the last read data value to zero
        for pin in range(0, self.total_pins_discovered):
            response_entry = [self.INPUT, 0]
            self.digital_response_table.append(response_entry)

        for pin in range(0, self.number_of_analog_pins_discovered):
            response_entry = [self.INPUT, 0]
            self.analog_response_table.append(response_entry)

        # set up latching tables
        for pin in range(0, self.total_pins_discovered):
            digital_latch_table_entry = [0, 0, 0, 0]
            self.digital_latch_table.append(digital_latch_table_entry)

        for pin in range(0, self.number_of_analog_pins_discovered):
            analog_latch_table_entry = [0, 0, 0, 0, 0]
            self.analog_latch_table.append(analog_latch_table_entry)

        return True

    def report_version(self, data):
        """
        This method processes the report version message,  sent asynchronously by Firmata when it starts up
        or after refresh_report_version() is called

        Use the api method api_get_version to retrieve this information
        @param data: Message data from Firmata
        @return: No return value.
        """
        self.firmata_version.append(data[0])  # add major
        self.firmata_version.append(data[1])  # add minor

    def set_analog_latch(self, pin, threshold_type, threshold_value):
        """
        This method "arms" a pin to allow data latching for the pin.
        @param pin: Analog pin number (value following an 'A' designator, i.e. A5 = 5
        @param threshold_type: ANALOG_LATCH_GT | ANALOG_LATCH_LT  | ANALOG_LATCH_GTE | ANALOG_LATCH_LTE
        @param threshold_value: numerical value
        """
        self.data_lock.acquire(True)
        self.analog_latch_table[pin] = [self.LATCH_ARMED, threshold_type, threshold_value, 0, 0]
        self.data_lock.release()

    def set_digital_latch(self, pin, threshold_type):
        """
        This method "arms" a pin to allow data latching for the pin.
        @param pin: digital pin number
        @param threshold_type: DIGITAL_LATCH_HIGH | DIGITAL_LATCH_LOW
        """
        self.data_lock.acquire(True)
        self.digital_latch_table[pin] = [self.LATCH_ARMED, threshold_type, 0, 0]
        self.data_lock.release()


    def get_analog_latch_data(self, pin):
        """
        This method reads the analog latch table for the specified pin and returns a list that contains:
        [latch_state, latched_data, and time_stamp].
        If the latch state is latched, the entry in the table is cleared
        @param pin:  pin number
        @return: [latch_state, latched_data, and time_stamp]
        """
        self.data_lock.acquire(True)
        pin_data = self.analog_latch_table[pin]
        current_latch_data = [pin,
                              pin_data[self.LATCH_STATE],
                              pin_data[self.ANALOG_LATCHED_DATA],
                              pin_data[self.ANALOG_TIME_STAMP]]
        # if this is latched data, clear the latch table entry for this pin
        if pin_data[self.LATCH_STATE] == self.LATCH_LATCHED:
            self.analog_latch_table[pin] = [0, 0, 0, 0, 0]
        self.data_lock.release()
        return current_latch_data


    def get_digital_latch_data(self, pin):
        """
        This method reads the digital latch table for the specified pin and returns a list that contains:
        [latch_state, latched_data, and time_stamp].
        If the latch state is latched, the entry in the table is cleared
        @param pin:  pin number
        @return: [latch_state, latched_data, and time_stamp]
        """
        self.data_lock.acquire(True)
        pin_data = self.digital_latch_table[pin]
        current_latch_data = [pin,
                              pin_data[self.LATCH_STATE],
                              pin_data[self.DIGITAL_LATCHED_DATA],
                              pin_data[self.DIGITAL_TIME_STAMP]]
        if pin_data[self.LATCH_STATE] == self.LATCH_LATCHED:
            self.digital_latch_table[pin] = [0, 0, 0, 0]
        self.data_lock.release()
        return current_latch_data


    def report_firmware(self, data):
        """
        This method processes the report firmware message,  sent asynchronously by Firmata when it starts up
        or after refresh_report_firmware() is called
        
        Use the api method api_get_firmware_version to retrieve this information
        @param data: Message data from Firmata
        @return: No return value.
        """
        self.firmata_firmware.append(data[0])  # add major
        self.firmata_firmware.append(data[1])  # add minor

        # extract the file name string from the message
        # file name is in bytes 2 to the end
        name_data = data[2:]

        # constructed file name
        file_name = []

        # the file name is passed in with each character as 2 bytes, the high order byte is equal to 0
        # so skip over these zero bytes
        for i in name_data[::2]:
            file_name.append(chr(i))

        # add filename to tuple
        self.firmata_firmware.append("".join(file_name))

    def analog_message(self, data):
        """
        This method handles the incoming analog data message.
        It stores the data value for the pin in the analog response table.
        It checks to see if the
        @param data: Message data from Firmata
        @return: No return value.
        """
        self.data_lock.acquire(True)

        # convert MSB and LSB into an integer
        self.analog_response_table[data[self.RESPONSE_TABLE_MODE]][self.RESPONSE_TABLE_PIN_DATA_VALUE] \
            = (data[self.MSB] << 7) + data[self.LSB]

        pin = data[0]
        pin_response_data_data = self.analog_response_table[pin]
        value = pin_response_data_data[self.RESPONSE_TABLE_PIN_DATA_VALUE]
        # check if data is to be latched
        # get the analog latching table entry for this pin
        latching_entry = self.analog_latch_table[pin]
        if latching_entry[self.LATCH_STATE] == self.LATCH_ARMED:
            # Has the latching criteria been met
            if latching_entry[self.LATCHED_THRESHOLD_TYPE] == self.ANALOG_LATCH_GT:
                if value > latching_entry[self.ANALOG_LATCH_DATA_TARGET]:
                    updated_latch_entry = latching_entry
                    updated_latch_entry[self.LATCH_STATE] = self.LATCH_LATCHED
                    updated_latch_entry[self.ANALOG_LATCHED_DATA] = value
                    # time stamp it
                    updated_latch_entry[self.ANALOG_TIME_STAMP] = time.time()
                    self.analog_latch_table[pin] = updated_latch_entry
                else:
                    pass # haven't hit target
            elif latching_entry[self.LATCHED_THRESHOLD_TYPE] == self.ANALOG_LATCH_GTE:
                if value >= latching_entry[self.ANALOG_LATCH_DATA_TARGET]:
                    updated_latch_entry = latching_entry
                    updated_latch_entry[self.LATCH_STATE] = self.LATCH_LATCHED
                    updated_latch_entry[self.ANALOG_LATCHED_DATA] = value
                    # time stamp it
                    updated_latch_entry[self.ANALOG_TIME_STAMP] = time.time()
                    self.analog_latch_table[pin] = updated_latch_entry
                else:
                    pass # haven't hit target:
            elif latching_entry[self.LATCHED_THRESHOLD_TYPE] == self.ANALOG_LATCH_LT:
                if value < latching_entry[self.ANALOG_LATCH_DATA_TARGET]:
                    updated_latch_entry = latching_entry
                    updated_latch_entry[self.LATCH_STATE] = self.LATCH_LATCHED
                    updated_latch_entry[self.ANALOG_LATCHED_DATA] = value
                    # time stamp it
                    updated_latch_entry[self.ANALOG_TIME_STAMP] = time.time()
                    self.analog_latch_table[pin] = updated_latch_entry
                else:
                    pass # haven't hit target:
            elif latching_entry[self.LATCHED_THRESHOLD_TYPE] == self.ANALOG_LATCH_LTE:
                if value <= latching_entry[self.ANALOG_LATCH_DATA_TARGET]:
                    updated_latch_entry = latching_entry
                    updated_latch_entry[self.LATCH_STATE] = self.LATCH_LATCHED
                    updated_latch_entry[self.ANALOG_LATCHED_DATA] = value
                    # time stamp it
                    updated_latch_entry[self.ANALOG_TIME_STAMP] = time.time()
                    self.analog_latch_table[pin] = updated_latch_entry
                else:
                    pass # haven't hit target:
            else:
                pass
        self.data_lock.release()

    def digital_message(self, data):
        """
        This method handles the incoming digital message.
        It stores the data values in the digital response table.
        Data is stored for all 8 bits of a  digital port
        @param data: Message data from Firmata
        @return: No return value.
        """
        port = data[0]
        port_data = (data[self.MSB] << 7) + data[self.LSB]

        # set all the pins for this reporting port
        # get the first pin number for this report
        pin = port * 8
        for pin in range(pin, pin + 8):
            # shift through all the bit positions and set the digital response table
            self.data_lock.acquire(True)
            self.digital_response_table[pin][self.RESPONSE_TABLE_PIN_DATA_VALUE] = port_data & 0x01
            # determine if the latch data table needs to be updated for each pin
            latching_entry = self.digital_latch_table[pin]
            if latching_entry[self.LATCH_STATE] == self.LATCH_ARMED:
                if latching_entry[self.LATCHED_THRESHOLD_TYPE] == self.DIGITAL_LATCH_LOW:
                    if (port_data & 0x01) == 0:
                        updated_latch_entry = latching_entry
                        updated_latch_entry[self.LATCH_STATE] = self.LATCH_LATCHED
                        updated_latch_entry[self.DIGITAL_LATCHED_DATA] = self.DIGITAL_LATCH_LOW
                        # time stamp it
                        updated_latch_entry[self.DIGITAL_TIME_STAMP] = time.time()
                    else:
                        pass
                elif latching_entry[self.LATCHED_THRESHOLD_TYPE] == self.DIGITAL_LATCH_HIGH:
                    if port_data & 0x01:
                        updated_latch_entry = latching_entry
                        updated_latch_entry[self.LATCH_STATE] = self.LATCH_LATCHED
                        updated_latch_entry[self.DIGITAL_LATCHED_DATA] = self.DIGITAL_LATCH_HIGH
                        # time stamp it
                        updated_latch_entry[self.DIGITAL_TIME_STAMP] = time.time()
                    else:
                        pass
            else:
                pass

            self.data_lock.release()
            # get the next data bit
            port_data >>= 1

    def encoder_data(self, data):
        """
        This method handles the incoming encoder data message and stores
        the data in the response table.
        @param data: Message data from Firmata
        @return: No return value.
        """
        val = int((data[self.MSB] << 7) + data[self.LSB])
        # set value so that it shows positive and negative values
        if val > 8192:
            val -= 16384
        self.data_lock.acquire(True)
        self.digital_response_table[data[self.RESPONSE_TABLE_MODE]][self.RESPONSE_TABLE_PIN_DATA_VALUE] = val
        self.data_lock.release()

    def sonar_data(self, data):
        """
        This method handles the incoming sonar data message and stores
        the data in the response table.
        @param data: Message data from Firmata
        @return: No return value.
        """
        val = int((data[self.MSB] << 7) + data[self.LSB])
        pin_number = data[0]
        self.data_lock.acquire(True)
        self.active_sonar_map[pin_number] = val
        # also write it into the digital response table
        self.digital_response_table[data[self.RESPONSE_TABLE_MODE]][self.RESPONSE_TABLE_PIN_DATA_VALUE] = val
        self.data_lock.release()

    def get_analog_response_table(self):
        """
        This method returns the entire analog response table to the caller
        @return: The analog response table.
        """
        self.data_lock.acquire(True)
        data = self.analog_response_table
        self.data_lock.release()
        return data

    def get_digital_response_table(self):
        """
        This method returns the entire digital response table to the caller
        @return: The digital response table.
        """
        self.data_lock.acquire(True)
        data = self.digital_response_table
        self.data_lock.release()
        return data


    def send_sysex(self, sysex_command, sysex_data=None):
        """
        This method will send a Sysex command to Firmata with any accompanying data

        @param sysex_command: sysex command
        @param sysex_data: data for command
        @return : No return value.
        """
        if not sysex_data:
            sysex_data = []

        # convert the message command and data to characters
        sysex_message = chr(self.START_SYSEX)
        sysex_message += chr(sysex_command)
        if len(sysex_data):
            for d in sysex_data:
                sysex_message += chr(d)
        sysex_message += chr(self.END_SYSEX)

        for data in sysex_message:
            self.transport.write(data)

    def send_command(self, command):
        """
        This method is used to transmit a non-sysex command.
        @param command: Command to send to firmata includes command + data formatted by caller
        @return : No return value.
        """
        send_message = ""
        for i in command:
            send_message += chr(i)

        for data in send_message:
            self.transport.write(data)

    def system_reset(self):
        """
        Send the reset command to the Arduino.
        It resets the response tables to their initial values
        @return: No return value
        """
        data = chr(self.SYSTEM_RESET)
        self.transport.write(data)

        # response table re-initialization
        # for each pin set the mode to input and the last read data value to zero
        self.data_lock.acquire(True)

        # remove all old entries from existing tables
        for _ in range(len(self.digital_response_table)):
            self.digital_response_table.pop()

        for _ in range(len(self.analog_response_table)):
            self.analog_response_table.pop()

        # reinitialize tables
        for pin in range(0, self.total_pins_discovered):
            response_entry = [self.INPUT, 0]
            self.digital_response_table.append(response_entry)

        for pin in range(0, self.number_of_analog_pins_discovered):
            response_entry = [self.INPUT, 0]
            self.analog_response_table.append(response_entry)

        self.data_lock.release()

        time.sleep(2)


    #noinspection PyMethodMayBeStatic
    # keeps pycharm happy
    def _string_data(self, data):
        """
        This method handles the incoming string data message from Firmata.
        The string is printed to the console

        @param data: Message data from Firmata
        @return: No return value.s
        """
        print "_string_data:"
        string_to_print = []
        for i in data[::2]:
            string_to_print.append(chr(i))
        print string_to_print

    def i2c_reply(self, data):
        """
        This method receives replies to i2c_read requests. It stores the data for each i2c device
        address in a dictionary called i2c_map. The data is retrieved via a call to i2c_get_read_data()
        in pymata.py
        @param data: raw data returned from i2c device
        """
        reply_data = []
        address = (data[0] & 0x7f) + (data[1] << 7)
        register = data[2] & 0x7f + data[3] << 7
        reply_data.append(register)
        for i in xrange(4, len(data), 2):
            data_item = (data[i] & 0x7f) + (data[i + 1] << 7)
            reply_data.append(data_item)
        self.i2c_map[address] = reply_data

    def capability_response(self, data):
        """
        This method handles a capability response message and stores the results to be retrieved
        via get_capability_query_results() in pymata.py
        @param data: raw capability data
        """
        self.capability_query_results = data

    def pin_state_response(self, data):
        """
        This method handles a pin state response message and stores the results to be retrieved
        via get_pin_state_query_results() in pymata.py
        @param data:  raw pin state data
        """
        self.last_pin_query_results = data

    def analog_mapping_response(self, data):
        """
        This method handles an analog mapping query response message and stores the results to be retrieved
        via get_analog_mapping_request_results() in pymata.py
        @param data: raw analog mapping data
        """
        self.analog_mapping_query_results = data


    def run(self):
        """
        This method starts the thread that continuously runs to receive and interpret
        messages coming from Firmata. This must be the last method in this file

        It also checks the deque for messages to be sent to Firmata.
        """

        # To add a command to the command dispatch table, append here.
        self.command_dispatch.update({self.REPORT_VERSION: [self.report_version, 2]})
        self.command_dispatch.update({self.REPORT_FIRMWARE: [self.report_firmware, 1]})
        self.command_dispatch.update({self.ANALOG_MESSAGE: [self.analog_message, 2]})
        self.command_dispatch.update({self.DIGITAL_MESSAGE: [self.digital_message, 2]})
        self.command_dispatch.update({self.ENCODER_DATA: [self.encoder_data, 3]})
        self.command_dispatch.update({self.SONAR_DATA: [self.sonar_data, 3]})
        self.command_dispatch.update({self.STRING_DATA: [self._string_data, 2]})
        self.command_dispatch.update({self.I2C_REPLY: [self.i2c_reply, 2]})
        self.command_dispatch.update({self.CAPABILITY_RESPONSE: [self.capability_response, 2]})
        self.command_dispatch.update({self.PIN_STATE_RESPONSE: [self.pin_state_response, 2]})
        self.command_dispatch.update({self.ANALOG_MAPPING_RESPONSE: [self.analog_mapping_response, 2]})

        while 1:  # a forever loop
            if len(self.command_deque):
                # get next byte from the deque and process it
                data = self.command_deque.popleft()

                # this list will be populated with the received data for the command
                command_data = []

                # process sysex commands
                if data == self.START_SYSEX:
                    # next char is the actual sysex command
                    # wait until we can get data from the deque
                    while len(self.command_deque) == 0:
                        pass
                    sysex_command = self.command_deque.popleft()
                    # retrieve the associated command_dispatch entry for this command
                    dispatch_entry = self.command_dispatch.get(sysex_command)

                    # get a "pointer" to the method that will process this command
                    method = dispatch_entry[0]

                    # now get the rest of the data excluding the END_SYSEX byte
                    end_of_sysex = False
                    while not end_of_sysex:
                        # wait for more data to arrive
                        while len(self.command_deque) == 0:
                            pass
                        data = self.command_deque.popleft()
                        if data != self.END_SYSEX:
                            command_data.append(data)
                        else:
                            end_of_sysex = True

                            # invoke the method to process the command
                            method(command_data)
                            # go to the beginning of the loop to process the next command
                    continue

                #is this a command byte in the range of 0x80-0xff - these are the non-sysex messages
                elif 0x80 <= data <= 0xff:
                    # look up the method for the command in the command dispatch table
                    # for the digital reporting the command value is modified with port number
                    # the handler needs the port to properly process, so decode that from the command and
                    # place in command_data
                    if 0x90 <= data <= 0x9f:
                        port = data & 0xf
                        command_data.append(port)
                        data = 0x90
                    # the pin number for analog data is embedded in the command so, decode it
                    elif 0xe0 <= data <= 0xef:
                        pin = data & 0xf
                        command_data.append(pin)
                        data = 0xe0
                    else:
                        pass

                    dispatch_entry = self.command_dispatch.get(data)

                    # this calls the method retrieved from the dispatch table
                    method = dispatch_entry[0]

                    # get the number of parameters that this command provides
                    num_args = dispatch_entry[1]

                    #look at the number of args that the selected method requires
                    # now get that number of bytes to pass to the called method
                    for i in range(num_args):
                        while len(self.command_deque) == 0:
                            pass
                        data = self.command_deque.popleft()
                        command_data.append(data)
                        #go execute the command with the argument list
                    method(command_data)

                    # go to the beginning of the loop to process the next command
                    continue







