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
}


MARKDOWN = {
    "description",
    "flavor",
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
        if output_key in MARKDOWN and value:
            item_data[output_key] = snudown.markdown(value)
        else:
            item_data[output_key] = value or DEFAULTS.get(output_key, "")

    compendium[item_name] = item_data


print json.dumps(
    compendium,
    indent=4,
    sort_keys=True,
)
