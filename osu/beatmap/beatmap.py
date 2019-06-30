import configparser


class Beatmap:
    @staticmethod
    def from_osu_file(path):
        beatmap = Beatmap()
        with open(path, "r", encoding="utf-8") as f:
            props = parse_section(f, "General")
            validate_mode(props)
            beatmap.audio_path = props["AudioFilename"]

            props = parse_section(f, "Metadata")
            beatmap.id = props["BeatmapID"]

            props = parse_section(f, "Difficulty")
            beatmap.hp = float(props["HPDrainRate"])
            beatmap.cs = float(props["CircleSize"])
            beatmap.od = float(props["OverallDifficulty"])
            beatmap.ar = float(props["ApproachRate"])

            breaks = parse_breaks(f)
            timing_points = parse_timing_points(f)
            hit_objects = parse_hit_objects(f)

            # Split timing points and hit objects into sections separated by the breaks.
            timing_point_sections = partition_timing_points(
                timing_points, breaks)
            hit_objects_sections = partition_hit_objects(hit_objects, breaks)
            for i in range(len(hit_objects_sections)):
                process_section(
                    timing_point_sections[i], hit_objects_sections[i])
        return beatmap


class HitObject:
    def __init__(self, x, y, offset):
        self.x = x
        self.y = y
        self.offset = offset

    def __str__(self):
        return f"Offset: {self.offset}"


class TimingPoint:
    def __init__(self, offset, millis_per_beat):
        self.offset = offset
        self.millis_per_beat = millis_per_beat

    def is_inherited(self):
        return self.millis_per_beat < 0

    def __str__(self):
        return f"Offset: {self.offset}, {self.millis_per_beat}"


def process_section(timing_points, hit_objects):
    start = timing_points[0].offset
    millis_per_beat_divisor = timing_points[0].millis_per_beat / 4
    for hit_object in hit_objects:
        time_since_start = hit_object.offset - start
        num_divisors_from_start = int(
            round(time_since_start / millis_per_beat_divisor))
        predicted_offset = int(
            round(start + num_divisors_from_start * millis_per_beat_divisor))
        # The editor appears to always round down but we can remove that assumption by checking if within one millisecond.
        millis_diff = abs(predicted_offset - hit_object.offset)
        if millis_diff > 1:
            raise Exception("Hit object doesn't fall on a 1/4 beat divisor.")


def partition_timing_points(timing_points, breaks):
    if timing_points[0].is_inherited():
        raise Exception("Invalid starting timing point.")

    timing_point_sections = partition_entries(
        timing_points, breaks, allowed_between_breaks=True)
    for i, section in enumerate(timing_point_sections):
        if len(section) == 0 or section[0].is_inherited():
            # Make sure each section has a non-inherited timing point as the first entry.
            previous_section = timing_point_sections[i - 1]
            section.insert(0, previous_section[0])

    millis_per_beat = timing_points[0].millis_per_beat
    for section in timing_point_sections:
        validate_timing_point_section(section, millis_per_beat)
    return timing_point_sections


def validate_timing_point_section(timing_points, millis_per_beat):
    if timing_points[0].millis_per_beat != millis_per_beat:
        raise Exception("Must be single bpm.")
    if any(
            i > 0 and not timing_point.is_inherited() for i, timing_point in enumerate(timing_points)):
        raise Exception("Must be single bpm.")


def partition_hit_objects(hit_objects, breaks):
    hit_object_sections = partition_entries(
        hit_objects, breaks, allowed_between_breaks=False)
    if any(len(section) == 0 for section in hit_object_sections):
        raise Exception("Empty section between breaks.")
    return hit_object_sections


def partition_entries(entries, breaks, allowed_between_breaks):
    sections = list(map(lambda e: [], range(len(breaks) + 1)))
    for entry in entries:
        offset = entry.offset
        # Find the correct section to place the entry.
        section_index = len(sections) - 1
        for i, b in enumerate(breaks):
            if b[0] <= offset and offset <= b[1]:
                if allowed_between_breaks:
                    section_index = -1
                    break
                raise Exception("Timing entry located during break.")
            elif offset < b[0]:
                section_index = i
                break
        if section_index != -1:
            sections[section_index].append(entry)
    return sections


def validate_mode(general_props):
    if general_props["Mode"] != "0":
        raise Exception("Not an osu standard beatmap.")


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
    return timing_points


def parse_breaks(f):
    breaks = []
    events = read_list_section(f, "Events")
    for event in events:
        if event[0] == "2":
            start = float(event[1])
            end = float(event[2])
            breaks.append((start, end))
    return breaks


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
