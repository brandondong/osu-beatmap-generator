import configparser

from osu.beatmap.hit_object import HitObject

DEFAULT_SLIDER_MULTIPLIER = 1.4
DIVISOR_LEEWAY = 1


class Beatmap:
    def __init__(self):
        self._divisor_sections = []

    @staticmethod
    def from_osu_file(path):
        beatmap = Beatmap()
        with open(path, "r", encoding="utf-8") as f:
            parse_general(f, beatmap)
            parse_metadata(f, beatmap)
            slider_multiplier = parse_difficulty(f, beatmap)

            breaks = parse_breaks(f)
            timing_points = parse_timing_points(f)
            hit_objects = parse_hit_objects(f, slider_multiplier)

            # Split hit objects into sections separated by the breaks.
            hit_objects_sections = partition_hit_objects(hit_objects, breaks)
            for hit_objects_section in hit_objects_sections:
                beatmap._divisor_sections.append(DivisorSection(
                    timing_points, hit_objects_section))
        return beatmap

    def get_timeseries_training_data(self, onsets):
        timeseries_inputs = []
        labels = []
        for divisor_section in self._divisor_sections:
            timeseries, label_vec = divisor_section.get_timeseries_training_data(
                onsets)
            timeseries_inputs.append(timeseries)
            labels.append(label_vec)
        return timeseries_inputs, labels


class DivisorSection:
    def __init__(self, timing_points, hit_objects):
        starting_point = starting_timing_point(timing_points, hit_objects)
        start = starting_point.offset
        millis_per_beat_divisor = starting_point.millis_per_beat / 4

        first_hit_object = hit_objects[0]
        time_since_start = first_hit_object.offset - start
        num_divisors_from_start = int(
            round(time_since_start / millis_per_beat_divisor))

        # Fill a list with what is happening on each beat divisor
        divisors = []
        current_hit_object_index = 0
        while current_hit_object_index < len(hit_objects):
            hit_object = hit_objects[current_hit_object_index]
            predicted_offset = int(
                round(start + num_divisors_from_start * millis_per_beat_divisor))
            millis_diff = abs(predicted_offset - hit_object.offset)
            # The editor appears to always round down but we can remove that assumption by checking if within one millisecond.
            # There have also been unexplainable observed rounding errors. Add a leeway to compensate.
            if millis_diff <= 1 + DIVISOR_LEEWAY:
                divisors.append(hit_object)
                current_hit_object_index += 1
            elif hit_object.offset < predicted_offset:
                raise Exception(
                    f"Hit object {hit_object} doesn't fall on a 1/4 beat divisor, expected ~{predicted_offset}.")
            else:
                divisors.append(None)
            num_divisors_from_start += 1

    def get_timeseries_training_data(self, onsets):
        return None, None


class TimingPoint:
    def __init__(self, config_line):
        event = config_line.split(",")
        self.offset = int(event[0])
        self.millis_per_beat = float(event[1])

    def is_inherited(self):
        return self.millis_per_beat < 0

    def __str__(self):
        return f"[{self.offset}, {self.millis_per_beat}]"


def starting_timing_point(timing_points, hit_objects):
    start = hit_objects[0].offset
    for timing_point in reversed(timing_points):
        if not timing_point.is_inherited() and timing_point.offset <= start:
            return timing_point
    return timing_points[0]


def partition_hit_objects(hit_objects, breaks):
    sections = list(map(lambda e: [], range(len(breaks) + 1)))
    for entry in hit_objects:
        offset = entry.offset
        # Find the correct section to place the object.
        section_index = len(sections) - 1
        for i, b in enumerate(breaks):
            if b[0] <= offset and offset <= b[1]:
                raise Exception(f"Hit object {entry} located during break.")
            elif offset < b[0]:
                section_index = i
                break
        sections[section_index].append(entry)
    if any(len(section) == 0 for section in sections):
        raise Exception("Empty section between breaks.")
    return sections


def parse_hit_objects(f, slider_multiplier):
    entries = read_list_section(f, "HitObjects", last_section=True)
    return list(map(lambda e: HitObject.from_config_line(e, slider_multiplier), entries))


def parse_timing_points(f):
    timing_points = []
    event_lines = read_list_section(f, "TimingPoints")
    for event_line in event_lines:
        timing_points.append(TimingPoint(event_line))
    validate_timing_points(timing_points)
    return timing_points


def validate_timing_points(timing_points):
    if timing_points[0].is_inherited():
        raise Exception("Invalid starting timing point.")
    millis_per_beat = timing_points[0].millis_per_beat
    if any(
            tp.millis_per_beat != millis_per_beat and not tp.is_inherited() for tp in timing_points):
        raise Exception("Must be single bpm.")


def parse_breaks(f):
    breaks = []
    event_lines = read_list_section(f, "Events")
    for event_line in event_lines:
        event = event_line.split(",")
        if event[0] == "2":
            start = float(event[1])
            end = float(event[2])
            breaks.append((start, end))
    return breaks


def parse_general(f, beatmap):
    props = parse_section(f, "General")
    if props["Mode"] != "0":
        raise Exception("Not an osu standard beatmap.")
    beatmap.audio_path = props["AudioFilename"]


def parse_metadata(f, beatmap):
    props = parse_section(f, "Metadata")
    beatmap.id = int(props["BeatmapID"])


def parse_difficulty(f, beatmap):
    props = parse_section(f, "Difficulty")
    beatmap.hp = float(props["HPDrainRate"])
    beatmap.cs = float(props["CircleSize"])
    beatmap.od = float(props["OverallDifficulty"])
    beatmap.ar = float(props["ApproachRate"])
    slider_multiplier = props.get("SliderMultiplier")
    return DEFAULT_SLIDER_MULTIPLIER if slider_multiplier is None else float(slider_multiplier)


def parse_section(f, target):
    seek_until_target_section_passed(f, target)
    dummy_key = "a"
    config_string = f"[{dummy_key}]\n"
    while True:
        line = f.readline()
        if not line:
            raise Exception(
                "Unexpected end of file while searching for the end of the section.")
        if line == "\n":
            break
        config_string += line
    config = configparser.ConfigParser()
    config.read_string(config_string)
    return config[dummy_key]


def read_list_section(f, target, last_section=False):
    seek_until_target_section_passed(f, target)
    entries = []
    while True:
        line = f.readline()
        if not line:
            if last_section:
                return entries
            raise Exception(
                "Unexpected end of file while searching for the end of the section.")
        if line == "\n":
            return entries
        elif not line.startswith("//"):
            entries.append(line[:-1])


def seek_until_target_section_passed(f, target):
    target = f"[{target}]"
    while True:
        line = f.readline()
        if not line:
            raise Exception(
                f"Unexpected end of file while searching for {target}.")
        if line == f"{target}\n":
            return
