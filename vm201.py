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
import struct
# import time

# http://txt.arboreus.com/2013/03/13/pretty-print-tables-in-python.html
from tabulate import tabulate


# https://stackoverflow.com/questions/2184181/decoding-tcp-packets-using-python
# NB in the end only inspired by this solution. Hardly any code remains.
class TCPPacketHandler(object):
    def __init__(self):
        pass

    # https://stackoverflow.com/questions/16822967/need-
    # assistance-in-calculating-checksum
    def calculate_checksum(self, s):
        '''
        Two-complement of the sum of all previous bytes in the packet.

        @param s: string of bytes; len(s) = number of bytes.
        @return: chechsum one byte stored in a string.
        '''

        return struct.pack('1B', (-(sum(ord(c) for c in s) % 256) & 0xFF))

    def checksum_is_valid(self, packet):
        ''' The last byte is ETX; secondlast byte is the checksum'''

        return packet[-2] == self.calculate_checksum(packet[:-2])

    def decode(self, vm201, packet):
        '''
        Decode a TCP packet to obtain CMD and data_x

        @param packet: string containing the bytes; TCP packet received.
        @return: list of integer values of the bytes. If checksum fails: None.
        '''

        cmd_byte = packet[2]
        length = ord(packet[1])

        print 'Received', vm201.lookup(cmd_byte)

        if not self.checksum_is_valid(packet):
            print 'Error: in TCPPacketHandler.decode(); invalid checksum!'
            sys.exit()

        if len(packet) != length:
            print 'Error: expected: {0} bytes in packet; got: {1} bytes.'\
                .format(length, len(packet))
            sys.exit()

        return list(struct.unpack('B'*length, packet))

    def encode(self, vm201, cmd, data_x=''):
        '''
        Encode a TCP packet given a cmd.
        Generic packets: <STX><LEN><CMD><data_1>...<data_n><CHECKSUM><ETX>

        @param cmd: CMD_FULL_NAME, as given in 'VM201.commands' dict.
        @param data_x: optional data bytes.
        @ return string containing the bytes; TCP packet ready to transmit.
        '''

        stx = vm201.commands['STX']
        length = struct.pack('1B', vm201.commands['LEN_'+cmd])
        cmd_byte = vm201.commands[cmd]

        # bool('') -> False. Encode called without data_x -> skip this block.
        if data_x:
            # data_x is padded with zeros until it has length 9.
            data_x += (9 - len(data_x)) * '\x00'

        # If data_x is not given, adding data_x = '' does not alter checksum.
        checksum = self.calculate_checksum(stx + length + cmd_byte + data_x)
        etx = vm201.commands['ETX']

        print 'Sending', cmd

        # If data_x is not given, adding data_x = '' does not alter packet.
        return stx + length + cmd_byte + data_x + checksum + etx


class Channel(object):
    def __init__(self):
        self.name = None
        self.status = None
        self.timer = None

    def __str__(self):
        return 'name={0}, status={1}, timer={2}'\
            .format(self.name, self.status, self.timer)

    def as_list(self):
        return [self.name, self.status, self.timer]


