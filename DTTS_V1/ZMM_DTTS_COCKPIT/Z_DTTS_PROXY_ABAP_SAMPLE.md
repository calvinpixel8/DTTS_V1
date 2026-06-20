Code
*&---------------------------------------------------------------------*
*& Report Z_DTTS_REPROCESS_COCKPIT
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT Z_DTTS_REPROCESS_COCKPIT.
TABLES: mseg.
*" Variables for dynamic proxy-based web service call (config-driven via ZMM_DTTS_API_
CON)
DATA: request_ptr
inter

TYPE REF TO data,

"Dynamic request structure po

response_ptr
ointer

TYPE REF TO data,

"Dynamic response structure p

lo_proxy
p_lport

TYPE REF TO object,
TYPE prx_logical_port_name,

"Web service proxy object
"Logical port name for proxy

ptab

TYPE abap_parmbind_tab,

"Parameter binding table for

wa_ptab

TYPE abap_parmbind,

"Single parameter binding ent

proxy
ry
wa_zmm_dtts_api_con TYPE zmm_dtts_api_con.

"API config row (proxy class,

method etc.)
TYPES: BEGIN OF ty_alv_data,

Code

selkz
"mandt

TYPE char1,
TYPE mandt,

tran_id

TYPE n LENGTH 20,

item_no
zeile

TYPE numc4,
TYPE mblpo,

product
prod_name

TYPE matnr,
TYPE maktx,

prod_qty
prod_unit

TYPE menge_d,
TYPE meins,

gtin

TYPE z_dgtin,

batch
exp_date

TYPE charg_d,
TYPE vfdat,

notif_id
tr_response

TYPE char50,
TYPE string,

mat_doc
mvt_type

TYPE mblnr,
TYPE bwart,

sr_number
created_date

TYPE char50,
TYPE dats,

created_time

TYPE tims,

created_by
changed_date

TYPE xubname,
TYPE dats,

changed_time
changed_by

TYPE tims,
TYPE xubname,

prod_stat
trans_stat

TYPE char10,
TYPE char10,

doc_year

TYPE mjahr,

1

item_operation

TYPE char20,

header_operation TYPE char20,
frm_gln
TYPE zmm_sst_gln_src,
to_gln
auth_gln

TYPE zmm_sst_gln_des,
TYPE zmm_sst_gln_auth,

END OF ty_alv_data.
DATA: gt_alv_data TYPE TABLE OF ty_alv_data.
*----------------------------------------------------------------------*
* SELECTION SCREEN
*----------------------------------------------------------------------*
SELECTION-SCREEN BEGIN OF BLOCK b1 WITH FRAME TITLE TEXT-001.
SELECT-OPTIONS: s_matdoc FOR mseg-mblnr,
s_year
s_bwart

FOR mseg-mjahr,
FOR mseg-bwart.

PARAMETERS: p_oper TYPE char20.
SELECTION-SCREEN END OF BLOCK b1.
*----------------------------------------------------------------------*
* LOCAL CLASS DEFINITION
*----------------------------------------------------------------------*
CLASS lcl_dtts_cockpit DEFINITION.
PUBLIC SECTION.
TYPES: BEGIN OF ty_alv_data,
selkz

TYPE char1,

"mandt
tran_id

TYPE mandt,
TYPE ztran_id,

item_no
zeile

TYPE numc4,
TYPE mblpo,

product
prod_name

TYPE matnr,
TYPE maktx,

prod_qty
prod_unit

TYPE menge_d,
TYPE meins,

gtin

TYPE z_dgtin,

batch
exp_date

TYPE charg_d,
TYPE vfdat,

notif_id
tr_response

TYPE char50,
TYPE string,

mat_doc
mvt_type

TYPE mblnr,
TYPE bwart,

sr_number

TYPE char50,

created_date
created_time

TYPE dats,
TYPE tims,

created_by
changed_date

TYPE xubname,
TYPE dats,

changed_time
changed_by

TYPE tims,
TYPE xubname,

prod_stat
trans_stat

TYPE char10,
TYPE char10,

doc_year

TYPE mjahr,

item_operation
TYPE char20,
header_operation TYPE char20,
frm_gln
to_gln

TYPE zmm_sst_gln_src,
TYPE zmm_sst_gln_des,

auth_gln
TYPE zmm_sst_gln_auth,
END OF ty_alv_data.

Code

2

DATA: gt_alv_data TYPE TABLE OF ty_alv_data.
DATA: go_alv

TYPE REF TO cl_gui_alv_grid,

go_container TYPE REF TO cl_gui_custom_container.
METHODS:
get_data,
display_alv,
handle_user_command FOR EVENT user_command OF cl_gui_alv_grid
IMPORTING e_ucomm,
handle_toolbar FOR EVENT toolbar OF cl_gui_alv_grid
IMPORTING e_object e_interactive.
PRIVATE SECTION.
METHODS:
reprocess_selected_items.
ENDCLASS.
*----------------------------------------------------------------------*
* LOCAL CLASS IMPLEMENTATION
*----------------------------------------------------------------------*
CLASS lcl_dtts_cockpit IMPLEMENTATION.
METHOD get_data.
" Retrieve data based on selection screen
" ZIMMDTTS_4 is a view mapping to ZIMM_DTTS_FY_HELPER left outer join zmm_sst_dtts
_hdr
SELECT ""itm~mandt,
itm~tran_id,
itm~item_no,
itm~zeile,
itm~product,
itm~prod_name,
itm~prod_qty,
itm~prod_unit,
itm~gtin,
itm~batch,
itm~exp_date,
itm~notif_id,
itm~tr_response,
itm~mat_doc,
itm~mvt_type,
itm~sr_number,
itm~created_date,
itm~created_time,
itm~created_by,
itm~changed_date,
itm~changed_time,
itm~changed_by,
itm~prod_stat,
itm~trans_stat,
itm~doc_year,
itm~item_operation,
hdr~operation AS header_operation,
hdr~frm_gln,
hdr~to_gln,

Code

3

hdr~auth_gln
FROM zimmdtts_4 AS itm
LEFT OUTER JOIN zmm_sst_dtts_hdr AS hdr ON

itm~mat_doc = hdr~mat_doc

AND itm~doc_year = hdr~doc_yr
AND itm~mvt_type
= hdr~mvt_type
WHERE itm~mat_doc IN @s_matdoc
AND itm~doc_year IN @s_year
AND itm~mvt_type IN @s_bwart
""AND hdr~operation = @p_oper
INTO CORRESPONDING FIELDS OF TABLE @gt_alv_data.

