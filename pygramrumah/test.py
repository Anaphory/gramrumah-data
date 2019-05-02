import re

import pycldf

gramrumah = pycldf.StructureDataset.from_metadata("../cldf/StructureDataset-metadata.json")


values = {}
used_values = {}

for row in gramrumah["ParameterTable"].iterdicts():
    values[row["Parameter_ID"]] = vals = {}
    for kv in row["Possible_Values"].split(";"):
        k, v = kv.split(":")
        vals[k] = (v or "").strip()

valuetable = []
l = []
for row in gramrumah["ValueTable"].iterdicts():
    p, k, v = row["Parameter_ID"], row["Code_ID"], row["Answer"]
    w = values[p].get(k)
    if v == "?":
        k = "?"
        v = "Not known"
    try:
        x = int(v)
        if row["Feature"].startswith("How many") and int(k) == int(v):
            pass
        elif row["Feature"].startswith("How many"):
            row["Source"].insert(0, "needs-check")
            k = v = w = x
        else:
            k = str(x)
            try:
                x = values[p][k]
                int(x)
                row["Source"].insert(0, "needs-check")
            except KeyError:
                row["Source"].insert(0, "needs-check")
            except ValueError:
                v = x.strip()
    except (ValueError, TypeError):
        pass
    if v != w:
        if k == "?" and v == "Not known":
            used_values.setdefault(p, {}).setdefault(k, v)
        row["Source"].insert(0, "needs-check")
    else:
        used_values.setdefault(p, {}).setdefault(k, v)
    row["Code_ID"], row["Answer"] = k, v
    row["Source"] = sorted(set(row["Source"]) - {"nan"})
    valuetable.append(row)

gramrumah["ValueTable"].write(valuetable)

codetable = []
for parameter, items in used_values.items():
    for name, description in items.items():
        description = '' if description is None else str(description)
        desc = re.sub('[^0-9a-zA-Z_]', '', description)
        codetable.append({
            "ID": "{parameter:}-{desc:}".format(parameter=parameter, desc=desc),
            "Parameter_ID": parameter,
            "Name": name,
            "Description": description.strip()
        })

gramrumah["CodeTable"].write(codetable)
