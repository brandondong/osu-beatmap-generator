class BreakEvent:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    @staticmethod
    def from_config_line(line):
        event = line.split(",")
        if event[0] != "2":
            return None
        start = int(event[1])
        end = int(event[2])
        if start > end:
            raise Exception(f"Invalid break event line: {line}.")
        return BreakEvent(start, end)