IF sy-subrc <> 0.
MESSAGE 'No data found for the given selection criteria.' TYPE 'S' DISPLAY LIKE
'E'.
ENDIF.
ENDMETHOD.
METHOD display_alv.
DATA: lt_fcat
TYPE lvc_t_fcat,
ls_layout TYPE lvc_s_layo.
IF go_container IS INITIAL.
" Need to create a screen 0100 for this ALV or use full screen CL_SALV_TABLE.
" For simplicity in full screen without screen painter, we use cl_gui_alv_grid w
ith default full screen container.
*
*

CREATE OBJECT go_alv
EXPORTING

*

i_parent = cl_gui_container=>screen0.
CREATE OBJECT go_container
EXPORTING
container_name = 'CC_ALV'.
CREATE OBJECT go_alv
EXPORTING
i_parent = go_container.
" Prepare layout
ls_layout-sel_mode = 'A'.
ls_layout-box_fname = 'SELKZ'.
" Build Field Catalog dynamically or manually
CALL FUNCTION 'LVC_FIELDCATALOG_MERGE'
EXPORTING

i_structure_name = 'ZIMM_DTTS_FY_HELPER' " Approximation, manual setup is be
tter for custom fields
CHANGING
ct_fieldcat

= lt_fcat

EXCEPTIONS
OTHERS
= 1.
DATA ls_fcat LIKE LINE OF lt_fcat.
CLEAR ls_fcat.
ls_fcat-fieldname = 'SELKZ'.
ls_fcat-checkbox = 'X'.
ls_fcat-edit

Code

= 'X'.

4

APPEND ls_fcat TO lt_fcat.
CLEAR ls_fcat.
" Mark fields as editable (allow user to edit data in ALV directly)
LOOP AT lt_fcat ASSIGNING FIELD-SYMBOL(<fs_fcat>).
<fs_fcat>-edit = 'X'.
ENDLOOP.
" Set Handlers
SET HANDLER me->handle_toolbar FOR go_alv.
SET HANDLER me->handle_user_command FOR go_alv.
" Display ALV
go_alv->set_table_for_first_display(
EXPORTING
is_layout

= ls_layout

CHANGING
it_outtab
= gt_alv_data
it_fieldcatalog = lt_fcat ).
ELSE.
go_alv->refresh_table_display( ).
ENDIF.
ENDMETHOD.
METHOD handle_toolbar.
DATA: ls_toolbar TYPE stb_button.
CLEAR ls_toolbar.
ls_toolbar-function = 'REPROCESS'.
ls_toolbar-icon = '@5C@'. " Reprocess Icon
ls_toolbar-quickinfo = 'Reprocess Selected Items'.
ls_toolbar-butn_type = 0.
ls_toolbar-text = 'Reprocess'.
APPEND ls_toolbar TO e_object->mt_toolbar.
ENDMETHOD.
METHOD handle_user_command.
CASE e_ucomm.
WHEN 'REPROCESS'.
go_alv->check_changed_data( ).
me->reprocess_selected_items( ).
ENDCASE.
ENDMETHOD.

METHOD reprocess_selected_items.
DATA: lt_selected
TYPE TABLE OF ty_alv_data,
lt_unique
lt_header

TYPE TABLE OF ty_alv_data,
TYPE TABLE OF zmm_sst_dtts_hdr,

lt_items

TYPE TABLE OF zmm_sst_dtts_itm,

lt_mseg
TYPE TABLE OF mseg,
wa_zmm_dtts_api_con TYPE zmm_dtts_api_con,

Code

ptab
wa_ptab

TYPE abap_parmbind_tab,
LIKE LINE OF ptab,

p_lport
lo_proxy

TYPE prx_logical_port_name,
TYPE REF TO object.

5

" 1. Extract selected lines
LOOP AT gt_alv_data INTO DATA(ls_alv) WHERE selkz = 'X'.
APPEND ls_alv TO lt_selected.
ENDLOOP.
IF lt_selected IS INITIAL.
MESSAGE 'Please select at least one item to reprocess.' TYPE 'I'.
RETURN.
ENDIF.
" 2. Remove items that have status SUCCESS
DELETE lt_selected WHERE prod_stat = 'SUCCESS'.
IF lt_selected IS INITIAL.
MESSAGE 'No eligible items to reprocess (all selected were SUCCESS).' TYPE 'I'.
RETURN.
ENDIF.
" 3. Sort selected items using key matdoc, mjahr and movement type
SORT lt_selected BY mat_doc doc_year mvt_type.
" 4. Create a new table with only unique matdoc, mjahr and movement type
lt_unique = lt_selected.
DELETE ADJACENT DUPLICATES FROM lt_unique COMPARING mat_doc doc_year mvt_type.
" 5. Loop in this unique table
LOOP AT lt_unique INTO DATA(ls_unique).
CLEAR: lt_header, lt_items.
" Get the header row from header table and append it
SELECT * FROM zmm_sst_dtts_hdr
INTO TABLE @DATA(lt_hdr_tmp)
WHERE mat_doc = @ls_unique-mat_doc
AND doc_yr = @ls_unique-doc_year
AND mvt_type = @ls_unique-mvt_type.
APPEND LINES OF lt_hdr_tmp TO lt_header.
DATA(lv_operation) = ls_unique-header_operation.
" Loop at the selected items table for the item lines and append to lt_items
LOOP AT lt_selected INTO DATA(ls_sel_item)
WHERE mat_doc = ls_unique-mat_doc
AND doc_year = ls_unique-doc_year
AND mvt_type = ls_unique-mvt_type.
DATA: ls_item TYPE zmm_sst_dtts_itm.
MOVE-CORRESPONDING ls_sel_item TO ls_item.
APPEND ls_item TO lt_items.
ENDLOOP.
" =============================================================
" LOAD API CONFIGURATION FROM ZMM_DTTS_API_CON
" =============================================================
SELECT SINGLE * FROM zmm_dtts_api_con INTO @wa_zmm_dtts_api_con
WHERE api_name = @lv_operation.

Code

6

IF sy-subrc = 0.
" Dynamically create request and response objects based on config
CREATE DATA request_ptr TYPE (wa_zmm_dtts_api_con-request_structure).
ASSIGN request_ptr->* TO FIELD-SYMBOL(<fs_request>).
CREATE DATA response_ptr TYPE (wa_zmm_dtts_api_con-response_structure).
ASSIGN response_ptr->* TO FIELD-SYMBOL(<fs_response>).
" =============================================================
" BUILD API REQUEST BASED ON OPERATION TYPE
" =============================================================
CASE lv_operation.
WHEN 'ACCEPT'.
PERFORM accept_request

