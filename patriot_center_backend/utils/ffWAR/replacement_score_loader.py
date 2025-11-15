import os
import json
REPLACEMENT_SCORE_FILE = "patriot_center_backend/data/ffWAR/replacement_score.json"


def replacement_score_loader():
    # Check if the file exists
    if os.path.exists(REPLACEMENT_SCORE_FILE):
        with open(REPLACEMENT_SCORE_FILE, "r") as file:
            data = json.load(file)

    return data