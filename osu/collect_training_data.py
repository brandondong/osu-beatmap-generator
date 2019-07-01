import argparse
from html.parser import HTMLParser
import os
import shutil
import zipfile

import requests

from beatmap.beatmap import Beatmap

OSU_SIGNIN_PAGE = "https://osu.ppy.sh/home"
# Recently ranked beatmapsets with osu standard filter.
BASE_SEARCH_URL = "https://osu.ppy.sh/beatmapsets/search?m=0"
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
            process_beatmapset(session, beatmapset, is_debug)
            count_beatmapsets_retrieved += 1
            if count_beatmapsets_retrieved >= beatmapset_limit:
                return


def process_beatmapset(session, beatmapset, is_debug):
    validate_beatmapset(beatmapset)
    # Download the beatmap and extract it to a temporary directory.
    temp_dir = "temp"
    retrieve_beatmapset(session, beatmapset, temp_dir, is_debug)

    # Process all the .osu files.
    valid_beatmaps = []
    for file in os.listdir(temp_dir):
        if is_osu_file(file):
            full_path = os.path.join(temp_dir, file)
            try:
                beatmap = Beatmap.from_osu_file(full_path)
                valid_beatmaps.append(beatmap)
            except Exception as e:
                # Beatmap doesn't meet training data criteria.
                debug_print(f"Skipping beatmap: {e}", is_debug)

    # Finished. Remove the temporary directory.
    shutil.rmtree(temp_dir)


def is_osu_file(file):
    _, ext = os.path.splitext(file)
    return ext.lower() == ".osu"


def retrieve_beatmapset(session, beatmapset, out_dir, is_debug):
    beatmapset_id = beatmapset["id"]
    beatmapset_download_link = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}/download?noVideo=1"
    debug_print(
        f"Retrieving beatmapset: {beatmapset_download_link}.", is_debug)
    response = session.get(beatmapset_download_link)
    temp_file = "temp.zip"
    with open(temp_file, "wb") as f:
        f.write(response.content)
    debug_print(
        "Download finished.", is_debug)
    with zipfile.ZipFile(temp_file, "r") as zip_ref:
        zip_ref.extractall(out_dir)
    os.remove(temp_file)


def validate_beatmapset(beatmapset):
    # Sanity check that there are osu standard beatmaps in the beatmapset.
    contains_standard = any(
        beatmap["mode_int"] == OSU_STANDARD_MODE for beatmap in beatmapset["beatmaps"])
    if not contains_standard:
        raise Exception("osu standard filter failed.")


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
os.makedirs(TRAINING_PATH, exist_ok=True)
# Login to osu in order to be able to download beatmapsets.
session = login_to_osu(args.username, args.password, args.debug)
retrieve_beatmap_data(session, args.limit, args.debug)