USING lt_mseg lt_header lt_items CHANGING <fs_req

uest>.
WHEN 'RETURN'.
PERFORM return_request

USING lt_mseg lt_header lt_items CHANGING <fs_req

uest>.
WHEN 'DISPATCH'.
PERFORM dispatch_request

USING lt_mseg lt_header lt_items CHANGING <fs_r

equest>.
WHEN 'DISPATCH_CANCEL'.
PERFORM dispatch_cancel_request

USING lt_mseg lt_header lt_items CHANGIN

G <fs_request>.
WHEN 'TRANSFER'.
PERFORM transfer_request

USING lt_mseg lt_header lt_items CHANGING <fs_r

equest>.
WHEN 'TRANSFER_CANCEL'.
PERFORM transfer_cancel_request
G <fs_request>.
WHEN 'CONSUME'.
PERFORM consume_request

USING lt_mseg lt_header lt_items CHANGIN

USING lt_mseg lt_header lt_items CHANGING <fs_re

quest>.
WHEN 'CONSUME_CANCEL'.
PERFORM consume_cancel_request

USING lt_mseg lt_header lt_items CHANGING

<fs_request>.
WHEN 'DRUG_SALE'.
PERFORM pharmacy_sale_request
<fs_request>.

USING lt_mseg lt_header lt_items CHANGING

WHEN 'DRUG_SALE_CANCEL'.
PERFORM pharmacy_sale_cancel_request
ANGING <fs_request>.
WHEN 'DEACTIVATE'.
PERFORM deactivate_request

USING lt_mseg lt_header lt_items CH

USING lt_mseg lt_header lt_items CHANGING <fs

_request>.
WHEN 'DEACTIVATE_CANCEL'.
PERFORM deactivate_cancel_request
ING <fs_request>.

USING lt_mseg lt_header lt_items CHANG

ENDCASE.
" =============================================================
" CREATE PROXY AND CALL DTTS WEB SERVICE
" =============================================================
CLEAR ptab.
CLEAR wa_ptab.
wa_ptab-name

Code

= 'LOGICAL_PORT_NAME'.

7

wa_ptab-kind

= cl_abap_objectdescr=>exporting.

p_lport = wa_zmm_dtts_api_con-logical_port.
wa_ptab-value = REF #( p_lport ).
INSERT wa_ptab INTO TABLE ptab.
TRY.
CREATE OBJECT lo_proxy TYPE (wa_zmm_dtts_api_con-proxy_class)
PARAMETER-TABLE ptab.
CALL METHOD lo_proxy->(wa_zmm_dtts_api_con-method_name)
EXPORTING
input = <fs_request>
IMPORTING
output = <fs_response>.
" ==========================================================
" PROCESS API RESPONSE AND UPDATE Z-TABLE RECORDS
" ==========================================================
CASE lv_operation.
WHEN 'ACCEPT'.
PERFORM accept_response

USING <fs_response> CHANGING lt_header lt_it

ems.
WHEN 'RETURN'.
PERFORM return_response

USING <fs_response> CHANGING lt_header lt_it

ems.
WHEN 'DISPATCH'.
PERFORM dispatch_response

USING <fs_response> CHANGING lt_header lt_

items.
WHEN 'DISPATCH_CANCEL'.
PERFORM dispatch_cancel_response

USING <fs_response> CHANGING lt_hea

der lt_items.
WHEN 'TRANSFER'.
PERFORM transfer_response

USING <fs_response> CHANGING lt_header lt_

items.
WHEN 'TRANSFER_CANCEL'.
PERFORM transfer_cancel_response

USING <fs_response> CHANGING lt_hea

der lt_items.
WHEN 'CONSUME'.
PERFORM consume_response

USING <fs_response> CHANGING lt_header lt_i

tems.
WHEN 'CONSUME_CANCEL'.
PERFORM consume_cancel_response

USING <fs_response> CHANGING lt_head

er lt_items.
WHEN 'DRUG_SALE'.
PERFORM pharmacy_sale_response

USING <fs_response> CHANGING lt_heade

r lt_items.
WHEN 'DRUG_SALE_CANCEL'.
PERFORM pharmacy_sale_cancel_response

USING <fs_response> CHANGING l

t_header lt_items.
WHEN 'DEACTIVATE'.
PERFORM deactivate_response

USING <fs_response> CHANGING lt_header l

t_items.
WHEN 'DEACTIVATE_CANCEL'.
PERFORM deactivate_cancel_response

USING <fs_response> CHANGING lt_h

eader lt_items.
ENDCASE.

Code

8

" Custom Table updates for reprocess
IF lt_header IS NOT INITIAL.
MODIFY zmm_sst_dtts_hdr FROM TABLE lt_header.
ENDIF.
" Instead of ZMM_SST_DTTS_ITM, we append a new line to ZMM_SST_DTTSIT2 if
it does not exist,
" else modify the status alone. The new line will have same data as old ta
ble except PROD_STAT and Trans Status.
LOOP AT lt_items INTO DATA(ls_new_item).
DATA: ls_dttsit2 TYPE zmm_sst_dttsit2.
" Check if line exists
SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @ls_dttsit2
"WHERE mandt
= @ls_new_item-mandt
WHERE tran_id = @ls_new_item-tran_id
AND item_no = @ls_new_item-item_no.
IF sy-subrc = 0.
" Record exists, just modify status
ls_dttsit2-prod_stat = ls_new_item-prod_stat.
ls_dttsit2-trans_stat = ls_new_item-trans_stat.
MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
ELSE.
" Record doesn't exist, append new line using data from old table with
new status
MOVE-CORRESPONDING ls_new_item TO ls_dttsit2.
" Set new PROD_STAT and TRANS_STAT handled by response FORM previously
INSERT zmm_sst_dttsit2 FROM ls_dttsit2.
ENDIF.
ENDLOOP.
CATCH cx_ai_application_fault INTO DATA(lx_app_fault).
PERFORM handle_dtts_application_fault
USING lx_app_fault lv_operation CH
ANGING lt_items lt_header.
CATCH cx_ai_system_fault INTO DATA(lx_sys).
PERFORM handle_api_error_multiple

USING lx_sys CHANGING lt_items lt_head

er.
CATCH cx_root INTO DATA(lx_root).
PERFORM handle_generic_error_multiple

USING lx_root CHANGING lt_items lt

_header.
ENDTRY.
ENDIF.
ENDLOOP.
MESSAGE 'Reprocessing Completed.' TYPE 'S'.
ENDMETHOD.

