import configparser


class Beatmap:
    @staticmethod
    def from_osu_file(path):
        beatmap = Beatmap()
        with open(path, "r", encoding="utf-8") as f:
            parse_general(f, beatmap)
            parse_metadata(f, beatmap)
            parse_difficulty(f, beatmap)

            breaks = parse_breaks(f)
            timing_points = parse_timing_points(f)
            hit_objects = parse_hit_objects(f)

            # Split hit objects into sections separated by the breaks.
            hit_objects_sections = partition_hit_objects(hit_objects, breaks)
            for i in range(len(hit_objects_sections)):
                process_section(
                    timing_points, hit_objects_sections[i])
        return beatmap


class HitObject:
    def __init__(self, x, y, offset):
        self.x = x
        self.y = y
        self.offset = offset

    def __str__(self):
        minutes_decimal = self.offset / 1000 / 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        return f"[offset={self.offset} ({minutes}:{seconds:.3f})]"


class TimingPoint:
    def __init__(self, offset, millis_per_beat):
        self.offset = offset
        self.millis_per_beat = millis_per_beat

    def is_inherited(self):
        return self.millis_per_beat < 0

    def __str__(self):
        return f"[{self.offset}, {self.millis_per_beat}]"


def process_section(timing_points, hit_objects):
    starting_point = starting_timing_point(timing_points, hit_objects)
    start = starting_point.offset
    millis_per_beat_divisor = starting_point.millis_per_beat / 4
    for hit_object in hit_objects:
        time_since_start = hit_object.offset - start
        num_divisors_from_start = int(
            round(time_since_start / millis_per_beat_divisor))
        predicted_offset = int(
            round(start + num_divisors_from_start * millis_per_beat_divisor))
        # The editor appears to always round down but we can remove that assumption by checking if within one millisecond.
        millis_diff = abs(predicted_offset - hit_object.offset)
        if millis_diff > 1:
            raise Exception(
                f"Hit object {hit_object} doesn't fall on a 1/4 beat divisor.")


def starting_timing_point(timing_points, hit_objects):
    # TODO.
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


def parse_hit_objects(f):
    entries = read_list_section(
        f, "HitObjects", max_split=5, last_section=True)
    return list(map(lambda e: HitObject(int(e[0]), int(e[1]), int(e[2])), entries))


def parse_timing_points(f):
    timing_points = []
    events = read_list_section(f, "TimingPoints")
    for event in events:
        offset = int(event[0])
        millis_per_beat = float(event[1])
        timing_points.append(TimingPoint(offset, millis_per_beat))
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
    events = read_list_section(f, "Events")
    for event in events:
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
    beatmap.id = props["BeatmapID"]


def parse_difficulty(f, beatmap):
    props = parse_section(f, "Difficulty")
    beatmap.hp = float(props["HPDrainRate"])
    beatmap.cs = float(props["CircleSize"])
    beatmap.od = float(props["OverallDifficulty"])
    beatmap.ar = float(props["ApproachRate"])


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


def read_list_section(f, target, max_split=-1, last_section=False):
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
            entries.append(line[:-1].split(",", max_split))


def seek_until_target_section_passed(f, target):
    target = f"[{target}]"
    while True:
        line = f.readline()
        if not line:
            raise Exception(
                f"Unexpected end of file while searching for {target}.")
        if line == f"{target}\n":
            return
