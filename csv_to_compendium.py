import csv
import sys
import json

import snudown


FIELDS = {
    "Drop Rate": "rarity",
    "Effect Visibility": "visibility",
    "Title": "title",
    "Damage": "damage",
    "Description": "description",
    "Flavour": "flavor",
}


DEFAULTS = {
    "visibility": "all",
    "damage": 1,
}


CONVERTERS = {
    "damage": int,
    "description": snudown.markdown,
    "flavor": snudown.markdown,
}


csv_file = open(sys.argv[1], "r")
reader = csv.DictReader(csv_file)

compendium = {}
for row in reader:
    item_name = row["Name"]
    item_data = {}

    item_data["targets"] = [x.strip()
                            for x in row["Targets"].split(",") if x.strip()]

    for key, value in row.iteritems():
        output_key = FIELDS.get(key)
        if not output_key:
            continue

        value = value.strip()
        converter = CONVERTERS.get(output_key)
        if converter and value:
            item_data[output_key] = converter(value)
        else:
            item_data[output_key] = value or DEFAULTS.get(output_key, "")

    compendium[item_name] = item_data


print json.dumps(
    compendium,
    indent=4,
    sort_keys=True,
)