ENDCLASS.
*----------------------------------------------------------------------*
* MAIN PROGRAM EXECUTION
*----------------------------------------------------------------------*
DATA: go_main TYPE REF TO lcl_dtts_cockpit.

Code

9

START-OF-SELECTION.
CREATE OBJECT go_main.
go_main->get_data( ).
CALL SCREEN 0100. " Assume a screen 0100 is created to host the ALV container
*&---------------------------------------------------------------------*
*& Module STATUS_0100 OUTPUT
*&---------------------------------------------------------------------*
MODULE status_0100 OUTPUT.
SET PF-STATUS 'STANDARD'.
go_main->display_alv( ).
ENDMODULE.
*&---------------------------------------------------------------------*
*& Module USER_COMMAND_0100 INPUT
*&---------------------------------------------------------------------*
MODULE user_command_0100 INPUT.
CASE sy-ucomm.
WHEN 'BACK' OR 'EXIT' OR 'CANC'.
LEAVE TO SCREEN 0.
ENDCASE.
ENDMODULE.
*&---------------------------------------------------------------------*
*& SECTION 2: REQUEST PREPARATION FORMS
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*& Form ACCEPT_REQUEST
*&---------------------------------------------------------------------*
FORM accept_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zaccept_service_request.
DATA: lwa_request
lwa_product_line
lv_gtin_formatted

TYPE zaccept_service_request,
TYPE zaccept_service_request_produ1,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_from_gln
lv_auth_gln

TYPE zmm_br_gln,
TYPE zmm_br_gln.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

" Get GLNs from header record
READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_from_gln = <fs_header>-frm_gln.
lv_auth_gln = <fs_header>-to_gln.
ENDIF.

Code

10

" Loop through ITEMS to build product list
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
" Format data from item record (has GTIN, BATCH, EXP_DATE, QUANTITY)
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin
= lv_gtin_formatted.
lwa_product_line-quantity = lv_quantity_formatted.
lwa_product_line-bn

= lv_batch_formatted.

lwa_product_line-xd

= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-accept_batch_service_request-productlist-pr
oduct.
ENDLOOP.
lwa_request-accept_batch_service_request-fromgln = lv_from_gln.
lwa_request-accept_batch_service_request-authgln = lv_auth_gln.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form

RETURN_REQUEST

*&---------------------------------------------------------------------*
FORM return_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zreturn_batch_service_request.
DATA: lwa_request
lwa_product_line
lv_gtin_formatted

TYPE zreturn_batch_service_request,
TYPE zreturn_batch_service_request3,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_to_gln
TYPE zmm_br_gln,
lv_auth_gln

TYPE zmm_br_gln.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_to_gln = <fs_header>-to_gln.
lv_auth_gln = <fs_header>-frm_gln.

Code

11

ENDIF.
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin
= lv_gtin_formatted.
lwa_product_line-quantity = lv_quantity_formatted.
lwa_product_line-bn

= lv_batch_formatted.

lwa_product_line-xd

= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-return_batch_service-productlist-product.
ENDLOOP.
lwa_request-return_batch_service-togln = lv_to_gln.
lwa_request-return_batch_service-authgln = lv_auth_gln.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form DISPATCH_REQUEST
*&---------------------------------------------------------------------*
FORM dispatch_request

USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zdispatch_batch_service_reque3.

DATA: lwa_request
lwa_product_line

TYPE zdispatch_batch_service_reque3,
TYPE zdispatch_batch_service_reque1,

lv_gtin_formatted
TYPE string,
lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_to_gln
lv_auth_gln

TYPE zmm_br_gln,
TYPE zmm_br_gln.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_to_gln = <fs_header>-to_gln.
lv_auth_gln = <fs_header>-frm_gln.
ENDIF.

Code

12

LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin
= lv_gtin_formatted.
lwa_product_line-quantity = lv_quantity_formatted.
lwa_product_line-bn
lwa_product_line-xd

= lv_batch_formatted.
= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-dispatch_batch_service-productlist-product.
ENDLOOP.
lwa_request-dispatch_batch_service-togln = lv_to_gln.
lwa_request-dispatch_batch_service-authgln = lv_auth_gln.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form DISPATCH_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM dispatch_cancel_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zdispatch_cancel_request.
DATA: lwa_request
lwa_product_line
lv_gtin_formatted

TYPE zdispatch_cancel_request,
TYPE zdispatch_cancel_request_prod1,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_to_gln
lv_auth_gln

TYPE zmm_br_gln,
TYPE zmm_br_gln.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_to_gln = <fs_header>-frm_gln.
lv_auth_gln = <fs_header>-to_gln.
ENDIF.
LOOP AT p_items_table ASSIGNING <fs_item>.

Code

13

**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin
= lv_gtin_formatted.
lwa_product_line-quantity = lv_quantity_formatted.
lwa_product_line-bn
lwa_product_line-xd

= lv_batch_formatted.
= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-dispatch_cancel-productlist-product.
ENDLOOP.
lwa_request-dispatch_cancel-togln = lv_to_gln.
lwa_request-dispatch_cancel-authgln = lv_auth_gln.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form TRANSFER_REQUEST
*&---------------------------------------------------------------------*
FORM transfer_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE ztransfer_batch_service_reque3.
DATA: lwa_request
lwa_product_line
lv_gtin_formatted

TYPE ztransfer_batch_service_reque3,
TYPE ztransfer_batch_service_reque2,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_to_gln
lv_auth_gln

TYPE zmm_br_gln,
TYPE zmm_br_gln.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_to_gln = <fs_header>-to_gln.
lv_auth_gln = <fs_header>-frm_gln.
ENDIF.
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.

Code

14

CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin
= lv_gtin_formatted.
lwa_product_line-quantity = lv_quantity_formatted.
lwa_product_line-bn
lwa_product_line-xd

= lv_batch_formatted.
= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-transfer_batch_service-productlist-product.
ENDLOOP.
lwa_request-transfer_batch_service-togln = lv_to_gln.
lwa_request-transfer_batch_service-authgln = lv_auth_gln.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form TRANSFER_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM transfer_cancel_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE ztransfer_cancel_request.
DATA: lwa_request
lwa_product_line
lv_gtin_formatted

TYPE ztransfer_cancel_request,
TYPE ztransfer_cancel_request_prod1,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_to_gln
TYPE zmm_br_gln,
lv_auth_gln

TYPE zmm_br_gln.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_to_gln = <fs_header>-to_gln.
lv_auth_gln = <fs_header>-frm_gln.
ENDIF.
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.

Code

15

PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin

= lv_gtin_formatted.

lwa_product_line-quantity = lv_quantity_formatted.
lwa_product_line-bn
lwa_product_line-xd

