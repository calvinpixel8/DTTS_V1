import re

with open("ZMM_DTTS_COCKPIT/Core Data Services/Z_MM_DTTS_COCKPIT_MDE.md", "r") as f:
    content = f.read()

# Add the factory action to the UI.lineItem of matdoc (alongside reprocess).
old_matdoc_annotation = """  @UI.lineItem:       [{ type: #FOR_ACTION, dataAction: 'reprocess', label: 'Reprocess' },
                       { position: 120, label: 'Material Document' }]
  matdoc;"""

new_matdoc_annotation = """  @UI.lineItem:       [{ type: #FOR_ACTION, dataAction: 'createWithPopup', label: 'Create' },
                       { type: #FOR_ACTION, dataAction: 'reprocess', label: 'Reprocess' },
                       { position: 120, label: 'Material Document' }]
  matdoc;"""

content = content.replace(old_matdoc_annotation, new_matdoc_annotation)

with open("ZMM_DTTS_COCKPIT/Core Data Services/Z_MM_DTTS_COCKPIT_MDE.md", "w") as f:
    f.write(content)
