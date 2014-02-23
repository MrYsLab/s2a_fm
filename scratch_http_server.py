# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 14:45:49 2013

@author: Alan Yorinks
Copyright (c) 2013-14 Alan Yorinks All right reserved.

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
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from string import split


class GetHandler(BaseHTTPRequestHandler):
    """
    This class contains the HTTP server that Scratch2 communicates with
    Scratch sends HTTP GET requests and this class processes the requests.

    HTTP GET requests are accepted and the appropriate command handler is
    called to process the command.
    """

    firmata = None

    # tcp server port - must match that in the .s2e descriptor file
    port = 50209

    # instance handle for the scratch command handler
    scratch_command_handler = None

    #indicator so that we can tell user Scratch is ready to go
    waiting_for_first_scratch_poll = True

    # this is a 'classmethod' because we need to set data before starting
    # the HTTP server.
    #noinspection PyMethodParameters
    @classmethod
    def set_items(self, firmata, scratch_command_handler):
        """
        This method stores the input parameters for later use.
        It is a class method, because these values need to established
        prior to instantiating the class
        """
        # instance variable for PyMata
        #noinspection PyAttributeOutsideInit
        self.firmata = firmata

        # instance variable for scratch command handler
        #noinspection PyAttributeOutsideInit
        self.command_handler = scratch_command_handler

    #noinspection PyPep8Naming
    def do_GET(self):
        """
        Scratch2 only sends HTTP GET commands. This method processes them.
        It differentiates between a "normal" command request and a request
        to send policy information to keep Flash happy on Scratch.
        (This may change when Scratch is converted to HTML 5
        """


        # skip over the / in the command
        cmd = self.path[1:]
        # create a list containing the command and all of its parameters
        cmd_list = split(cmd, '/')

        # get the command handler method for the command and call the handler
        # cmd_list[0] contains the command. look up the command method
        s = self.command_handler.do_command(cmd_list)

        self.send_resp(s)


    # we can't use the standard send_response since we don't conform to its
    # standards, so we craft our own response handler here
    def send_resp(self, response):
        """
        This method sends Scratch an HTTP response to an HTTP GET command.
        """

        crlf = "\r\n"
        # http_response = str(response + crlf)
        http_response = "HTTP/1.1 200 OK" + crlf
        http_response += "Content-Type: text/html; charset=ISO-8859-1" + crlf
        http_response += "Content-Length" + str(len(response)) + crlf
        http_response += "Access-Control-Allow-Origin: *" + crlf
        http_response += crlf
        #add the response to the nonsense above
        if response != 'okay':
            http_response += str(response + crlf)
        # send it out the door to Scratch
        self.wfile.write(http_response)

def start_server(firmata, command_handler):
    """
       This function populates class variables with essential data and
       instantiates the HTTP Server
    """

    GetHandler.set_items(firmata, command_handler)
    try:
        server = HTTPServer(('localhost', 50209), GetHandler)
        #server = HTTPServer(('', 50209), GetHandler)
        print 'Starting HTTP Server!'
        print 'Use <Ctrl-C> to exit the extension\n'
        print 'Please start Scratch or Snap!'
    except Exception:
        logging.debug('Exception in scratch_http_server.py: HTTP Socket may already be in use - restart Scratch')
        print 'HTTP Socket may already be in use - restart Scratch'
        raise
    try:
        #start the server
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('scratch_http_server.py: keyboard interrupt exception')
        print "Goodbye !"
        raise KeyboardInterrupt
    except Exception:
        logging.debug('scratch_http_server.py: Exception %s' % str(Exception))
        raise