= lv_batch_formatted.
= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-transfer_cancel-productlist-product.
ENDLOOP.
lwa_request-transfer_cancel-togln = lv_to_gln.
lwa_request-transfer_cancel-authgln = lv_auth_gln.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form

CONSUME_REQUEST

*&---------------------------------------------------------------------*
FORM consume_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zconsume_service_request.
DATA: lwa_request
lwa_product_line
lv_gtin_formatted

TYPE zconsume_service_request,
TYPE zconsume_service_request_prod1,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_auth_gln
TYPE zmm_br_gln.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_auth_gln = <fs_header>-frm_gln.
ENDIF.
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.

Code

16

CLEAR lwa_product_line.
lwa_product_line-gtin = lv_gtin_formatted.
lwa_product_line-sn = <fs_item>-sr_number.
lwa_product_line-bn
= lv_batch_formatted.
lwa_product_line-xd

= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-consume_service-productlist-product.
ENDLOOP.
lwa_request-consume_service-authgln = lv_auth_gln.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form CONSUME_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM consume_cancel_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zconsume_cancel_request.
DATA: lwa_request

TYPE zconsume_cancel_request,

lwa_product_line
lv_gtin_formatted

TYPE zconsume_cancel_request_produ1,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_auth_gln
TYPE zmm_br_gln.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>
TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_auth_gln = <fs_header>-to_gln.
ENDIF.
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin = lv_gtin_formatted.
lwa_product_line-sn = <fs_item>-sr_number.
lwa_product_line-bn

Code

= lv_batch_formatted.

17

lwa_product_line-xd

= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-consume_cancel-productlist-product.
ENDLOOP.
lwa_request-consume_cancel-authgln = lv_auth_gln.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form PHARMACY_SALE_REQUEST
*&---------------------------------------------------------------------*
FORM pharmacy_sale_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zpharmacy_sale_request.
DATA: lwa_request
lwa_product_line
lv_gtin_formatted

TYPE zpharmacy_sale_request,
TYPE zpharmacy_sale_request_produc1,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_to_gln
lv_auth_gln

TYPE zmm_br_gln,
TYPE zmm_br_gln,

lv_prescription_date
lv_year(4)

TYPE string,
TYPE c,

lv_month(2)
lv_day(2)

TYPE c,
TYPE c.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>
TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_to_gln = <fs_header>-to_gln.
lv_auth_gln = <fs_header>-frm_gln.
ENDIF.
" Format current date as YYYY-MM-DD for prescription date
lv_year = sy-datum+0(4).
lv_month = sy-datum+4(2).
lv_day
= sy-datum+6(2).
lv_prescription_date = |{ lv_year }-{ lv_month }-{ lv_day }|.
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date

Code

18

CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin = lv_gtin_formatted.
lwa_product_line-sn = <fs_item>-sr_number.
lwa_product_line-bn
= lv_batch_formatted.
lwa_product_line-xd

= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-pharmacy_sale-productlist-product.
ENDLOOP.
" Check if toGLN = authGLN (invalid destination)
IF lv_to_gln = lv_auth_gln.
lwa_request-pharmacy_sale-togln = '0000000000000'.
ELSEIF lv_to_gln IS NOT INITIAL.
lwa_request-pharmacy_sale-togln = lv_to_gln.
ELSE.
lwa_request-pharmacy_sale-togln = '0000000000000'.
ENDIF.
lwa_request-pharmacy_sale-authgln = lv_auth_gln.
lwa_request-pharmacy_sale-doctorid = 'NA'.
lwa_request-pharmacy_sale-patientnationalid = 'NA'.
lwa_request-pharmacy_sale-prescriptionid = 'NA'.
lwa_request-pharmacy_sale-prescriptiondate = lv_prescription_date.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form PHARMACY_SALE_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM pharmacy_sale_cancel_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zpharmacy_sale_cancel_reques
t3.
DATA: lwa_request
lwa_product_line
lv_gtin_formatted

TYPE zpharmacy_sale_cancel_request3,
TYPE zpharmacy_sale_cancel_request2,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_to_gln
TYPE zmm_br_gln,
lv_auth_gln

TYPE zmm_br_gln.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.

Code

19

lv_to_gln = <fs_header>-to_gln.
lv_auth_gln = <fs_header>-to_gln.
ENDIF.
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin = lv_gtin_formatted.
lwa_product_line-sn = <fs_item>-sr_number.
lwa_product_line-bn
lwa_product_line-xd

= lv_batch_formatted.
= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-pharmacy_sale_cancel-productlist-product.
ENDLOOP.
" Check if toGLN = authGLN (invalid destination)
IF lv_to_gln = lv_auth_gln.
lwa_request-pharmacy_sale_cancel-togln = '0000000000000'.
ELSEIF lv_to_gln IS NOT INITIAL.
lwa_request-pharmacy_sale_cancel-togln = lv_to_gln.
ELSE.
lwa_request-pharmacy_sale_cancel-togln = '0000000000000'.
ENDIF.
lwa_request-pharmacy_sale_cancel-authgln = lv_auth_gln.
lwa_request-pharmacy_sale_cancel-prescriptionid = 'NA'.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form DEACTIVATE_REQUEST
*&---------------------------------------------------------------------*
FORM deactivate_request USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zdeactivation_service_request3.
DATA: lwa_request
lwa_product_line
lv_gtin_formatted

TYPE zdeactivation_service_request3,
TYPE zdeactivation_service_request1,
TYPE string,

lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_auth_gln
TYPE zmm_br_gln,
lv_grund

Code

TYPE mb_grbew,

20

lv_grund_desc

TYPE grtxt.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>
<fs_mseg>

TYPE zmm_sst_dtts_itm,
TYPE matdoc.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_auth_gln = <fs_header>-frm_gln.
ENDIF.
READ TABLE p_mseg_table ASSIGNING <fs_mseg> INDEX 1.
IF sy-subrc = 0 AND <fs_mseg>-grund IS NOT INITIAL.
lv_grund = <fs_mseg>-grund.
" Get description from T157E table for English language
SELECT SINGLE grtxt FROM t157e WHERE spras = 'E'
AND bwart = @<fs_mseg>-bwart AND grund = @lv_grund

INTO @lv_grund_desc.

IF sy-subrc <> 0.
" Fallback if description not found
lv_grund_desc = 'Deactivation'.
ENDIF.
ELSE.
" Default values if GRUND is empty
lv_grund = '30'.
lv_grund_desc = 'Damaged Product'.
ENDIF.
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin = lv_gtin_formatted.
lwa_product_line-sn = <fs_item>-sr_number.
lwa_product_line-bn
= lv_batch_formatted.
lwa_product_line-xd

