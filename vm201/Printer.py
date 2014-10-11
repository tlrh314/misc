from sys import stdout


# issues: explicit locations. Should add parameters.
class Printer(object):
    def __init__(self):
        # self.row, self.col = 2, 1
        self.state_row, self.state_col = 2, 1
        self.log_row, self.log_col = 2, 42
        self.help_row, self.help_col = 45, 1

        self.table_len = 15

        self.msg_counter = 0

        stdout.write('\033[2J')  # Clear entire screen.
        stdout.write('\033[{0};{1}H'.format(self.state_row, self.state_col))
        stdout.write('System State\n')

        stdout.write('\033[{0};{1}H'.format(self.log_row, self.log_col))
        stdout.write('TCP Packet Log\n')

        stdout.write('\033[{0};{1}H'.format(self.state_row+1, self.state_col))
        stdout.write('-'*31)
        stdout.write('\033[{0};{1}H'.format(self.log_row+1, self.log_col))
        stdout.write('-'*14 + '\n')

        stdout.write('\033[{0};{1}H'.format(self.help_row, self.help_col))
        stdout.write('The following commands may be issued:\n')
        # stdout.write('\tHELP\n')
        stdout.write('\tCMD_STATUS\n')
        stdout.write('\tCMD_ON channel_number (1-8)\n')
        stdout.write('\tCMD_OFF channel_number (1-8)\n')
        stdout.write('\tCMD_TOGGLE channel_numer (1-8)\n')
        stdout.write('\tCMD_TMR_ENA channel_number (1-8)\n')
        stdout.write('\tCMD_TMR_DIS channel_number (1-8)\n')
        stdout.write('\tCMD_TMR_TOGGLE channel_numer (1-8)\n')
        stdout.write('\tQUIT\n')

    # http://www.darkcoding.net/software/pretty-command-line-console-output-on
    # -unix-in-python-and-go-lang/
    def clear(self):
        ''' Clear screen, return cursor to top left '''

        stdout.write('\033[{0}A'.format(self.table_len))
        stdout.write('\033[0J')
        stdout.flush()

    def add_tcp_msg(self, msg):
        # There is an off by one in the log when it renews after %
        msg_position = 5 + self.msg_counter % int(self.help_row - 5)
        stdout.write('\033[{0};{1}H'.format(msg_position, self.log_col))
        stdout.write('\033[K')
        if self.msg_counter >= int(self.help_row - 5):
            stdout.write('\033[{0};{1}H'.format(msg_position-1, self.log_col))
            stdout.write('\033[K')
        stdout.write('Msg {0}: {1}\n'.format(self.msg_counter, msg))
        stdout.write('\033[54;1H')
        stdout.write('\033[K')
        self.msg_counter += 1

    def update_state(self, table):
        stdout.write('\033[4;1H')
        stdout.write(table)
        stdout.write('\033[54;1H')
        stdout.write('\033[K')
