import argparse
from html.parser import HTMLParser
import logging
import os
import shutil
import signal
import zipfile

import requests

from osu.audio.audio_preprocessor import AudioPreprocessor
from osu.beatmap.beatmap import Beatmap
from osu.difficulty.difficulty_properties import DifficultyProperties

OSU_SIGNIN_PAGE = "https://osu.ppy.sh/home"
# Recently ranked beatmapsets with osu standard filter.
BASE_SEARCH_URL = "https://osu.ppy.sh/beatmapsets/search?m=0&s=ranked"
OSU_STANDARD_MODE = 0
LOGIN_FORM_TOKEN_PARAM = "_token"

TRAINING_PATH = "osu/training_data"


def retrieve_beatmap_data(session, beatmapset_limit, logger, sigint_catcher):
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

        logger.debug(f"Retrieving listing: {request_url}.")
        data = session.get(request_url).json()

        # Extract cursor data for the next request.
        cursor_data = data["cursor"]
        cursor_approved_date = cursor_data["approved_date"]
        cursor_id = cursor_data["_id"]

        for beatmapset in data["beatmapsets"]:
            if sigint_catcher.caught_sigint:
                logger.debug("Caught SIGINT. Terminating gracefully.")
                return

            saved_new = process_beatmapset(session, beatmapset, logger)
            if saved_new:
                count_beatmapsets_retrieved += 1
                if count_beatmapsets_retrieved >= beatmapset_limit:
                    return


def process_beatmapset(session, beatmapset, logger):
    logger.debug("======================================")
    validate_beatmapset(beatmapset)
    # Check if we already have this beatmapset.
    beatmapset_dir = training_folder(beatmapset)
    if os.path.exists(beatmapset_dir):
        beatmapset_id = beatmapset["id"]
        logger.debug(
            f"Beatmapset {beatmapset_id} is already part of the training data.")
        return False
    # Create the beatmapset training folder. Even if processing fails, we can use this as a marker to skip next time.
    os.makedirs(beatmapset_dir)

    # Download the beatmap and extract it to a temporary directory.
    temp_dir = "temp"
    retrieve_beatmapset(session, beatmapset, temp_dir, logger)

    successful = process_osu_folder(
        beatmapset, temp_dir, beatmapset_dir, logger)

    # Finished. Remove the temporary directory.
    shutil.rmtree(temp_dir)
    return successful


def process_osu_folder(beatmapset, osu_dir, training_dir, logger):
    beatmap_infos = process_osu_files(osu_dir, logger)
    if len(beatmap_infos) == 0:
        logger.debug("No valid beatmaps found, skipping beatmapset.")
        return False

    audio_path = get_audio_path(beatmap_infos, osu_dir, logger)
    if not audio_path:
        return False
    logger.debug("Processing audio.")
    try:
        AudioPreprocessor.save_training_audio(audio_path, training_dir)
    except Exception as e:
        logger.debug(f"Audio processing failed: {e}")
        return False

    copy_osu_files(beatmap_infos, training_dir)
    save_difficulty_info(beatmapset, beatmap_infos, training_dir)
    logger.debug("New beatmapset saved successfully.")
    return True


def process_osu_files(osu_dir, logger):
    beatmap_infos = []
    for file in os.listdir(osu_dir):
        if is_osu_file(file):
            full_path = os.path.join(osu_dir, file)
            try:
                beatmap = Beatmap.from_osu_file(full_path)
                beatmap_infos.append((beatmap, full_path))
                logger.debug(
                    f"Processed beatmap [{file}] successfully.")
            except Exception as e:
                # Beatmap doesn't meet training data criteria.
                logger.debug(f"Skipping beatmap [{file}]: {e}")
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


def get_audio_path(beatmap_infos, osu_dir, logger):
    audio_paths = set(map(lambda b: b[0].audio_path, beatmap_infos))
    if len(audio_paths) != 1:
        logger.debug("Multiple audio paths found.")
        return None
    return os.path.join(osu_dir, audio_paths.pop())


def retrieve_beatmapset(session, beatmapset, out_dir, logger):
    beatmapset_id = beatmapset["id"]
    beatmapset_download_link = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}/download?noVideo=1"
    logger.debug(
        f"Retrieving beatmapset: {beatmapset_download_link}.")
    response = session.get(beatmapset_download_link)
    temp_file = "temp.zip"
    with open(temp_file, "wb") as f:
        f.write(response.content)
    with zipfile.ZipFile(temp_file, "r") as zip_ref:
        zip_ref.extractall(out_dir)
    logger.debug(
        "Download finished.")
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
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("username", help="osu username")
    parser.add_argument("password", help="osu password")
    parser.add_argument("--limit", help="maximum number of beatmapsets to retrieve",
                        type=int, default=1000)
    parser.add_argument(
        "-d", "--debug", help="output debug information", action="store_true")
    return parser.parse_args()


def login_to_osu(username, password, logger):
    session = requests.session()
    html = session.get(OSU_SIGNIN_PAGE).text
    parser = OsuHomeParser()
    parser.feed(html)
    params = {"username": username, "password": password,
              LOGIN_FORM_TOKEN_PARAM: parser.token}
    response = session.request(parser.method, parser.url, params)
    if response.status_code >= 400:
        raise Exception(f"Failed to login for user={username}.")
    logger.debug(f"Successfully logged in for user={username}.")
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


def create_logger(debug):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG if debug else logging.WARNING)
    # Output to console.
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    return logger


class SigintCatcher():
    def __init__(self):
        self.caught_sigint = False

    def handle_sigint(self, *args):
        self.caught_sigint = True


args = set_and_parse_args()
logger = create_logger(args.debug)
# Login to osu in order to be able to download beatmapsets.
session = login_to_osu(args.username, args.password, logger)

# Set up a handler for SIGINT so the process can terminate gracefully.
sigint_catcher = SigintCatcher()
signal.signal(signal.SIGINT, sigint_catcher.handle_sigint)
retrieve_beatmap_data(session, args.limit, logger, sigint_catcher)