= lv_exp_date_formatted.

APPEND lwa_product_line TO lwa_request-deactivation_request-productlist-product.
ENDLOOP.
SHIFT lv_grund LEFT DELETING LEADING '0'.
lwa_request-deactivation_request-authgln = lv_auth_gln.
lwa_request-deactivation_request-dr = lv_grund.
lwa_request-deactivation_request-explanation = lv_grund_desc.
p_request = lwa_request.

Code

21

ENDFORM.
*&---------------------------------------------------------------------*
*& Form DEACTIVATE_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM deactivate_cancel_request

USING p_mseg_table TYPE table
p_header_table TYPE table
p_items_table TYPE table
CHANGING p_request TYPE zdeactivation_cancel_request.

DATA: lwa_request
lwa_product_line

TYPE zdeactivation_cancel_request,
TYPE zdeactivation_cancel_request_1,

lv_gtin_formatted
TYPE string,
lv_quantity_formatted TYPE string,
lv_batch_formatted
TYPE string,
lv_exp_date_formatted TYPE string,
lv_auth_gln

TYPE zmm_br_gln.

FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
IF sy-subrc = 0.
lv_auth_gln = <fs_header>-to_gln.
ENDIF.
LOOP AT p_items_table ASSIGNING <fs_item>.
**********SKip unregistered materials***************
IF <fs_item>-prod_stat EQ 'SUCCESS'.
CONTINUE.
ENDIF.
PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
<fs_item>-batch <fs_item>-exp_date
CHANGING lv_gtin_formatted lv_quantity_formatted
lv_batch_formatted lv_exp_date_formatted.
CLEAR lwa_product_line.
lwa_product_line-gtin = lv_gtin_formatted.
lwa_product_line-bn

= lv_batch_formatted.

lwa_product_line-sn = <fs_item>-sr_number.
lwa_product_line-xd
= lv_exp_date_formatted.
APPEND lwa_product_line TO lwa_request-deactivation_cancel-productlist-product.
ENDLOOP.
lwa_request-deactivation_cancel-authgln = lv_auth_gln.
p_request = lwa_request.
ENDFORM.
*&---------------------------------------------------------------------*
*& SECTION 3: RESPONSE PROCESSING FORMS
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*

Code

22

*&---------------------------------------------------------------------*
*& Form ACCEPT_RESPONSE
*&---------------------------------------------------------------------*
FORM accept_response USING p_response TYPE zaccept_service_response
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code

TYPE zaccept_service_response_prod1,
TYPE char5,

lv_description
TYPE char255,
lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-accept_batch_service_response-notificationid.
LOOP AT p_response-accept_batch_service_response-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin
AND <fs_item>-batch = lwa_product_resp-bn
AND <fs_item>-prod_qty = lwa_product_resp-quantity.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat

= lv_description.

<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
= sy-uname.
EXIT.
ENDIF.
ENDLOOP.
ENDLOOP.

Code

23

LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
= sy-uname.
ENDLOOP.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form RETURN_RESPONSE
*&---------------------------------------------------------------------*
FORM return_response USING p_response TYPE zreturn_batch_service_response
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code
lv_description

TYPE zreturn_batch_service_respons3,
TYPE char5,
TYPE char255,

lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-return_batch_service_response-notificationid.
LOOP AT p_response-return_batch_service_response-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin
AND <fs_item>-batch = lwa_product_resp-bn
AND <fs_item>-prod_qty = lwa_product_resp-quantity.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description

Code

24

USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat = lv_description.
<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
= sy-uname.
EXIT.
ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.

= sy-uname.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form DISPATCH_RESPONSE
*&---------------------------------------------------------------------*
FORM dispatch_response USING p_response TYPE zdispatch_batch_service_respo3
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code

TYPE zdispatch_batch_service_respo1,
TYPE char5,

lv_description
TYPE char255,
lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>
TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-dispatch_batch_service_respons-notificationid.
LOOP AT p_response-dispatch_batch_service_respons-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin

Code

25

AND <fs_item>-batch = lwa_product_resp-bn
AND <fs_item>-prod_qty = lwa_product_resp-quantity.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat

= lv_description.

<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
EXIT.

= sy-uname.

ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
= sy-uname.
ENDLOOP.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form DISPATCH_CANCEL_RESPONSE
*&---------------------------------------------------------------------*
FORM dispatch_cancel_response USING p_response TYPE zdispatch_cancel_response
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code
lv_description

TYPE zdispatch_cancel_response_pro1,
TYPE char5,
TYPE char255,

lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

Code

TYPE zmm_sst_dtts_itm.

26

lv_notification_id = p_response-dispatch_cancel_response-notificationid.
LOOP AT p_response-dispatch_cancel_response-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin
AND <fs_item>-batch = lwa_product_resp-bn
AND <fs_item>-prod_qty = lwa_product_resp-quantity.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat = lv_description.
<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
= sy-uname.
EXIT.
ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.

= sy-uname.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form TRANSFER_RESPONSE
*&---------------------------------------------------------------------*
FORM transfer_response USING p_response TYPE ztransfer_batch_service_respo3

Code

27

CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code

TYPE ztransfer_batch_service_respo2,
TYPE char5,

lv_description
TYPE char255,
lv_notification_id TYPE string,
lv_all_success

TYPE abap_bool VALUE abap_true.

DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-transfer_batch_service_respons-notificationid.
LOOP AT p_response-transfer_batch_service_respons-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin
AND <fs_item>-batch = lwa_product_resp-bn
AND <fs_item>-prod_qty = lwa_product_resp-quantity.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat

= lv_description.

<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
EXIT.

= sy-uname.

ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.

Code

28

ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.

= sy-uname.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form TRANSFER_CANCEL_RESPONSE
*&---------------------------------------------------------------------*
FORM transfer_cancel_response USING p_response TYPE ztransfer_cancel_response
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code

TYPE ztransfer_cancel_response_pro1,
TYPE char5,

lv_description
TYPE char255,
lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>
TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-transfer_cancel_response-notificationid.
LOOP AT p_response-transfer_cancel_response-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin
AND <fs_item>-batch = lwa_product_resp-bn
AND <fs_item>-prod_qty = lwa_product_resp-quantity.
<fs_item>-notif_id

= lv_notification_id.

<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat = lv_description.
<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.

Code

29

<fs_item>-changed_by

= sy-uname.

EXIT.
ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
= sy-uname.
ENDLOOP.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form CONSUME_RESPONSE
*&---------------------------------------------------------------------*
FORM consume_response USING p_response TYPE zconsume_service_response
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code
lv_description

