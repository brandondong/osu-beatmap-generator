import configparser

from osu.beatmap.break_event import BreakEvent
from osu.beatmap.divisor_section import DivisorSection
from osu.beatmap.hit_object import HitObject
from osu.beatmap.timing_point import TimingPoint

DEFAULT_SLIDER_MULTIPLIER = 1.4


class Beatmap:
    @staticmethod
    def from_osu_file(path):
        beatmap = Beatmap()
        with open(path, "r", encoding="utf-8") as f:
            parse_general(f, beatmap)
            parse_metadata(f, beatmap)
            slider_multiplier = parse_difficulty(f, beatmap)

            breaks = parse_breaks(f)
            timing_points = parse_timing_points(f)
            hit_objects = parse_hit_objects(f)

            # Split hit objects into sections separated by the breaks.
            hit_objects_sections = partition_hit_objects(hit_objects, breaks)
            beatmap.divisor_sections = [DivisorSection(
                timing_points, hit_objects, slider_multiplier) for hit_objects in hit_objects_sections]
        return beatmap

    def get_training_labels(self):
        return [ds.get_training_labels() for ds in self.divisor_sections]


def partition_hit_objects(hit_objects, breaks):
    sections = [[] for i in range(len(breaks) + 1)]
    section_index = 0
    for hit_object in hit_objects:
        # Update the index to search from for the next iteration.
        section_index = find_break_section(hit_object, breaks, section_index)
        sections[section_index].append(hit_object)
    if any(len(section) == 0 for section in sections):
        raise Exception("Empty section between breaks.")
    return sections


def find_break_section(hit_object, breaks, start_index):
    offset = hit_object.offset
    while True:
        if start_index > len(breaks) - 1:
            return start_index
        b = breaks[start_index]
        if b.start <= offset and offset <= b.end:
            raise Exception(f"Hit object {hit_object} located during break.")
        elif offset < b.start:
            return start_index
        start_index += 1


def parse_hit_objects(f):
    entries = read_list_section(f, "HitObjects", last_section=True)
    return [HitObject.from_config_line(entry) for entry in entries]


def parse_timing_points(f):
    event_lines = read_list_section(f, "TimingPoints")
    timing_points = [TimingPoint.from_config_line(
        line) for line in event_lines]
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
        break_event = BreakEvent.from_config_line(event_line)
        if break_event:
            breaks.append(break_event)
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
