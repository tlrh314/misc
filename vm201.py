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


commands = {'TX': '\x02',
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
            'LEN_CMD_TMR_ENA': 6,
            'CMD_TMR_DIS': 'D',
            'LEN_CMD_TMR_DIS': 6,
            'CMD_TMR_TOGGLE': 'G',
            'LEN_CMD_TMR_TOGGLE': 6
            }


def convert_and_check_response(t, packet_length):
    if len(t) != packet_length:
        print 'Error: expected: {0} bytes in packet; got: {1} bytes.'\
            .format(packet_length, len(t))
        sys.exit()

    all_bytes_as_integers = list()
    for byte in t:
        all_bytes_as_integers.append(ord(byte))

    return all_bytes_as_integers


def connect_to_vm201(host, port=9760, username=None, password=None):
    '''
    Connect to vm201 via TCP protocol
    @param host: string; hostname or ip-address.
    @param port: integer, default is 9760.
    @param username: connecting could require authentication.

    @return socket
    '''

    packet_length = commands['LEN_CMD_AUTH']  # Equal to LEN_CMD_LOGGED_IN.

    # create an INET, STREAMing socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print 'Failed to create socket'
        sys.exit()
    else:
        print 'Socket Created'

    try:
        remote_ip = socket.gethostbyname(host)
        s.connect((host, port))
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
        print 'Socket Connected to ' + host + ' on ip ' + remote_ip

    try:
        t = s.recv(packet_length)
    except Exception, e:
        # I have no idea whatsoever what could go wrong =)...
        raise
        print 'Error: something went wrong in recv function in {0}!'\
            .format('connect_to_vm201')
        sys.exit()

    response = convert_and_check_response(t, packet_length)

    # Succesfully logged in: <STX><5><CMD_LOGGED_IN><CHECKSUM><ETX>
    if response[2] == ord(commands['CMD_LOGGED_IN']):
        print 'Received CMD_LOGGED_IN'
    # Authentication needed: <STX><5><CMD_AUTH><CHECKSUM><ETX>
    elif response[2] == ord(commands['CMD_AUTH']):
        print 'Received CMD_AUTH'
        print 'To implement!'
    else:
        print 'Error:Received strange command from the server'
        sys.exit()

    return s


def receive_names_of_channels(s):
    '''
    Expected server response:
    <STX><22><CMD_NAME><Channelnr><char1 name>...<char16 of name><CHECKSUM><ETX>

    @param s: socket
    @return: dict -> keys: int (channel id); values: str (channel name)
    '''

    packet_length = commands['LEN_CMD_NAME']
    channel_names = dict()

    # First 8 output channels, then 1 input channel.
    for channel in range(9):
        try:
            t = s.recv(packet_length)
        except Exception, e:
            # I have no idea whatsoever what could go wrong =)...
            raise
            print 'Error: something went wrong in recv function in {0}!'\
                .format('receive_names_of_channels')
            sys.exit()

        response = convert_and_check_response(t, packet_length)
        if response[2] == ord(commands['CMD_NAME']):
            print 'Received CMD_NAME'
            channel_id = response[3]
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
            channel_names[channel_id] = name

    return channel_names


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


def receive_status_of_channels(s):
    '''
    Expected server response:
    <STX><8><CMD_STATUS><output status><output timer status><input status><CHECKSUM><ETX>

    @param s: socket
    @return tuple of dict1, dict2, int
        dict1 -> keys: int (channel id); values: int (channel output status)
        dict2 -> keys: int (channel id); values: int (channel timer status)
        int -> input_status: 0=off; 1=on
    '''
    packet_length = commands['LEN_CMD_STATUS']
    output_status = dict()
    timer_status = dict()

    try:
        t = s.recv(packet_length)
    except Exception, e:
        # I have no idea whatsoever what could go wrong =)...
        raise
        print 'Error: something went wrong in recv function in {0}!'\
            .format('receive_status_of_channels')
        sys.exit()

    response = convert_and_check_response(t, packet_length)
    if response[2] == ord(commands['CMD_STATUS']):
        print 'Received CMD_STATUS'
        output_string = bin(response[3])
        timer_string = bin(response[4])
        input_status = response[5]

    # The string is now channel 8...1, but we want 1..8
    output_string = output_string[::-1]
    timer_string = timer_string[::-1]

    for i in range(8):
        output_status[i+1] = output_string[i]
        timer_status[i+1] = timer_string[i]

    return output_status, timer_status, input_status


def print_channels(channel_names, state_of_system):
    output_status, timer_status, input_status = state_of_system

    header = ['Name', 'Output', 'Timer']
    table = list()

    for i in range(1, 9):
        table.append(([channel_names[i], output_status[i], timer_status[i]]))

    table.append(['', '', ''])
    table.append(['Input', input_status, '-'])
    print '\n' + tabulate(table, header, "rst") + '\n'


def send_command_to_vm201():
    print "Not implemented yet"
    return None


def main(host, port=9760, username=None, password=None):
    s = connect_to_vm201(host, port, username, password)
    print_channels(receive_names_of_channels(s), receive_status_of_channels(s))

    print "Disconnecting from the server"
    s.close()


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
        print 'Assmuming default port is used. user={0}, password={1}'.\
             format(sys.argv[2], sys.argv[3])
        main(sys.argv[1], 9760, sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 5:
        # hostname, port and username+password given
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4])
