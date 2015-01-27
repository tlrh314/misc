#!/usr/bin/env python
# communicate_with_vm201.py
#
# Timo Halbesma
#
# Control VM201 ethernet relay card over TCP.
#
# October 11th, 2014
# Version 2.0: Read TCP responses; send TCP packet to login and request status.

from sys import argv, exit
from time import sleep

from VM201RelayCard import VM201RelayCard


def on_off(host, port=9760, username=None, password=None, cmd=''):
    # Set verbose to False so no output is written to stdout.
    VM201 = VM201RelayCard(host, port, username, password, False)
    VM201.connect()
    VM201.status()

    if cmd.lower() == 'on':
        VM201.on_off_toggle('CMD_ON', 1)
        VM201.on_off_toggle('CMD_ON', 2)
        VM201.on_off_toggle('CMD_ON', 3)
    elif cmd.lower() == 'off':
        VM201.on_off_toggle('CMD_OFF', 1)
        VM201.on_off_toggle('CMD_OFF', 2)
        VM201.on_off_toggle('CMD_OFF', 3)
    else:
        print "'{0}' is not a valid option".format(cmd)

    VM201.send_status_request()
    VM201.status()
    VM201.disconnect()


def main(host, port=9760, username=None, password=None):
    # Explicitly set verbose to True [this is the default value though]
    VM201 = VM201RelayCard(host, port, username, password, True)

    VM201.connect()
    VM201.status()

    user_command = ''
    while user_command != 'QUIT':
        user_command = raw_input('> ')
        if user_command == 'HELP':
            VM201.display.add_tcp_msg('HELP: not available yet')
        elif user_command == 'CMD_STATUS':
            VM201.send_status_request()
            VM201.status()
        elif user_command == 'QUIT':
            VM201.disconnect()
        else:

            try:
                choice, argument = user_command.split()
            except ValueError, e:
                VM201.display.add_tcp_msg('Error: incorrect command or usage')
            else:
                try:
                    argument = int(argument)
                    if argument < 1 or argument > 8:
                        raise ValueError
                except ValueError, e:
                    VM201.display.add_tcp_msg('Error: incorrect usage')

                else:
                    if choice in ['CMD_ON', 'CMD_OFF', 'CMD_TOGGLE',
                                  'CMD_TMR_ENA', 'CMD_TMR_DIS',
                                  'CMD_TMR_TOGGLE']:
                        VM201.on_off_toggle(choice, argument)
                        VM201.send_status_request()
                        VM201.status()
                    else:
                        VM201.display.add_tcp_msg('Error: incorrect usage')


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
    elif len(argv) == 6:
        # hostname, port and username+password given and additional command
        on_off(argv[1], int(argv[2]), argv[3], argv[4], argv[5])
