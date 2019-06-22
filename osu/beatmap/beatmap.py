import configparser


class Beatmap:
    @staticmethod
    def from_osu_file(path):
        beatmap = Beatmap()
        with open(path, "r", encoding="utf-8") as f:
            props = parse_section(f, "General")
            if props["Mode"] != "0":
                raise Exception("Not an osu standard beatmap.")
            beatmap.audio_path = props["AudioFilename"]

            props = parse_section(f, "Metadata")
            beatmap.id = props["BeatmapID"]
        return beatmap


def parse_section(f, target):
    seek_until_target_passed(f, f"[{target}]")
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


def seek_until_target_passed(f, target):
    while True:
        line = f.readline()
        if not line:
            raise Exception(
                f"Unexpected end of file while searching for {target}.")
        if line == f"{target}\n":
            return
