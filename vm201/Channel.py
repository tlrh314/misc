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
