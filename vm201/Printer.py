from sys import stdout


class Printer(object):
    def __init__(self):
        self.msg_counter = 0

        stdout.write('\033[2J')  # clear entire screen
        stdout.write('\033[2;1H')  # move cursus to 1,1 (top left)
        stdout.write('System State\n')

        stdout.write('\033[2;42H')
        stdout.write('TCP Packet Log\n')

        stdout.write('\033[3;1H')
        stdout.write('-'*31)
        stdout.write('\033[3;42H')
        stdout.write('-'*14 + '\n')

        stdout.write('\n'*20)

        stdout.write('\033[45;1H')
        stdout.write('The following commands may be issued:\n')
        stdout.write('\tHELP\n')
        stdout.write('\tCMD_STATUS\n')
        stdout.write('\tQUIT\n')

    # http://www.darkcoding.net/software/pretty-command-line-console-output-on
    # -unix-in-python-and-go-lang/
    def clear(self):
        ''' Clear screen, return cursor to top left '''

        stdout.write('\033[15A')
        stdout.write('\033[0J')
        stdout.flush()

    def add_tcp_msg(self, msg):
        stdout.write('\033[{0};42H'.format(5 + self.msg_counter % 39))
        stdout.write('\033[K')
        stdout.write('Msg {0}: {1}\n'.format(self.msg_counter, msg))
        stdout.write('\033[50;1H')
        self.msg_counter += 1

    def update_state(self, table):
        stdout.write('\033[4;1H')
        stdout.write(table)
        stdout.write('\033[50;1H')
