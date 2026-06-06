import os

file_path_r = "ZMM_DTTS_COCKPIT/Core Data Services/ZR_MM_DTTS_COCKPIT.bdef.md"
with open(file_path_r, "r") as f:
    content = f.read()

content = content.replace(
    "factory action createWithPopup parameter Z_MM_DTTS_CREATE_PARAM [1];",
    "static action createWithPopup parameter Z_MM_DTTS_CREATE_PARAM;"
)

with open(file_path_r, "w") as f:
    f.write(content)

print("Root BDEF updated.")
