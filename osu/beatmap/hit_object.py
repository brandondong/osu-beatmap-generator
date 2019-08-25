from enum import Enum


class HitObjectType(Enum):
    SILENCE = 0
    HIT_CIRCLE = 1
    SLIDER = 2
    SPINNER = 3


class HitObject:
    def __init__(self, offset):
        self.offset = offset

    def __str__(self):
        minutes = int(self.offset / (1000 * 60))
        millis = self.offset % (1000 * 60)
        return f"[offset={self.offset} ({minutes}:{millis/1000:.3f})]"

    @staticmethod
    def from_config_line(line):
        s = line.split(",")
        x = int(s[0])
        y = int(s[1])
        offset = int(s[2])
        object_type = int(s[3])
        if is_bit_set(object_type, 0):
            return HitCircle(x, y, offset)
        elif is_bit_set(object_type, 1):
            pixel_length = float(s[7])
            return Slider(x, y, offset, pixel_length)
        elif is_bit_set(object_type, 3):
            return Spinner(offset, int(s[5]))
        raise Exception(f"Unrecognized hit object type: {object_type}.")


class HitCircle(HitObject):
    def __init__(self, x, y, offset):
        super().__init__(offset)
        self.x = x
        self.y = y

    def get_duration(self, beat_duration, slider_multiplier):
        return 0

    def get_type_enum(self):
        return HitObjectType.HIT_CIRCLE


class Slider(HitObject):
    def __init__(self, x, y, offset, pixel_length):
        super().__init__(offset)
        self.x = x
        self.y = y
        self.pixel_length = pixel_length

    def get_duration(self, beat_duration, slider_multiplier):
        return self.pixel_length / (100.0 * slider_multiplier) * beat_duration

    def get_type_enum(self):
        return HitObjectType.SLIDER


class Spinner(HitObject):
    def __init__(self, offset, end_time):
        super().__init__(offset)
        self.end_time = end_time

    def get_duration(self, beat_duration, slider_multiplier):
        return self.end_time - self.offset

    def get_type_enum(self):
        return HitObjectType.SPINNER


def is_bit_set(n, bit):
    return n & 1 << bit != 0
