'''
VM201RelayCard class.

Software representation of the VM201 Ethernet Relay Card.

Author: Timo Halbesma
Date: October 11th, 2014
Version: 2.0: Read TCP responses; send TCP packet to login and request status.
'''


from sys import exit
from socket import socket, AF_INET, SOCK_STREAM, gaierror, error, gethostbyname
from socket import timeout
from struct import pack


# http://txt.arboreus.com/2013/03/13/pretty-print-tables-in-python.html
from tabulate import tabulate

from Channel import Channel
from TCPPacketHandler import TCPPacketHandler
from Printer import Printer


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
                         'LEN_CMD_TMR_ENA': 6,
                         'CMD_TMR_DIS': 'D',
                         'LEN_CMD_TMR_DIS': 6,
                         'CMD_TMR_TOGGLE': 'G',
                         'LEN_CMD_TMR_TOGGLE': 6
                         }

        # Relay channels (8 output; 1 input)
        self.channels = dict()
        self.channel_string = str()
        self.timer_string = str()

        for i in range(1, 10):
            self.channels[i] = Channel()

        # TCP packet handler to decode and encode packets.
        self.tcp_handler = TCPPacketHandler()

        # Custum print handler
        self.display = Printer()

    def __str__(self):
        header = ['Name', 'Output', 'Timer']
        table = list()

        for i in range(1, 10):
            table.append(self.channels[i].as_list())

        # table.append(['', '', ''])
        state = '\n' + str(tabulate(table, header, "rst")) + '\n'

        return state

    def lookup(self, cmd_byte):
        ''' Lookup key in self.commands dict given its value cmd_byte '''

        try:
            return [key for key in self.commands if
                    self.commands[key] == cmd_byte][0]
        except KeyError, e:
            msg = 'Error: value \'{0}\' not found'\
                  .format(cmd_byte) + ' in VM201.commands dict!\n', e
            self.display.add_tcp_msg(msg)
            return None

    def connect(self):
        ''' Connect to vm201 via TCP protocol '''

        # 'LEN_CMD_AUTH' is equal to 'LEN_CMD_LOGGED_IN'.
        length = self.commands['LEN_CMD_AUTH']

        # create an INET, STREAMing socket
        try:
            self.socket = socket(AF_INET, SOCK_STREAM)
        except socket.error:
            msg = 'Failed to create socket'
            self.display.add_tcp_msg(msg)
            exit()
        else:
            self.display.add_tcp_msg('Socket Created.')

        try:
            remote_ip = gethostbyname(self.host)
            self.socket.connect((self.host, self.port))
        except gaierror:
            msg = 'Error in {0}: Hostname could not be resolved.'\
                .format('connect_to_vm201')
            self.display.add_tcp_msg(msg)
            exit()
        except error, e:
            msg = 'Error in {0}: {1}'\
                .format('connect_to_vm201', e)
            msg += '\nPerhaps hostname or port incorrect? Please double check.'
            self.display.add_tcp_msg(msg)
            exit()
        else:
            self.display.add_tcp_msg(
                'Socket Connected to ' + self.host + ' on ip ' + remote_ip)

        try:
            packet = self.socket.recv(length)
        except Exception, e:
            # I have no idea whatsoever what could go wrong =)...
            raise
            msg = 'Error: something went wrong in recv function in {0}!'\
                  .format('connect_to_vm201')
            self.display.add_tcp_msg(msg)
            exit()

        response = self.tcp_handler.decode(self, packet)
        login_status = self.lookup(chr(response[2]))
        if login_status == 'CMD_LOGGED_IN':
            # No auth required; no further steps needed.
            pass
        elif login_status == 'CMD_AUTH':
            self.login()
        else:
            msg = 'Error: unexpected server return {0}'.format(login_status)
            self.display.add_tcp_msg(msg)
            exit()

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

        if self.username is None or self.password is None:
            msg = 'Error: no username and/or password specified!'
            self.display.add_tcp_msg(msg)
            exit()

        packet = self.tcp_handler.encode(self, 'CMD_USERNAME', self.username)
        self.socket.send(packet)

        packet = self.tcp_handler.encode(self, 'CMD_PASSWORD', self.password)
        self.socket.send(packet)

        # 'LEN_CMD_LOGGED_IN' = 'LEN_CMD_ACCESS_DENIED'  = 'LEN_CMD_CLOSED'
        length = self.commands['LEN_CMD_LOGGED_IN']
        packet = self.socket.recv(length)
        response = self.tcp_handler.decode(self, packet)
        login_status = self.lookup(chr(response[2]))

        if login_status == 'CMD_LOGGED_IN':
            self.display.add_tcp_msg('Authentication succeeded.')
        elif login_status == 'CMD_ACCESS_DENIED':
            self.display.add_tcp_msg('Authentication failed.')
            packet = self.socket.recv(length)
            response = self.tcp_handler.decode(self, packet)
            exit()

    def receive_names_of_channels(self):
        '''
        Expected server response:
        <STX><22><CMD_NAME><Channelnr><char1 name>...<char16 of name><CHECKSUM><ETX>
        '''

        length = self.commands['LEN_CMD_NAME']

        # First 8 output channels, then 1 input channel.
        for i in range(1, 10):
            try:
                packet = self.socket.recv(length)
            except Exception, e:
                # I have no idea whatsoever what could go wrong =)...
                raise
                msg = 'Error: something went wrong in recv function in {0}!'\
                      .format('receive_names_of_channels')
                self.display.add_tcp_msg(msg)
                exit()

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

        length = self.commands['LEN_CMD_STATUS']

        try:
            packet = self.socket.recv(length)
        except Exception, e:
            # I have no idea whatsoever what could go wrong =)...
            raise
            msg = 'Error: something went wrong in recv function in {0}!'\
                  .format('receive_status_of_channels')
            self.display.add_tcp_msg(msg)
            exit()

        response = self.tcp_handler.decode(self, packet)

        self.channel_string = bin(response[3])
        self.timer_string = bin(response[4])
        self.input_status = response[5]

        # The string is now channel 8...1, but we want 1...8
        channel_string = self.channel_string[::-1]
        timer_string = self.timer_string[::-1]

        for i in range(8):
            self.channels[i+1].status = channel_string[i]
            self.channels[i+1].timer = timer_string[i]

        self.channels[9].status = self.input_status
        self.channels[9].timer = '-'

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
        self.display.update_state(str(self))

    def update_string(self, s, channel_id):
        '''
        NB channel bits 7...0 = channels 8...1
        calculate new channel/input string where only channel_id is flipped!

        @param s: str, either channel or input string
        @param channel_id: int; which channel should be changed?
        @return str; newly generated channel/input string.
        '''

        new_bit = ''
        if s[-channel_id] == '0':
            new_bit = '1'
        elif s[-channel_id] == '1':
            new_bit = '0'

        return s[: -channel_id] + new_bit + s[len(s) - channel_id + 1: len(s)]

    def string_of_change(self, channel_id):
        ''' Return zero for all channels but channel_id '''
        byte_string = '0' * (8 - channel_id) + '1' + '0' * (channel_id - 1)
        return (pack('B', int(byte_string, 2)))

    def on_off_toggle(self, cmd, channel_id):
        '''
        Expected by the server
        <STX><6><CMD_...><channels><CHECKSUM><ETX>
            channel bits 7...0 = channels 8...1 ; bit=0 no change ;
            bit=1 switch channel
        @param cmd: works both with the output status and the timer.
        '''

        change = self.string_of_change(channel_id)
        packet = self.tcp_handler.encode(self, cmd, change, channel_id)
        self.socket.send(packet)

        # If and only if the status has changed, a CMD_STATUS is send by the
        # server. But this we do not know, so we set a timeout and wait...
        self.socket.settimeout(3.0)
        try:
            self.display.add_tcp_msg('Waiting for CMD_STATUS')
            self.receive_status_of_channels()
            # packet = self.socket.recv(8)
        except timeout, e:
            self.display.add_tcp_msg('Timeout -> channel unchanged')
        except Exception, e:
            self.display.add_tcp_msg('Error: unknown')
            raise e
        # else:
        #    self.display.add_tcp_msg(packet.split())

    def pulse(self, channel_id):
        '''
        Expected by the server
        <STX><8><CMD_PULSE><channels><pulsetime><units><CHECKSUM><ETX>
            channel bits 7...0 = channels 8...1 ; bit=0 no change ;
            bit=1 pulse channel
            pulse time: 1...99
            units: 's'= seconds; 'm' = minutes; 'h' = hours
        '''

        return None

    def timer_on_off_toggle(self, cmd, channel_id):
        '''
        Expected by the server
        <STX><6><CMD_TMR_ENA><channels><CHECKSUM><ETX>
            channel bits 7...0 = channels 8...1 ; bit=0 no change ;
            bit=1 switch channel ON
        '''

        return None

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
        self.display.add_tcp_msg('Socket Closed.')

        exit()


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
