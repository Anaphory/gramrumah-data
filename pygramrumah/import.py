from pathlib import Path

import json

import re
from difflib import get_close_matches

import xlrd
import pyexcel_ods3 as odsrd
import pycldf

def read_rows_excel(filename):
    for row in xlrd.open_workbook(filename).sheet_by_index(0).get_rows():
        yield [cell.value for cell in row]

def read_rows_ods(filename):
    first_sheet, content = odsrd.get_data(filename).popitem(last=False)
    for row in content:
        yield row

df = pycldf.Dataset.from_metadata(Path(__file__).parent.parent / "cldf" / "StructureDataset-metadata.json")
features = {row["Feature"]: row for row in df["ParameterTable"].iterdicts()}

rows = list(df["ValueTable"].iterdicts())
values = {row["ID"]: row for row in df["CodeTable"].iterdicts()}


def read(lect, filename):
    errors = []
    header = None
    for cells in read_rows_ods(filename):
        if "a_text" in cells:
            # Found the header
            header = cells
            continue
        elif not header:
            continue
        data = dict(zip(header, cells))
        if "q_text" not in data:
            continue
        if re.match("[0-9]\. [A-Z][a-z ]*", data.get("q_text", "")):
            # Section header
            continue
        if re.match("^[A-Z ]*$", data.get("q_text", "")):
            # Section header
            continue
        feature = None
        matches = get_close_matches(data["q_text"], features, 1, 0.9)
        if matches:
            if matches[0].replace("order", "relative position") != data["q_text"].replace(",", ";"):
                print(matches[0])
                print(data["q_text"])
                if not input():
                    errors.append(data)
                    continue
            feature = features.pop(matches[0])
        if feature:
            parameter = feature["Parameter_ID"]
            answer =  str(data.get("a_text")).lower()
            code = "{:}-{:}".format(parameter, re.sub('[^0-9a-zA-Z_]', '', answer))
            try:
                formal_answer = values[code]
            except KeyError:
                formal_answer = values[code] = {
                    "ID": code,
                    "Parameter_ID": parameter,
                    "Name": answer,
                    "Description": answer}
            if formal_answer["Description"] != answer:
                print("In {:}, expected code {:}, but found code {:}.".format(
                    code, formal_answer["Description"], answer))
            row = {
                "ID": "{:}-{:}".format(lect, parameter),
                "Parameter_ID": parameter,
                "Language_ID": lect,
                "Feature": feature["Feature"],
                "Code_ID": formal_answer["ID"],
                "Answer": answer,
                "Comment": data.get("a_notes"),
                "Source": [data.get("a_reference")]
            }
            rows.append(row)
        else:
            errors.append(data)
    return errors


for filename, lect in [
        ("/vol/winshare/Public/ResearchData/HUM/LUCL-KlamerVICI/New languages for GramRumah/Questionnaire MK_2016_typological_questionnaire_Kafoa.ods",
         "kafo1240"),
        ("/vol/winshare/Public/ResearchData/HUM/LUCL-KlamerVICI/New languages for GramRumah/Questionnaire MK_2016_typological_questionnaire_Kui.ods",
         "kuii1253"),
        ("/vol/winshare/Public/ResearchData/HUM/LUCL-KlamerVICI/New languages for GramRumah/Questionnaire MK_2016_typological_questionnaire_Kula.ods",
         "kula1280-lanto"),
]:
    errors = read(lect, filename)
    with Path(filename).with_suffix(".json").open("w") as jsonfile:
        json.dump(errors, jsonfile)

df["ValueTable"].write(rows)
values = sorted(values.values(), key=lambda x: x["ID"])
df["CodeTable"].write(values)
