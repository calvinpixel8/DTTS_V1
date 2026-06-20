import os

file_path = "ZMM_DTTS_COCKPIT/Source Code Library/ZCL_MM_DTTS_COCKPIT_BDEF.md"
with open(file_path, "r") as f:
    content = f.read()

# Replace the mapped-item assignment in createWithPopup so it doesn't return anything mapped, thus no navigation.
# Also append the created record directly to lcl_buffer=>mt_create to bypass navigation if we use static action.
# Wait, if we use static action, `keys` only has `%cid` and `%param`, it does not have `%tky` of an existing instance.
# If we do MODIFY ENTITIES IN LOCAL MODE CREATE, it creates the entity and it works.
# But returning `mapped-item = ls_mapped-item` is what causes the UI to navigate to the new item.
# We can just remove `mapped-item = ls_mapped-item.` or report a success message.

old_meth = """    MODIFY ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
      ENTITY Item
      CREATE FIELDS ( doc_year matdoc mvttype item_no tran_id gtin prodqty produnit batch expdate operation frm_gln to_gln prodstat createddate createdtime createdby )
      WITH lt_create
      MAPPED DATA(ls_mapped)
      FAILED DATA(ls_failed)
      REPORTED DATA(ls_reported).

    mapped-item = ls_mapped-item."""

new_meth = """    MODIFY ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
      ENTITY Item
      CREATE FIELDS ( doc_year matdoc mvttype item_no tran_id gtin prodqty produnit batch expdate operation frm_gln to_gln prodstat createddate createdtime createdby )
      WITH lt_create
      MAPPED DATA(ls_mapped)
      FAILED DATA(ls_failed)
      REPORTED DATA(ls_reported).

    " Do not map the result to prevent navigation to the object page
    " mapped-item = ls_mapped-item.

    " Add success message
    LOOP AT lt_create INTO DATA(ls_create).
      APPEND VALUE #( %cid = ls_create-%cid
                      %msg = new_message( id       = 'ZMM_DTTS'
                                          number   = '000'
                                          severity = if_abap_behv_message=>severity-success
                                          v1       = 'Data saved in table' ) ) TO reported-item.
    ENDLOOP."""

if old_meth in content:
    content = content.replace(old_meth, new_meth)
    with open(file_path, "w") as f:
        f.write(content)
    print("Class updated.")
else:
    print("String not found in Class.")
