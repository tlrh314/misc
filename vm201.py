#!/usr/bin/env python
# vm201.py
#
# Timo Halbesma
#
# Control VM201 ethernet relay card over TCP.
#
# October 8th, 2014
# Version 1.0: Read TCP responses.

import sys
import socket
# import struct
# import time

# http://txt.arboreus.com/2013/03/13/pretty-print-tables-in-python.html
from tabulate import tabulate


class Channel():
    def __init__(self):
        self.name = None
        self.status = None
        self.timer = None

    def __str__(self):
        return 'name={0}, status={1}, timer={2}'\
            .format(self.name, self.status, self.timer)

    def as_list(self):
        return [self.name, self.status, self.timer]


class VM201RelayCard():
    def __init__(self, host, port=9760, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.socket = None
        self.channels = dict()

        for i in range(1, 10):
            self.channels[i] = Channel()

        self.commands = {'TX': '\x02',
                         'ETX': '\x03',
                         'CMD_AUTH': 'A',
                         'LEN_CMD_AUTH': 5,
                         'CMD_USERNAME': 'U',
                         'LEN_CMD_USERNAME': 14,
                         'CMD_PASSWORD': 'W',
                         'LEN_CMD_PASSWORD': 14,
                         'CMD_LOGGED_IN': 'L',
                         'LEN_CMD_LOGGED_IN': 5,
                         'CMD_ACCESS_DENIED': 'X',
                         'LEN_CMD_ACCESS_DENIED': 5,
                         'CMD_CLOSED': 'C',
                         'LEN_CMD_CLOSED': 5,
                         'CMD_NAME': 'N',
                         'LEN_CMD_NAME': 22,
                         'CMD_STATUS_REQ': 'R',
                         'LEN_CMD_STATUS_REQ': 5,
                         'CMD_STATUS': 'S',
                         'LEN_CMD_STATUS': 8,
                         'CMD_ON': 'O',
                         'LEN_CMD_ON': 6,
                         'CMD_OFF': 'F',
                         'LEN_CMD_OFF': 6,
                         'CMD_TOGGLE': 'T',
                         'LEN_CMD_TOGGLE': 6,
                         'CMD_PULSE': 'P',
                         'LEN_CMD_PULSE': 8,
                         'CMD_UPDATE': 'V',
                         'LEN_CMD_UPDATE': 6,
                         'CMD_TMR_ENA': 'E',
                         'LEN_CMD_TMR_DIS': 6,
                         'CMD_TMR_TOGGLE': 'G',
                         'LEN_CMD_TMR_TOGGLE': 6
                         }

    def convert_and_check_response(self, t, packet_length):
        if len(t) != packet_length:
            print 'Error: expected: {0} bytes in packet; got: {1} bytes.'\
                .format(packet_length, len(t))
            sys.exit()

        all_bytes_as_integers = list()
        for byte in t:
            all_bytes_as_integers.append(ord(byte))

        return all_bytes_as_integers

    def connect(self):
        '''
        Connect to vm201 via TCP protocol

        '''

        # 'LEN_CMD_AUTH' is equal to 'LEN_CMD_LOGGED_IN'.
        packet_length = self.commands['LEN_CMD_AUTH']

        # create an INET, STREAMing socket
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print 'Failed to create socket'
            sys.exit()
        else:
            print 'Socket Created'

        try:
            remote_ip = socket.gethostbyname(self.host)
            self.socket.connect((self.host, self.port))
        except socket.gaierror:
            print 'Error in {0}: Hostname could not be resolved.'\
                .format('connect_to_vm201')
            sys.exit()
        except socket.error, e:
            print 'Error in {0}: {1}'\
                .format('connect_to_vm201', e)
            print 'Perhaps hostname or port incorrect? Please double check.'
            sys.exit()
        else:
            print 'Socket Connected to ' + self.host + ' on ip ' + remote_ip

        try:
            t = self.socket.recv(packet_length)
        except Exception, e:
            # I have no idea whatsoever what could go wrong =)...
            raise
            print 'Error: something went wrong in recv function in {0}!'\
                .format('connect_to_vm201')
            sys.exit()

        response = self.convert_and_check_response(t, packet_length)

        # Succesfully logged in: <STX><5><CMD_LOGGED_IN><CHECKSUM><ETX>
        if response[2] == ord(self.commands['CMD_LOGGED_IN']):
            print 'Received CMD_LOGGED_IN'
        # Authentication needed: <STX><5><CMD_AUTH><CHECKSUM><ETX>
        elif response[2] == ord(self.commands['CMD_AUTH']):
            print 'Received CMD_AUTH'
            print 'To implement!'
        else:
            print 'Error:Received strange command from the server'
            sys.exit()

    def disconnect(self):
        print "Disconnecting from the server"
        self.socket.close()

    def receive_names_of_channels(self):
        '''
        Expected server response:
        <STX><22><CMD_NAME><Channelnr><char1 name>...<char16 of name><CHECKSUM><ETX>
        '''

        packet_length = self.commands['LEN_CMD_NAME']

        # First 8 output channels, then 1 input channel.
        for i in range(1, 10):
            try:
                t = self.socket.recv(packet_length)
            except Exception, e:
                # I have no idea whatsoever what could go wrong =)...
                raise
                print 'Error: something went wrong in recv function in {0}!'\
                    .format('receive_names_of_channels')
                sys.exit()

            response = self.convert_and_check_response(t, packet_length)
            if response[2] == ord(self.commands['CMD_NAME']):
                print 'Received CMD_NAME'
                name = ''
                for char in response[4:20]:
                    # There appears to be buggy behaviour in the VM201 firmware.
                    # The channel names might have seemingly random chars added.
                    lowercase = (chr(char) >= 'a' and chr(char) <= 'z')
                    uppercase = (chr(char) >= 'A' and chr(char) <= 'Z')
                    # digit = (chr(char) >= 0 and chr(char) <= '9')
                    # space = (chr(char) == 32)
                    if uppercase or lowercase:
                        name += chr(char)
                self.channels[i].name = name

    def receive_status_of_channels(self):
        '''
        Expected server response:
        <STX><8><CMD_STATUS><output status><output timer status><input status><CHECKSUM><ETX>
        '''

        packet_length = self.commands['LEN_CMD_STATUS']

        try:
            t = self.socket.recv(packet_length)
        except Exception, e:
            # I have no idea whatsoever what could go wrong =)...
            raise
            print 'Error: something went wrong in recv function in {0}!'\
                .format('receive_status_of_channels')
            sys.exit()

        response = self.convert_and_check_response(t, packet_length)
        if response[2] == ord(self.commands['CMD_STATUS']):
            print 'Received CMD_STATUS'
            output_string = bin(response[3])
            timer_string = bin(response[4])
            input_status = response[5]

        # The string is now channel 8...1, but we want 1..8
        output_string = output_string[::-1]
        timer_string = timer_string[::-1]

        for i in range(8):
            self.channels[i+1].status = output_string[i]
            self.channels[i+1].timer = timer_string[i]

        self.channels[9].status = input_status
        self.channels[9].timer = '-'

    def __str__(self):
        header = ['Name', 'Output', 'Timer']
        table = list()

        for i in range(1, 10):
            table.append(self.channels[i].as_list())

        table.append(['', '', ''])
        state = '\n' + str(tabulate(table, header, "rst")) + '\n'

        return state

    # Checksum function in Pascal (Delphi ?)
    # function VM201Checksum(Data: array of Byte; Size: Integer): Byte;
    # var
    #  i: Integer;
    #    n: Byte;
    #    begin
    #      n := 0;
    #
    #        for i:=0 to Size-1 do
    #                n := n + Data[i];
    #
    #                  Result := (1 + (not ($FF and n)));
    #                  end;

    def send_command_to_vm201():
        print "Not implemented yet"
        return None


# http://www.gossamer-threads.com/lists/python/python/134741
def bin(i):
    ''' Return str of binary byte representation of given int i'''
    s = ''
    while i:
        s = (i & 1 and '1' or '0') + s
        i >>= 1
    while len(s) < 8:
        s = '0' + s
    return s or '0'


def main(host, port=9760, username=None, password=None):
    VM201 = VM201RelayCard(host, port, username, password)

    VM201.connect()
    VM201.receive_names_of_channels()
    VM201.receive_status_of_channels()
    print VM201
    VM201.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'Usage: python {0} hostname [port] [username password]'\
            .format(__file__)
        sys.exit()
    elif len(sys.argv) == 2:
        # hostname given (required)
        main(sys.argv[1])
    elif len(sys.argv) == 3:
        # hostname and port given.
        main(sys.argv[1], int(sys.argv[2]))
    elif len(sys.argv) == 4:
        # hostname and username+password given, thus, default port used.
        print 'Assmuming default port is used. user={0}, password={1}'\
            .format(sys.argv[2], sys.argv[3])
        main(sys.argv[1], 9760, sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 5:
        # hostname, port and username+password given
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4])