class VM201RelayCard(object):
    def __init__(self, host, port=9760, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        # Socket to communicatie over with the vm201 firmware.
        self.socket = None

        # Pre-defined commands stated in the protocol.
        self.commands = {'STX': '\x02',
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

        # Relay channels (8 output; 1 input)
        self.channels = dict()

        for i in range(1, 10):
            self.channels[i] = Channel()

        # TCP packet handler to decode and encode packets.
        self.tcp_handler = TCPPacketHandler()

    def lookup(self, cmd_byte):
        ''' Lookup key in self.commands dict given its value cmd_byte '''

        try:
            return [key for key in self.commands if
                    self.commands[key] == cmd_byte][0]
        except KeyError, e:
            print 'Error: value \'{0}\' not found'\
                .format(cmd_byte) + ' in VM201.commands dict!\n', e
            return None

    def login(self):
        '''
        Expected client answer to received CMD_AUTH::
        <STX><14><CMD_USERNAME><char1 of username>...<char9 of username><CHECKSUM><ETX>
        <STX><14><CMD_PASSWORD><char1 of password>...<char9 of password><CHECKSUM><ETX>

        Expected server response:
        invalid -> <STX><5><CMD_ACCESS_DENIED><CHECKSUM><ETX>
                -> <STX><5><CMD_CLOSED><CHECKSUM><ETX>
        succes -> <STX><5><CMD_LOGGED_IN><CHECKSUM><ETX>
        '''

        packet = self.tcp_handler.encode(self, 'CMD_USERNAME', self.username)
        self.socket.send(packet)

        packet = self.tcp_handler.encode(self, 'CMD_PASSWORD', self.password)
        self.socket.send(packet)

        # 'LEN_CMD_LOGGED_IN' = 'LEN_CMD_ACCESS_DENIED'  = 'LEN_CMD_CLOSED'
        packet_length = self.commands['LEN_CMD_LOGGED_IN']
        packet = self.socket.recv(packet_length)
        response = self.tcp_handler.decode(self, packet)
        login_status = self.lookup(chr(response[2]))

        if login_status == 'CMD_LOGGED_IN':
            print 'Authentication succes.'
        elif login_status == 'CMD_ACCESS_DENIED':
            print 'Authentication failure.'
            packet = self.socket.recv(packet_length)
            response = self.tcp_handler.decode(self, packet)
            sys.exit()


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
            print 'Socket Created.'

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
            packet = self.socket.recv(packet_length)
        except Exception, e:
            # I have no idea whatsoever what could go wrong =)...
            raise
            print 'Error: something went wrong in recv function in {0}!'\
                .format('connect_to_vm201')
            sys.exit()

        response = self.tcp_handler.decode(self, packet)
        login_status = self.lookup(chr(response[2]))
        if login_status == 'CMD_LOGGED_IN':
            # No auth required; no further steps needed.
            pass
        elif login_status == 'CMD_AUTH':
            self.login()
        else:
            print 'Error: unexpected server return {0}'.format(login_status)
            sys.exit()

    def disconnect(self):
        '''
        Expected by the server
        <STX><5><CMD_CLOSED><CHECKSUM><ETX>
        '''

        packet = self.tcp_handler.encode(self, 'CMD_CLOSED')
        self.socket.send(packet)

        length = self.commands['LEN_CMD_CLOSED']
        packet = self.socket.recv(length)
        self.tcp_handler.decode(self, packet)

        self.socket.close()
        print 'Socket Closed.'

        sys.exit()

    def receive_names_of_channels(self):
        '''
        Expected server response:
        <STX><22><CMD_NAME><Channelnr><char1 name>...<char16 of name><CHECKSUM><ETX>
        '''

        packet_length = self.commands['LEN_CMD_NAME']

        # First 8 output channels, then 1 input channel.
        for i in range(1, 10):
            try:
                packet = self.socket.recv(packet_length)
            except Exception, e:
                # I have no idea whatsoever what could go wrong =)...
                raise
                print 'Error: something went wrong in recv function in {0}!'\
                    .format('receive_names_of_channels')
                sys.exit()

            response = self.tcp_handler.decode(self, packet)

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
            packet = self.socket.recv(packet_length)
        except Exception, e:
            # I have no idea whatsoever what could go wrong =)...
            raise
            print 'Error: something went wrong in recv function in {0}!'\
                .format('receive_status_of_channels')
            sys.exit()

        response = self.tcp_handler.decode(self, packet)

        output_string = bin(response[3])
        timer_string = bin(response[4])
        input_status = response[5]

        # The string is now channel 8...1, but we want 1...8
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

        # table.append(['', '', ''])
        state = '\n' + str(tabulate(table, header, "rst")) + '\n'

        return state


    def send_status_request(self):
        '''
        Expected by the server
        <STX><5><CMD_STATUS_REQ><CHECKSUM><ETX>
        '''

        packet = self.tcp_handler.encode(self, 'CMD_STATUS_REQ')

        self.socket.send(packet)

    def status(self):
        self.receive_names_of_channels()
        self.receive_status_of_channels()
        print self



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
    VM201.status()
    VM201.send_status_request()
    VM201.status()
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
