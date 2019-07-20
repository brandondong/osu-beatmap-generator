import argparse
from html.parser import HTMLParser
import os
import shutil
import zipfile

import requests

from audio.audio_preprocessor import AudioPreprocessor
from difficulty.difficulty_properties import DifficultyProperties
from beatmap.beatmap import Beatmap

OSU_SIGNIN_PAGE = "https://osu.ppy.sh/home"
# Recently ranked beatmapsets with osu standard filter.
BASE_SEARCH_URL = "https://osu.ppy.sh/beatmapsets/search?m=0&s=ranked"
OSU_STANDARD_MODE = 0
LOGIN_FORM_TOKEN_PARAM = "_token"

TRAINING_PATH = "training_data"


def retrieve_beatmap_data(session, beatmapset_limit, is_debug):
    if beatmapset_limit <= 0:
        return
    count_beatmapsets_retrieved = 0
    # Track pagination.
    cursor_approved_date = None
    cursor_id = None

    while True:
        # Match scrolling behavior of https://osu.ppy.sh/beatmapsets.
        if cursor_approved_date and cursor_id:
            request_url = f"{BASE_SEARCH_URL}&cursor%5Bapproved_date%5D={cursor_approved_date}&cursor%5B_id%5D={cursor_id}"
        else:
            request_url = BASE_SEARCH_URL

        debug_print(f"Retrieving listing: {request_url}.", is_debug)
        data = session.get(request_url).json()

        # Extract cursor data for the next request.
        cursor_data = data["cursor"]
        cursor_approved_date = cursor_data["approved_date"]
        cursor_id = cursor_data["_id"]

        for beatmapset in data["beatmapsets"]:
            saved_new = process_beatmapset(session, beatmapset, is_debug)
            if saved_new:
                count_beatmapsets_retrieved += 1
                if count_beatmapsets_retrieved >= beatmapset_limit:
                    return


def process_beatmapset(session, beatmapset, is_debug):
    debug_print("======================================", is_debug)
    validate_beatmapset(beatmapset)
    # Check if we already have this beatmapset.
    beatmapset_dir = training_folder(beatmapset)
    if os.path.exists(beatmapset_dir):
        beatmapset_id = beatmapset["id"]
        debug_print(
            f"Beatmapset {beatmapset_id} is already part of the training data.", is_debug)
        return False
    # Create the beatmapset training folder. Even if processing fails, we can use this as a marker to skip next time.
    os.makedirs(beatmapset_dir)

    # Download the beatmap and extract it to a temporary directory.
    temp_dir = "temp"
    retrieve_beatmapset(session, beatmapset, temp_dir, is_debug)

    successful = process_osu_folder(
        beatmapset, temp_dir, beatmapset_dir, is_debug)

    # Finished. Remove the temporary directory.
    shutil.rmtree(temp_dir)
    return successful


def process_osu_folder(beatmapset, osu_dir, training_dir, is_debug):
    beatmap_infos = process_osu_files(osu_dir, is_debug)
    if len(beatmap_infos) == 0:
        debug_print("No valid beatmaps found, skipping beatmapset.", is_debug)
        return False

    audio_path = get_audio_path(beatmap_infos, osu_dir, is_debug)
    if not audio_path:
        return False
    debug_print("Processing audio.", is_debug)
    try:
        AudioPreprocessor.save_training_audio(audio_path, training_dir)
    except Exception as e:
        debug_print(f"Audio processing failed: {e}", is_debug)
        return False

    copy_osu_files(beatmap_infos, training_dir)
    save_difficulty_info(beatmapset, beatmap_infos, training_dir)
    return True


def process_osu_files(osu_dir, is_debug):
    beatmap_infos = []
    for file in os.listdir(osu_dir):
        if is_osu_file(file):
            full_path = os.path.join(osu_dir, file)
            try:
                beatmap = Beatmap.from_osu_file(full_path)
                beatmap_infos.append((beatmap, full_path))
                debug_print(
                    f"Processed beatmap [{file}] successfully.", is_debug)
            except Exception as e:
                # Beatmap doesn't meet training data criteria.
                debug_print(f"Skipping beatmap [{file}]: {e}", is_debug)
    return beatmap_infos


