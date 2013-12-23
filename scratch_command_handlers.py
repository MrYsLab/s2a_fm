# -*- coding: utf-8 -*-

"""
Created on Wed Nov  25 13:17:15 2013

@author: Alan Yorinks
Copyright (c) 2013 Alan Yorinks All right reserved.

@co-author: Sjoerd Dirk Meijer, fromScratchEd.nl (language support)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""

import logging
import datetime

class ScratchCommandHandlers:
    """
    This class processes any command received from Scratch 2.0

    If commands need to be added in the future, a command handler method is
    added to this file and the command_dict at the end of this file is
    updated to contain the method. Command names must be the same in the json .s2e Scratch
    descriptor file.
    """
    #Add your own translation to this list and make a new s2a_fm.s2e file with your translation
    ln_languages = ['English', 'Dutch (NL)'] #just for reference
    ln_ENABLE = ['Enable', 'aan']
    ln_DISABLE = ['Disable', 'uit']
    ln_INPUT = ['Input', 'ingang']
    ln_OUTPUT = ['Output', 'uitgang']
    ln_PWM = ['PWM', 'PWM']
    ln_SERVO = ['Servo' , 'servo']
    ln_TONE = ['Tone', 'toon']
    ln_OFF = ['Off', 'uitgeschakeld']
    ln_ON = ['On', 'ingeschakeld']

    # pin counts for the board
    total_pins_discovered = 0
    number_of_analog_pins_discovered = 0

    # lists to keep track of which pins need to be included in the poll responses
    digital_poll_list = []
    analog_poll_list = []

    # detected pin capability map
    pin_map = {}

    # instance variable for PyMata
    firmata = None

    # debug state - 0 == off and 1 == on
    debug = 0

    # base report string to be modified in response to a poll command
    # PIN and VALUE will be replaced with pin number and the current value for the pin
    digital_reporter_base = 'digital_read/PIN VALUE'
    analog_reporter_base = 'analog_read/PIN VALUE'

    # convenience definition for cr + lf
    end_of_line = "\r\n"

    # indices into the command list sent to each command method
    CMD_COMMAND = 0  # this is the actual command
    CMD_ENABLE_DISABLE = 1  # enable or disable pin
    CMD_PIN = 1  # pin number for all commands except the Enable/Disable
    CMD_PIN_ENABLE_DISABLE = 2
    CMD_DIGITAL_MODE = 3  # pin mode
    CMD_VALUE = 2  # value pin to be set to
    CMD_TONE_FREQ = 2  # frequency for tone command
    CMD_TONE_DURATION = 3  # tone duration
    CMD_SERVO_DEGREES = 2  # number of degrees for servo position
    CMD_DEBUG = 1 # debugger on or off

    def check_CMD_ENABLE_DISABLE(self, command):
        if command in self.ln_ENABLE:
            return 'Enable'
        if command in self.ln_DISABLE:
            return 'Disable'

    def check_CMD_DIGITAL_MODE(self, command):
        if command in self.ln_INPUT:
            return 'Input'
        if command in self.ln_OUTPUT:
            return 'Output'
        if command in self.ln_PWM:
            return 'PWM'
        if command in self.ln_SERVO:
            return 'Servo'
        if command in self.ln_TONE:
            return 'Tone'

    def check_DEBUG(self, command):
        if command in self.ln_OFF:
            return 'Off'
        if command in self.ln_ON:
            return 'On'
    

    def __init__(self, firmata, com_port, total_pins_discovered, number_of_analog_pins_discovered):
        """
        The class constructor creates the pin lists for the pins that will report
        data back to Scratch as a result of a poll request.
        @param total_pins_discovered:
        @param number_of_analog_pins_discovered:
        """
        self.firmata = firmata  
        self.com_port = com_port
        self.total_pins_discovered = total_pins_discovered
        self.number_of_analog_pins_discovered = number_of_analog_pins_discovered
        self.first_poll_received = False
        self.debug = 0


        # Create a pin list for poll data based on the total number of pins( digital table)
        # and a pin list for the number of analog pins.
        # Pins will be marked using Firmata Pin Types

        for x in range(self.total_pins_discovered):
            self.digital_poll_list.append(self.firmata.IGNORE)

        for x in range(self.number_of_analog_pins_discovered):
            self.analog_poll_list.append(self.firmata.IGNORE)

    def do_command(self, command):
        """
        This method looks up the command that resides in element zero of the command list
        within the command dictionary and executes the method for the command.
        Each command returns string that will be eventually be sent to Scratch
        @param command: This is a list containing the Scratch command and all its parameters
        @return: String to be returned to Scratch via HTTP
        """
        method = self.command_dict.get( command[0])
        if command[0] != "poll":
            # turn on debug logging if requested
            if self.debug == 'On':
                debug_string = "DEBUG: "
                debug_string += str(datetime.datetime.now())
                debug_string += ": "
                for data in command:
                    debug_string += "".join(map(str, data))
                    debug_string += ' '
                logging.debug(debug_string)
                print debug_string
        return method(self, command)

    #noinspection PyUnusedLocal
    def poll(self, command):
        # look for first poll and when received let the world know we are ready!
        """
        This method scans the data tables and assembles data for all reporter
        blocks and returns the data to the caller.
        @param command: This is a list containing the Scratch command and all its parameters It is unsused
        @return: 'okay'
        """
        if not self.first_poll_received :
            logging.info('Scratch detected! Ready to rock and roll...')
            print 'Scratch detected! Ready to rock and roll...'
            self.first_poll_received = True

        # assemble all output pin reports

        # first get the current digital and analog pin values from firmata
        digital_response_table = self.firmata.get_digital_response_table()
        analog_response_table = self.firmata.get_analog_response_table()

        # for each pin in the poll list that is set as an INPUT,
        # retrieve the pins value from the response table and build the response
        # string

        # digital first
        responses = ''
        for pin in range(self.total_pins_discovered):
            if self.digital_poll_list[pin] == self.firmata.INPUT:
                pin_number = str(pin)
                pin_entry = digital_response_table[pin]
                value = str(pin_entry[1])
                report_entry = self.digital_reporter_base
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

        # now check for any analog reports to be added
        for pin in range(self.number_of_analog_pins_discovered):
            if self.analog_poll_list[pin] != self.firmata.IGNORE:
                pin_number = str(pin)
                pin_entry = analog_response_table[pin]
                value = str(pin_entry[1])
                report_entry = self.analog_reporter_base
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line
        if responses == '':
            responses = 'okay'
        return responses

    #noinspection PyUnusedLocal
    def send_cross_domain_policy(self, command):
        """
        This method returns cross domain policy back to Scratch upon request.
        It keeps Flash happy.
        @param command: Command and all possible parameters in list form
        @return: policy string
        """
        policy = "<cross-domain-policy>\n"
        policy += "  <allow-access-from domain=\"*\" to-ports=\""
        policy += str(self.com_port)
        policy += "\"/>\n"
        policy += "</cross-domain-policy>\n\0"
        return policy

    #noinspection PyUnusedLocal
    def reset_arduino(self, command):
        """
        This method will send the reset command to the arduino and the poll tables
        @param command: Command and all possible parameters in list form
        @return: 'okay'
        """
        # reset the tables
        for x in range(self.total_pins_discovered):
            self.digital_poll_list[x] = self.firmata.IGNORE

        for x in range(self.number_of_analog_pins_discovered):
            self.analog_poll_list[x] = self.firmata.IGNORE
        self.firmata.reset()
        self.debug = 0
        return 'okay'

    def digital_pin_mode(self, command):
        """
        This method will set the poll list table appropriately and
        send the arduino a set_pin  configuration message.
        @param command: Command and all possible parameters in list form
        @return: 'okay'
        """
        if command[self.CMD_PIN_ENABLE_DISABLE] == 'PIN':
            logging.debug('digital_pin_mode: The pin number must be set to a numerical value')
            print 'digital_pin_mode: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN_ENABLE_DISABLE])

        # test for a valid pin number
        if pin >= self.total_pins_discovered:
            logging.debug('digital_pin_mode: pin %d exceeds number of pins on board' % pin)
            print 'digital_pin_mode: pin %d exceeds number of pins on board' % pin
            return 'okay'
        # ok pin is range, but make
        else:
            # now test for enable or disable

            if self.check_CMD_ENABLE_DISABLE(command[self.CMD_ENABLE_DISABLE]) == 'Enable':
                # choices will be input or some output mode
                if self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Input':
                    if self.valid_digital_pin_mode_type(pin, self.firmata.INPUT):
                        # set the digital poll list for the pin
                        self.digital_poll_list[pin] = self.firmata.INPUT
                        # send the set request to the Arduino
                        self.firmata.set_pin_mode( pin, self.firmata.INPUT, self.firmata.DIGITAL)
                    else:
                        logging.debug('digital_pin_mode: Pin %d does not support INPUT mode'% pin)
                        print 'digital_pin_mode: Pin %d does not support INPUT mode '% pin
                        return 'okay'
                else:
                    # an output mode, so just clear the poll bit
                    if self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Output':
                        if self.valid_digital_pin_mode_type(pin, self.firmata.OUTPUT):
                            self.digital_poll_list[pin] = self.firmata.OUTPUT
                            self.firmata.set_pin_mode( pin, self.firmata.OUTPUT, self.firmata.DIGITAL)
                        else:
                            logging.debug('digital_pin_mode: Pin %d does not support OUTPUT mode' % pin)
                            print 'digital_pin_mode: Pin %d does not support OUTPUT mode' % pin
                            return 'okay'
                    elif self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'PWM':
                        if self.valid_digital_pin_mode_type(pin, self.firmata.PWM):
                            self.digital_poll_list[pin] = self.firmata.PWM
                            self.firmata.set_pin_mode( pin, self.firmata.PWM, self.firmata.DIGITAL)
                        else:
                            logging.debug('digital_pin_mode: Pin %d does not support PWM mode' % pin)
                            print 'digital_pin_mode: Pin %d does not support PWM mode' % pin
                            return 'okay'
                    elif self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Tone':
                        # Tone can be on any pin so we look for OUTPUT
                        if self.valid_digital_pin_mode_type(pin, self.firmata.OUTPUT):
                            self.digital_poll_list[pin] = self.digital_poll_list[pin] = self.firmata.TONE_TONE
                            self.firmata.set_pin_mode( pin, self.firmata.OUTPUT, self.firmata.DIGITAL)
                        else:
                            logging.debug('digital_pin_mode: Pin %d does not support TONE mode' % pin)
                            print 'digital_pin_mode: Pin %d does not support TONE mode' % pin
                            return 'okay'
                    elif self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Servo':
                        if self.valid_digital_pin_mode_type(pin, self.firmata.SERVO):
                            self.digital_poll_list[pin] = self.firmata.SERVO
                            self.firmata.servo_config(pin)
                        else:
                            logging.debug('digital_pin_mode: Pin %d does not support SERVO mode' % pin)
                            print 'digital_pin_mode: Pin %d does not support SERVO mode' % pin
                            return 'okay'
                    else:
                        logging.debug('digital_pin_mode: Unknown output mode')
                        print 'digital_pin_mode: Unknown output mode'
                        return 'okay'
            if self.check_CMD_ENABLE_DISABLE(command[self.CMD_ENABLE_DISABLE]) == 'Disable':
                # disable pin of any type by setting it to IGNORE in the table
                self.digital_poll_list[pin] = self.firmata.IGNORE
                # this only applies to Input pins. For all other pins we leave the poll list as is
                if self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Input':
                    # send a disable reporting message
                    self.firmata.disable_digital_reporting(pin)
            # normal http return for commands
            return 'okay'

    def valid_digital_pin_mode_type(self, pin, pin_mode):
        """
        This is a utility method to determine if the pin supports the pin mode
        @param pin: Pin number
        @param pin_mode: Pin Mode
        @return: True if the mode is supported or False if it not supported.
        """
        pin_modes = self.pin_map[pin]
        if pin_mode in pin_modes:
            return True
        else:
            return False


    def analog_pin_mode(self, command):
        """
        This method will set the poll list table appropriately and
        send the arduino the correct configuration message.
        @param command: Command and all possible parameters in list form
        @return: 'okay'
        """

        if command[self.CMD_PIN_ENABLE_DISABLE] == 'PIN':
            logging.debug('analog_pin_mode: The pin number must be set to a numerical value')
            print 'analog_pin_mode: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN_ENABLE_DISABLE])

        # Normally analog pins act as inputs only, but the DUE allow analog ins
        # test for a valid pin number
        if pin >= self.number_of_analog_pins_discovered:
            print 'analog_pin_mode: pin %d exceeds number of analog pins on board' % pin
            logging.debug('analog_pin_mode: pin %d exceeds number of analog pins on board' % pin)
            return 'okay'
        else:
            # now test for enable or disable
            if self.check_CMD_ENABLE_DISABLE(command[self.CMD_ENABLE_DISABLE]) == 'Enable':
                # enable the analog pin
                self.analog_poll_list[pin] = self.firmata.INPUT
                self.firmata.set_pin_mode( pin, self.firmata.INPUT, self.firmata.ANALOG)  
            else:
                # Set analog poll list entry for the pin to IGNORE.
                # Disable reporting
                self.analog_poll_list[pin] = self.firmata.IGNORE
                self.firmata.disable_analog_reporting(pin)  

        return 'okay'

    def digital_write(self, command):
        """
        This method outputs a 0 or a 1 to the designated digital pin that has been previously
        been configured as an output.

        If the pin is configured as an INPUT, writing a HIGH value with digitalWrite()
        will enable an internal 20K pullup resistor (see the tutorial on digital pins on arduino site).
        Writing LOW will disable the pullup. The pullup resistor is enough to light an LED dimly,
        so if LEDs appear to work, but very dimly, this is a likely cause.
        The remedy is to set the pin to an output.

        @param command: Command and all possible parameters in list form
        @return: okay
        """
        # test pin as a digital output pin in poll list table

        if command[self.CMD_PIN] == 'PIN':
            logging.debug('digital_write: The pin number must be set to a numerical value')
            print 'digital_write: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.OUTPUT:
            self.firmata.digital_write( pin, int(command[self.CMD_VALUE]))
            return 'okay'
        # for pullup - see description above
        elif self.digital_poll_list[pin] == self.firmata.INPUT:
            self.firmata.digital_write( pin, int(command[self.CMD_VALUE]))
            return 'okay'
        else:
            print 'digital write: Pin %d must be enabled before writing to it.' % pin
            logging.debug('digital write: Pin %d must be enabled before writing to it.' % pin)
            return 'okay'


    def analog_write(self, command):
        """
        This method write the value (0-255) to the digital pin that has been
        previously been specified as a PWM pin. NOTE: Pin number is the digital
        pin number and not an analog pin number.
        @param command: Command and all possible parameters in list form
        @return: okay or _problem
        """

        if command[self.CMD_PIN] == 'PIN':
            logging.debug('analog_write: The pin number must be set to a numerical value')
            print 'analog_write: The pin number must be set to a numerical value'
            return 'okay'

        if command[self.CMD_VALUE] == 'VAL':
            logging.debug('analog_write: The value field must be set to a numerical value')
            print 'analog_write: The value field must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.PWM:
            # check to make sure that the value is in the range of 0-255
            if 0 <= int(command[1]) <= 255:
                self.firmata.analog_write(pin, int(command[self.CMD_VALUE]))
                return 'okay'
            else:
                print 'analog_write data value %d is out of range. It should be between 0-255' % \
                      int(command[self.CMD_VALUE])
                logging.debug('analog_write data value %d is out of range. It should be between 0-255' %
                              int(command[self.CMD_VALUE]))
                return '_problem analog_write data value %d is out of range. It should be between 0-255' % \
                       int(command[self.CMD_VALUE])
        else:
            print'analog_write: Pin %d must be enabled before writing to it.' % pin
            logging.debug('analog_write: Pin %d must be enabled before writing to it.' % pin)
            return '_problem Pin must be enabled before writing to it.'

    def play_tone(self, command):
        # check to make sure pin was configured for tone
        """
        This method will play a tone for the specified pin in command
        @param command: Command and all possible parameters in list form
        @return: okay or _problem
        """
        if command[self.CMD_PIN] == 'PIN':
            logging.debug('play_tome: The pin number must be set to a numerical value')
            print 'play_tone: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.TONE_TONE:
            #noinspection PyUnusedLocal
            value = command[1]
            self.firmata.play_tone(pin, self.firmata.TONE_TONE, int(command[self.CMD_TONE_FREQ]),
                                   int(command[self.CMD_TONE_DURATION]))
            return 'okay'
        else:
            print 'play_tone: Pin %d was not enabled as TONE.' % pin
            logging.debug('play_tone: Pin %d was not enabled as TONE.' % pin)
            return 'okay'

    def tone_off(self, command):
       # check to make sure pin was configured for tone
        """
        This method will force tone to be off.
        @param command: Command and all possible parameters in list form
        @return: okay
        """
        if command[self.CMD_PIN] == 'PIN':
            logging.debug('tone_off: The pin number must be set to a numerical value')
            print 'tone_off: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.TONE_TONE:
            #noinspection PyUnusedLocal
            value = command[1]
            self.firmata.play_tone(pin, self.firmata.TONE_NO_TONE, 0, 0)  
            return 'okay'
        else:
            print 'tone_off: Pin %d was not enabled as TONE.' % pin
            logging.debug('tone_off: Pin %d was not enabled as TONE.' % pin)
            return 'okay'

    def debug_control(self, command):
        """
        This method controls command block debug logging
        @param command: Either On or Off
        @return: okay
        """
        self.debug = self.check_DEBUG(command[self.CMD_DEBUG])
        return 'okay'

    def set_servo_position(self, command):
        # check to make sure pin was configured for servo
        """
        This method will command the servo position if the digital pin was
        previously configured for Servo operation.
        A maximum of 180 degrees is allowed
        @param command: Command and all possible parameters in list form
        @return: okay
        """
        if command[self.CMD_PIN] == 'PIN':
            logging.debug('servo_position: The pin number must be set to a numerical value')
            print 'servo_position: The pin number must be set to a numerical value'
            return 'okay'
        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.SERVO:
            if 0 <= int(command[self.CMD_SERVO_DEGREES]) <= 180:
                self.firmata.analog_write(pin,  int(command[self.CMD_SERVO_DEGREES]))
                return 'okay'
            else:
                print "set_servo_position: Request of %d degrees. Servo range is 0 to 180 degrees" % int(command[1])
                logging.debug("set_servo_position: Request of %d degrees. Servo range is 0 to 180 degrees" % int(command[1]))
                return 'okay'
        else:
            print 'set_servo_position: Pin %d was not enabled for SERVO operations.' % pin
            logging.debug('set_servo_position: Pin %d was not enabled for SERVO operations.' % pin)
            return '_problem Pin was not enabled for SERVO operations.'


    # This table must be at the bottom of the file because Python does not provide forward referencing for
    # the methods defined above.
    command_dict = {'crossdomain.xml': send_cross_domain_policy, 'reset_all': reset_arduino,
                        'digital_pin_mode': digital_pin_mode,  "analog_pin_mode": analog_pin_mode,
                        "digital_write": digital_write, "analog_write": analog_write,
                        "play_tone": play_tone, "tone_off": tone_off,
                        "set_servo_position": set_servo_position, "poll": poll,
                        "debugger": debug_control
                        }