TYPE zconsume_service_response_pro1,
TYPE char5,
TYPE char255,

lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>
TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-consume_service_response-notificationid.
LOOP AT p_response-consume_service_response-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs
_item>-sr_number = lwa_product_resp-sn.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.

Code

30

lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat = lv_description.
<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
= sy-uname.
EXIT.
ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.

= sy-uname.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form

CONSUME_CANCEL_RESPONSE

*&---------------------------------------------------------------------*
FORM consume_cancel_response USING p_response TYPE zconsume_cancel_response
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code

TYPE zconsume_cancel_response_prod1,
TYPE char5,

lv_description
TYPE char255,
lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>
TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-consume_cancel_service_respons-notificationid.
LOOP AT p_response-consume_cancel_service_respons-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.

Code

31

SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs
_item>-sr_number = lwa_product_resp-sn.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat = lv_description.
<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
= sy-uname.
EXIT.
ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.

= sy-uname.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form PHARMACY_SALE_RESPONSE
*&---------------------------------------------------------------------*
FORM pharmacy_sale_response USING p_response TYPE zpharmacy_sale_response
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code
lv_description

TYPE zpharmacy_sale_response_produ1,
TYPE char5,
TYPE char255,

lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

Code

TYPE zmm_sst_dtts_itm.

32

lv_notification_id = p_response-pharmacy_sale_service_response-notificationid.
LOOP AT p_response-pharmacy_sale_service_response-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs
_item>-sr_number = lwa_product_resp-sn.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat = lv_description.
<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
= sy-uname.
EXIT.
ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.

= sy-uname.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form PHARMACY_SALE_CANCEL_RESPONSE
*&---------------------------------------------------------------------*
FORM pharmacy_sale_cancel_response
USING p_response TYPE zpharmacy_sale_cancel_respons3

Code

33

CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code

TYPE zpharmacy_sale_cancel_respons2,
TYPE char5,

lv_description
TYPE char255,
lv_notification_id TYPE string,
lv_all_success

TYPE abap_bool VALUE abap_true.

DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>

TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-pharmacy_sale_cancel_response-notificationid.
LOOP AT p_response-pharmacy_sale_cancel_response-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs
_item>-sr_number = lwa_product_resp-sn.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat

= lv_description.

<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
EXIT.

= sy-uname.

ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.

Code

34

<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.

= sy-uname.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form

DEACTIVATE_RESPONSE

*&---------------------------------------------------------------------*
FORM deactivate_response USING p_response TYPE zdeactivation_service_respons3
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code
lv_description

TYPE zdeactivation_service_respons1,
TYPE char5,
TYPE char255,

lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>
TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-deactivation_response-notificationid.
LOOP AT p_response-deactivation_response-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs
_item>-sr_number = lwa_product_resp-sn.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.
lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat

= lv_description.

<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
EXIT.

= sy-uname.

ENDIF.

Code

35

ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.

= sy-uname.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form DEACTIVATE_CANCEL_RESPONSE
*&---------------------------------------------------------------------*
FORM deactivate_cancel_response USING p_response TYPE zdeactivation_cancel_response3
CHANGING p_header_table TYPE table
p_items_table TYPE table.
DATA: lwa_product_resp
lv_error_code

TYPE zdeactivation_cancel_response1,
TYPE char5,

lv_description
TYPE char255,
lv_notification_id TYPE string,
lv_all_success
TYPE abap_bool VALUE abap_true.
DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
<fs_item>
TYPE zmm_sst_dtts_itm.

lv_notification_id = p_response-deactivation_cancel_response-notificationid.
LOOP AT p_response-deactivation_cancel_response-productlist-product
INTO lwa_product_resp.
LOOP AT p_items_table ASSIGNING <fs_item>.
lv_item_gtin = <fs_item>-gtin.
lv_resp_gtin = lwa_product_resp-gtin.
SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.
IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs
_item>-sr_number = lwa_product_resp-sn.
<fs_item>-notif_id
= lv_notification_id.
<fs_item>-tr_response = lwa_product_resp-rc.
IF lwa_product_resp-rc = '00000'.
<fs_item>-prod_stat = 'SUCCESS'.
ELSE.
<fs_item>-prod_stat = 'ERROR'.
lv_all_success = abap_false.
ENDIF.

Code

36

lv_error_code = lwa_product_resp-rc.
PERFORM get_error_description
USING lv_error_code
CHANGING lv_description.
<fs_item>-trans_stat = lv_description.
<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
EXIT.

= sy-uname.

ENDIF.
ENDLOOP.
ENDLOOP.
LOOP AT p_header_table ASSIGNING <fs_header>.
IF lv_all_success = abap_true.
<fs_header>-status = 'SUCCESS'.
ELSE.
<fs_header>-status = 'ERROR'.
ENDIF.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by

= sy-uname.

ENDLOOP.
ENDFORM.
*&---------------------------------------------------------------------*
*& SECTION 4: EXCEPTION HANDLERS & SUPPORTING PERFORMS
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*& Form

HANDLE_DTTS_APPLICATION_FAULT

*&---------------------------------------------------------------------*
* Generic handler using config table fault attribute
FORM handle_dtts_application_fault USING p_exception TYPE REF TO cx_ai_application_fau
lt
p_operation TYPE char20
CHANGING p_items_table TYPE table
p_header_table TYPE table.
DATA: lv_response_code TYPE string,
lv_message

TYPE string.

FIELD-SYMBOLS: <fs_item>
TYPE zmm_sst_dtts_itm,
<fs_header> TYPE zmm_sst_dtts_hdr,
<fs_field>

TYPE any.

" ========== Extract Fault Details (Direct Access - Flat Structure) ==========
TRY.
" Try to access RESPONSE_CODE directly
ASSIGN p_exception->('RESPONSE_CODE') TO <fs_field>.
IF sy-subrc = 0 AND <fs_field> IS ASSIGNED.
lv_response_code = <fs_field>.
ENDIF.

Code

37

" Try to access MESSAGE directly
UNASSIGN <fs_field>.
ASSIGN p_exception->('MESSAGE') TO <fs_field>.
IF sy-subrc = 0 AND <fs_field> IS ASSIGNED.
lv_message = <fs_field>.
ENDIF.
CATCH cx_root.
" Continue to fallback
ENDTRY.
" ========== Fallback if extraction failed ==========
IF lv_response_code IS INITIAL.
lv_response_code = 'APP_FAULT'.
ENDIF.
IF lv_message IS INITIAL.
lv_message = p_exception->get_text( ).
IF lv_message IS INITIAL.
lv_message = |DTTS Application Fault - Operation: { p_operation }|.
ENDIF.
ENDIF.
" ========== Update ALL Items with Fault Details ==========
LOOP AT p_items_table ASSIGNING <fs_item>.
<fs_item>-tr_response = lv_response_code.
<fs_item>-trans_stat = lv_message.
<fs_item>-prod_stat
<fs_item>-notif_id

