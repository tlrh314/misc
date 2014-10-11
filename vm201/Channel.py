'''
Channel class.

The VM201 Ethernet Relay Card has 8 relays (Channels) and 1 input Channel.
Each channel has a name, status (1 on / 0 off) and timer (1 on / 0 off).
Only the input Channel does not have a timer.

Author: Timo Halbesma
Date: October 11th, 2014
Version: 1.0: implemented
'''


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
