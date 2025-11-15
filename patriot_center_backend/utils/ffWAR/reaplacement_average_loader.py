import os
import json
REPLACEMENT_AVERAGE_FILE = "patriot_center_backend/data/ffWAR/replacement_average.json"
    

def replacement_average_loader():
    # Check if the file exists
    if os.path.exists(REPLACEMENT_AVERAGE_FILE):
        with open(REPLACEMENT_AVERAGE_FILE, "r") as file:
            data = json.load(file)

    return data