= 'ERROR'.
= ''.

" Update item timestamp
<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
= sy-uname.
ENDLOOP.
" Update headers with timestamp and STATUS
LOOP AT p_header_table ASSIGNING <fs_header>.
<fs_header>-status = 'ERROR'.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.

= sy-uname.

" Save to database
IF p_items_table IS NOT INITIAL.
MODIFY zmm_sst_dtts_itm FROM TABLE p_items_table.
ENDIF.
IF p_header_table IS NOT INITIAL.
MODIFY zmm_sst_dtts_hdr FROM TABLE p_header_table.
ENDIF.

Code

38

ENDFORM.

*&---------------------------------------------------------------------*
*& Form HANDLE_API_ERROR_MULTIPLE
*&---------------------------------------------------------------------*
FORM handle_api_error_multiple USING p_exception TYPE REF TO cx_ai_system_fault
CHANGING p_items_table TYPE table
p_header_table TYPE table.
DATA: lv_sys_error

TYPE string,

lv_mpl_id
TYPE string,
lv_error_code TYPE string.
FIELD-SYMBOLS: <fs_item>

TYPE zmm_sst_dtts_itm,

<fs_header> TYPE zmm_sst_dtts_hdr.
" Get error message
lv_sys_error = p_exception->get_text( ).
" Extract MPL ID if available
IF lv_sys_error CS 'MPL ID'.
FIND REGEX 'MPL ID ([A-Za-z0-9_]+)' IN lv_sys_error
SUBMATCHES lv_mpl_id.
ENDIF.
" Extract DTTS error code if available (e.g., 98765)
IF lv_sys_error CS '<FC>'.
FIND REGEX '<FC>(\d+)</FC>' IN lv_sys_error
SUBMATCHES lv_error_code.
ENDIF.
" Update ALL items with error code
LOOP AT p_items_table ASSIGNING <fs_item>.
<fs_item>-tr_response = lv_error_code.
<fs_item>-prod_stat = 'ERROR'.
<fs_item>-trans_stat = lv_sys_error.
" Update item timestamp
<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
= sy-uname.
ENDLOOP.
" Update headers
LOOP AT p_header_table ASSIGNING <fs_header>.
<fs_header>-status = 'ERROR'.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
ENDLOOP.
" Save

= sy-uname.

error records to database

MODIFY zmm_sst_dtts_itm FROM TABLE p_items_table.
MODIFY zmm_sst_dtts_hdr FROM TABLE p_header_table.

Code

39

ENDFORM.
*&---------------------------------------------------------------------*
*& Form HANDLE_GENERIC_ERROR_MULTIPLE
*&---------------------------------------------------------------------*
FORM handle_generic_error_multiple USING p_exception TYPE REF TO cx_root
CHANGING p_items_table TYPE table
p_header_table TYPE table.

DATA: lv_root_error TYPE string.
FIELD-SYMBOLS: <fs_item>
TYPE zmm_sst_dtts_itm,
<fs_header> TYPE zmm_sst_dtts_hdr.
" Get error message
lv_root_error = p_exception->get_text( ).
" Update ALL items with generic error
LOOP AT p_items_table ASSIGNING <fs_item>.
<fs_item>-tr_response = 'ERROR'.
<fs_item>-prod_stat = 'ERROR'.
"

Update item timestamp

<fs_item>-changed_date = sy-datum.
<fs_item>-changed_time = sy-uzeit.
<fs_item>-changed_by
ENDLOOP.

= sy-uname.

" Update headers
LOOP AT p_header_table ASSIGNING <fs_header>.
<fs_header>-status = 'ERROR'.
<fs_header>-changed_date = sy-datum.
<fs_header>-changed_time = sy-uzeit.
<fs_header>-changed_by
= sy-uname.
ENDLOOP.
" Save ALL records
MODIFY zmm_sst_dtts_itm FROM TABLE p_items_table.
MODIFY zmm_sst_dtts_hdr FROM TABLE p_header_table.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form FORMAT_DATA
*&---------------------------------------------------------------------*
FORM format_data USING p_gtin_in TYPE any
p_quantity_in TYPE any
p_batch_in TYPE any
p_exp_date_in TYPE any
CHANGING p_gtin_out TYPE string
p_quantity_out TYPE string
p_batch_out TYPE string
p_exp_date_out TYPE string.

Code

40

DATA: lv_len
lv_qty_int
lv_qty_dec

TYPE i,
TYPE string,
TYPE string,

lv_year(4) TYPE c,
lv_month(2) TYPE c,
lv_day(2)

TYPE c.

" Format GTIN
p_gtin_out = p_gtin_in.
CONDENSE p_gtin_out NO-GAPS.
lv_len = strlen( p_gtin_out ).
IF lv_len < 14.
p_gtin_out = |{ p_gtin_out WIDTH = 14 PAD = '0' ALIGN = RIGHT }|.
ENDIF.
" Format Quantity
p_quantity_out = p_quantity_in.
IF p_quantity_out CS '.'.
SPLIT p_quantity_out AT '.' INTO lv_qty_int lv_qty_dec.
p_quantity_out = lv_qty_int.
ENDIF.
p_quantity_out = |{ p_quantity_out ALPHA = OUT }|.
CONDENSE p_quantity_out NO-GAPS.
" Format Batch
p_batch_out = p_batch_in.
CONDENSE p_batch_out NO-GAPS.
" Format Expiry Date
CLEAR p_exp_date_out.
IF p_exp_date_in IS NOT INITIAL.
lv_year = p_exp_date_in+0(4).
lv_month = p_exp_date_in+4(2).
lv_day
= p_exp_date_in+6(2).
p_exp_date_out = |{ lv_year }-{ lv_month }-{ lv_day }|.
ENDIF.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form

GET_ERROR_DESCRIPTION

*&---------------------------------------------------------------------*
FORM get_error_description USING p_error_code TYPE char5
CHANGING p_description TYPE char255.
CLEAR p_description.
SELECT SINGLE description FROM zdtts_errorlist INTO @p_description
WHERE error_code = @p_error_code
AND language = 'en'.
IF sy-subrc <> 0.
p_description = |Error Code: { p_error_code }|.
ENDIF.
ENDFORM.

Code

41

