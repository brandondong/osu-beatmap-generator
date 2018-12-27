import sys

from data_collection import beatmap_info_retriever

num_retrieve = 1000
if len(sys.argv) == 2:
	num_retrieve = int(sys.argv[1])

beatmap_info_retriever.retrieve_metadata(num_retrieve)