def save_difficulty_info(beatmapset, beatmap_infos, training_dir):
    valid_beatmap_ids = set(map(lambda b: b[0].id, beatmap_infos))
    diff_map = {}
    for beatmap in beatmapset["beatmaps"]:
        beatmap_id = beatmap["id"]
        if beatmap_id in valid_beatmap_ids:
            diff_map[beatmap_id] = beatmap["difficulty_rating"]
    DifficultyProperties.save_training_star_difficulties(
        diff_map, training_dir)


def copy_osu_files(beatmap_infos, training_dir):
    for beatmap_info in beatmap_infos:
        beatmap = beatmap_info[0]
        full_path = beatmap_info[1]
        dest = os.path.join(training_dir, f"{beatmap.id}.osu")
        os.rename(full_path, dest)


def training_folder(beatmapset):
    return os.path.join(TRAINING_PATH, str(beatmapset["id"]))


def is_osu_file(file):
    _, ext = os.path.splitext(file)
    return ext.lower() == ".osu"


def get_audio_path(beatmap_infos, osu_dir, is_debug):
    audio_paths = set(map(lambda b: b[0].audio_path, beatmap_infos))
    if len(audio_paths) != 1:
        debug_print("Multiple audio paths found.", is_debug)
        return None
    return os.path.join(osu_dir, audio_paths.pop())


def retrieve_beatmapset(session, beatmapset, out_dir, is_debug):
    beatmapset_id = beatmapset["id"]
    beatmapset_download_link = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}/download?noVideo=1"
    debug_print(
        f"Retrieving beatmapset: {beatmapset_download_link}.", is_debug)
    response = session.get(beatmapset_download_link)
    temp_file = "temp.zip"
    with open(temp_file, "wb") as f:
        f.write(response.content)
    with zipfile.ZipFile(temp_file, "r") as zip_ref:
        zip_ref.extractall(out_dir)
    debug_print(
        "Download finished.", is_debug)
    os.remove(temp_file)


def validate_beatmapset(beatmapset):
    # Sanity check that there are osu standard beatmaps in the beatmapset.
    contains_standard = any(
        beatmap["mode_int"] == OSU_STANDARD_MODE for beatmap in beatmapset["beatmaps"])
    if not contains_standard:
        raise Exception("osu standard filter failed.")
    if beatmapset["ranked"] != 1:
        raise Exception("Ranked search filter failed.")


def set_and_parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="osu username")
    parser.add_argument("password", help="osu password")
    parser.add_argument("--limit", help="maximum number of beatmapsets to retrieve (default 1000)",
                        type=int, default=1000)
    parser.add_argument(
        "-d", "--debug", help="output debug information", action="store_true")
    return parser.parse_args()


def login_to_osu(username, password, is_debug):
    session = requests.session()
    html = session.get(OSU_SIGNIN_PAGE).text
    parser = OsuHomeParser()
    parser.feed(html)
    params = {"username": username, "password": password,
              LOGIN_FORM_TOKEN_PARAM: parser.token}
    response = session.request(parser.method, parser.url, params)
    if response.status_code >= 400:
        raise Exception(f"Failed to login for user={username}.")
    debug_print(f"Successfully logged in for user={username}.", is_debug)
    return session


class OsuHomeParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.found_token = False

    def handle_starttag(self, tag, attrs):
        if self.found_token:
            return
        if tag == "form":
            # Remember the attributes of the form that contains the CSRF input.
            for key_value in attrs:
                key = key_value[0]
                value = key_value[1]
                if key == "method":
                    self.method = value
                elif key == "action":
                    self.url = value
        elif tag == "input":
            # Look for the CSRF token to be submitted during login.
            if ("name", LOGIN_FORM_TOKEN_PARAM) in attrs:
                self.token = next(
                    key_value[1] for key_value in attrs if key_value[0] == "value")
                self.found_token = True


def debug_print(msg, is_debug):
    if is_debug:
        print(msg)


args = set_and_parse_args()
# Login to osu in order to be able to download beatmapsets.
session = login_to_osu(args.username, args.password, args.debug)
retrieve_beatmap_data(session, args.limit, args.debug)
