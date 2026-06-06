import os

file_path = "ZMM_DTTS_COCKPIT/Source Code Library/ZCL_MM_DTTS_COCKPIT_BDEF.md"
with open(file_path, "r") as f:
    content = f.read()

# Since createWithPopup is a static action, reported-item doesn't exist for the static keys properly.
# Actually, the signature is:
# IMPORTING keys FOR ACTION Item~createWithPopup.
# The `keys` parameter contains `%cid` and `%param`.
# `reported-item` does exist because it's part of the standard behavior response structures.

# Also, the message class 'ZMM_DTTS' with number '000' might not exist or we should use a more generic way
# or ensure it works.
