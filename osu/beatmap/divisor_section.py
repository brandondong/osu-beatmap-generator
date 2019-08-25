from osu.beatmap.hit_object import HitObjectType

DIVISOR_LEEWAY_MS = 1


class DivisorSection:
    def __init__(self, timing_points, hit_objects, slider_multiplier):
        self.divisors = []
        self.offset = hit_objects[0].offset

        starting_point = reference_timing_point(timing_points, hit_objects)
        start = starting_point.offset
        millis_per_beat_divisor = starting_point.millis_per_beat / 4

        # Process the events of each beat divisor from the first hit object to the last.
        divisor_start_offset = int(
            round((self.offset - start) / millis_per_beat_divisor))
        hit_object_index = 0
        timing_point_index = find_associated_timing_point(
            hit_objects[hit_object_index], timing_points, 0)
        while True:
            predicted_offset = int(
                round(start + (divisor_start_offset + len(self.divisors)) * millis_per_beat_divisor))
            hit_object = hit_objects[hit_object_index]
            if falls_on_divisor(predicted_offset, hit_object):
                add_hit_object_to_divisors(
                    self.divisors, hit_object, timing_points[timing_point_index], starting_point.millis_per_beat, slider_multiplier)
                hit_object_index += 1
                if hit_object_index > len(hit_objects) - 1:
                    return
                timing_point_index = find_associated_timing_point(
                    hit_objects[hit_object_index], timing_points, timing_point_index)
            elif hit_object.offset < predicted_offset:
                raise create_offset_error(
                    self.divisors, hit_object, predicted_offset)
            else:
                self.divisors.append(HitObjectType.SILENCE.value)

    def get_training_labels(self):
        return self.divisors


def falls_on_divisor(predicted_offset, hit_object):
    millis_diff = abs(predicted_offset - hit_object.offset)
    # The editor appears to always round down but we can remove that assumption by checking if within one millisecond.
    # There have also been unexplainable observed rounding errors. Add a leeway to compensate.
    return millis_diff <= 1 + DIVISOR_LEEWAY_MS


def add_hit_object_to_divisors(divisors, hit_object, timing_point, millis_per_beat, slider_multiplier):
    duration = hit_object.get_duration(
        timing_point.get_beat_duration(millis_per_beat), slider_multiplier)
    num_divisors = max(1, int(round(duration / (millis_per_beat / 4))))
    for i in range(num_divisors):
        divisors.append(hit_object.get_type_enum().value)


def create_offset_error(divisors, hit_object, predicted_offset):
    if len(divisors) > 0 and divisors[-1] != HitObjectType.SILENCE.value and divisors[-1] != HitObjectType.HIT_CIRCLE.value:
        return Exception(
            f"Hit object {hit_object} intersects with previous hit object.")
    return Exception(
        f"Hit object {hit_object} doesn't fall on a 1/4 beat divisor, expected ~{predicted_offset}.")


def reference_timing_point(timing_points, hit_objects):
    start = hit_objects[0].offset
    for timing_point in reversed(timing_points):
        if not timing_point.is_inherited() and timing_point.offset <= start:
            return timing_point
    return timing_points[0]


def find_associated_timing_point(hit_object, timing_points, start_index):
    index = start_index + 1
    while True:
        if index > len(timing_points) - 1:
            return index - 1
        timing_point = timing_points[index]
        if timing_point.offset > hit_object.offset:
            return index - 1
        index += 1
