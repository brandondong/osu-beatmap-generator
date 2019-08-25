class TimingPoint:
    def __init__(self, config_line):
        event = config_line.split(",")
        self.offset = int(event[0])
        self.millis_per_beat = float(event[1])

    def is_inherited(self):
        return self.millis_per_beat < 0

    def get_beat_duration(self, millis_per_beat):
        if self.is_inherited():
            return self.millis_per_beat * millis_per_beat / -100
        return self.millis_per_beat

    def __str__(self):
        return f"[{self.offset}, {self.millis_per_beat}]"

    @staticmethod
    def from_config_line(config_line):
        return TimingPoint(config_line)
