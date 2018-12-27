import json
import os
import urllib.request

BASE_SEARCH_URL = "https://osu.ppy.sh/beatmapsets/search"
BEATMAPSET_URL = "https://osu.ppy.sh/beatmapsets/"

TRAINING_METADATA_PATH = "training_data/metadata/"

def retrieve_metadata(num_retrieve):
	# Ensure the training data folders have been created.
	os.makedirs(TRAINING_METADATA_PATH, exist_ok=True)

	if num_retrieve <= 0:
		return
	
	cursor_approved_date = None
	cursor_id = None
	
	while True:
		# Request a list of beatmap sets and their metadata.
		if cursor_approved_date and cursor_id:
			request_url = f"{BASE_SEARCH_URL}?cursor%5Bapproved_date%5D={cursor_approved_date}&cursor%5B_id%5D={cursor_id}"
		else:
			request_url = BASE_SEARCH_URL
		
		with urllib.request.urlopen(request_url) as response:
			contents = response.read()
		data = json.loads(contents)

		# Extract cursor data for the next request.
		cursor_data = data["cursor"]
		cursor_approved_date = cursor_data["approved_date"]
		cursor_id = cursor_data["_id"]

		for beatmapset in data["beatmapsets"]:
			bpm = beatmapset["bpm"]
			for beatmap in beatmapset["beatmaps"]:
				# Check that this is an osu standard beatmap.
				if beatmap["mode_int"] == 0:
					beatmap_id = beatmap["id"]
					# Get beatmap specific input features.
					difficulty_rating = beatmap["difficulty_rating"]
					total_length = beatmap["total_length"]
					# And output features.
					cs = beatmap["cs"]
					drain = beatmap["drain"]
					accuracy = beatmap["accuracy"]
					ar = beatmap["ar"]
					
					# Write to training data. Each beatmap is in its own csv file indexed by its id.
					filename = os.path.join(TRAINING_METADATA_PATH, f"{beatmap_id}.csv")
					with open(filename, encoding="utf-8", mode="w") as csv_file:
						# Save entry as a row in the format of [difficulty_rating],[bpm],[total_length],[cs],[drain],[accuracy],[ar].
						print(f"{difficulty_rating},{bpm},{total_length},{cs},{drain},{accuracy},{ar}", file=csv_file)
					
					num_retrieve -= 1
					# Check if the number to retrieve has been met.
					if num_retrieve == 0:
						# This is the earliest ranked beatmap set added to the training data.
						set_id = beatmapset["id"]
						ranked_date = beatmapset["ranked_date"]
						print(f"Earliest ranked beatmap set added to the training data was ranked on {ranked_date}.")
						print(f"{BEATMAPSET_URL}{set_id}")
						return