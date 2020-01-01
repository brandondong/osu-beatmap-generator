import argparse

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("username", help="osu username")
parser.add_argument("password", help="osu password")
parser.add_argument("--limit", help="maximum number of beatmaps to retrieve",
                    type=int, default=1000)
args = parser.parse_args()
