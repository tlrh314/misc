import sys
import struct

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
