import re

with open("ZMM_DTTS_COCKPIT/Core Data Services/ZR_MM_DTTS_COCKPIT.bdef.md", "r") as f:
    content = f.read()

# In RAP, a factory action should not just be `factory action createWithPopup parameter Z_MM_DTTS_CREATE_PARAM [1];`
# For unmanaged implementations, if you comment out `create`, the framework might struggle with OData V4 routing for a custom factory action that creates instances because it expects the standard `create` entity set segment to be active in some S/4HANA versions.
# The user said: "after i commented create iam getting error Resource not found for segment 'com.sap.gateway.srvd.zsrv_mm_dtts_cockpit.v0001.createWithPopup'"
# This confirms that commenting out `create` breaks the OData Service definition for the factory action.
# So we MUST keep `create;` in the Root BDEF.
# What about the Projection BDEF?
# If we have `use create;` in the Projection BDEF, Fiori displays the generic "Create" button.
# If we comment it out (`//use create;`), Fiori removes the generic "Create" button.
# BUT does commenting out `use create;` in the Projection ALSO remove the OData segment for the EntitySet creation? YES, it disables the POST method on the EntitySet entirely, which also kills factory actions attached to it!
# HOW to fix this?
# We must ENABLE `use create;` in the Projection BDEF to restore the OData segment.
# BUT we must HIDE the standard Fiori "Create" button!
# How to hide the standard Fiori Create button while keeping `use create` active?
# In Fiori Elements, we use the UI annotation:
# `@UI.createHidden: true` on the Root Entity.
# Let's verify this strategy: We restore `use create;` and add `@UI.createHidden: true` in the MDE.

with open("ZMM_DTTS_COCKPIT/Core Data Services/ZR_MM_DTTS_COCKPIT.bdef.md", "w") as f:
    f.write(content)

with open("ZMM_DTTS_COCKPIT/Core Data Services/ZC_MM_DTTS_COCKPIT.bdef.md", "r") as f:
    proj_content = f.read()

proj_content = proj_content.replace("//use create; \" Disabled standard create to enforce popup creation", "use create;")
proj_content = proj_content.replace("//use create;", "use create;") # Just in case

with open("ZMM_DTTS_COCKPIT/Core Data Services/ZC_MM_DTTS_COCKPIT.bdef.md", "w") as f:
    f.write(proj_content)

with open("ZMM_DTTS_COCKPIT/Core Data Services/Z_MM_DTTS_COCKPIT_MDE.md", "r") as f:
    mde_content = f.read()

# Inject @UI.createHidden: true at the header
if "@UI.createHidden: true" not in mde_content:
    mde_content = mde_content.replace("annotate view ZC_MM_DTTS_COCKPIT with\n{", "annotate view ZC_MM_DTTS_COCKPIT with\n{\n  @UI.createHidden: true")

with open("ZMM_DTTS_COCKPIT/Core Data Services/Z_MM_DTTS_COCKPIT_MDE.md", "w") as f:
    f.write(mde_content)
