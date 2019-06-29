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


def process_section(timing_points, hit_objects):
    validate_timing_point_section(timing_points)
    start = timing_points[0][0]
    millis_per_beat_divisor = timing_points[0][1] / 4
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


def validate_timing_point_section(timing_points):
    if any(
            i > 0 and timing_point[1] >= 0 for i, timing_point in enumerate(timing_points)):
        raise Exception("Must be single bpm.")


def partition_timing_points(timing_points, breaks):
    if len(breaks) == 0:
        return [timing_points]


def partition_hit_objects(hit_objects, breaks):
    if len(breaks) == 0:
        return [hit_objects]


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
        timing_points.append((offset, millis_per_beat))
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
