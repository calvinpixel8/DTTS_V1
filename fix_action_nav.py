import os
import re

file_path = "ZMM_DTTS_COCKPIT/Core Data Services/Z_MM_DTTS_COCKPIT_MDE.md"

with open(file_path, "r") as f:
    content = f.read()

# Replace the createWithPopup action line
old_action = "{ type: #FOR_ACTION, dataAction: 'createWithPopup', label: 'Create' }"
new_action = "{ type: #FOR_ACTION, dataAction: 'createWithPopup', label: 'Create', invocationGrouping: #ISOLATED }"

if old_action in content:
    content = content.replace(old_action, new_action)
    with open(file_path, "w") as f:
        f.write(content)
    print("Action updated to ISOLATED to prevent navigation.")
else:
    print("Action string not found. Need to check exact string.")
