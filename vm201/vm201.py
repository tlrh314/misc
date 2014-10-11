#!/usr/bin/env python
# vm201.py
#
# Timo Halbesma
#
# Control VM201 ethernet relay card over TCP.
#
# October 11th, 2014
# Version 2.0: Read TCP responses; send TCP packet to login and request status.

from sys import argv, exit

from VM201RelayCard import VM201RelayCard


def main(host, port=9760, username=None, password=None):
    VM201 = VM201RelayCard(host, port, username, password)

    VM201.connect()
    VM201.status()
    VM201.send_status_request()
    VM201.status()
    VM201.disconnect()


if __name__ == "__main__":
    if len(argv) < 2:
        print 'Usage: python {0} hostname [port] [username password]'\
            .format(__file__)
        exit()
    elif len(argv) == 2:
        # hostname given (required)
        main(argv[1])
    elif len(argv) == 3:
        # hostname and port given.
        main(argv[1], int(argv[2]))
    elif len(argv) == 4:
        # hostname and username+password given, thus, default port used.
        print 'Assmuming default port is used. user={0}, password={1}'\
            .format(argv[2], argv[3])
        main(argv[1], 9760, argv[2], argv[3])
    elif len(argv) == 5:
        # hostname, port and username+password given
        main(argv[1], int(argv[2]), argv[3], argv[4])
