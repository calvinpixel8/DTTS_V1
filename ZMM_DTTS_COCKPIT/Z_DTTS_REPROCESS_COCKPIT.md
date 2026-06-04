# Z_DTTS_REPROCESS_COCKPIT — ABAP Report

## Overview

This report implements a reprocessing cockpit for DTTS (Drug Track and Trace System) transactions. It displays failed or errored material document items in an ALV grid and allows users to reprocess them by calling the appropriate DTTS web service dynamically based on API configuration.

---

## Report Header

```abap
*&---------------------------------------------------------------------*
*& Report Z_DTTS_REPROCESS_COCKPIT
*&---------------------------------------------------------------------*
REPORT Z_DTTS_REPROCESS_COCKPIT.

TABLES: mseg.
```

---

## Global Data Declarations

```abap
DATA: request_ptr         TYPE REF TO data,          "Dynamic request structure pointer
      response_ptr        TYPE REF TO data,          "Dynamic response structure pointer
      lo_proxy            TYPE REF TO object,         "Web service proxy object
      p_lport             TYPE prx_logical_port_name, "Logical port name for proxy
      ptab                TYPE abap_parmbind_tab,     "Parameter binding table for proxy
      wa_ptab             TYPE abap_parmbind,         "Single parameter binding entry
      wa_zmm_dtts_api_con TYPE zmm_dtts_api_con.      "API config row (proxy class, method etc.)
```

---

## Type Definitions

```abap
TYPES: BEGIN OF ty_alv_data,
         selkz            TYPE char1,
         tran_id          TYPE n LENGTH 20,
         item_no          TYPE numc4,
         zeile            TYPE mblpo,
         product          TYPE matnr,
         prod_name        TYPE maktx,
         prod_qty         TYPE menge_d,
         prod_unit        TYPE meins,
         gtin             TYPE z_dgtin,
         batch            TYPE charg_d,
         exp_date         TYPE vfdat,
         notif_id         TYPE char50,
         tr_response      TYPE string,
         mat_doc          TYPE mblnr,
         mvt_type         TYPE bwart,
         sr_number        TYPE char50,
         created_date     TYPE dats,
         created_time     TYPE tims,
         created_by       TYPE xubname,
         changed_date     TYPE dats,
         changed_time     TYPE tims,
         changed_by       TYPE xubname,
         prod_stat        TYPE char10,
         trans_stat       TYPE char10,
         doc_year         TYPE mjahr,
         item_operation   TYPE char20,
         header_operation TYPE char20,
         frm_gln          TYPE zmm_sst_gln_src,
         to_gln           TYPE zmm_sst_gln_des,
         auth_gln         TYPE zmm_sst_gln_auth,
       END OF ty_alv_data.

DATA: gt_alv_data TYPE TABLE OF ty_alv_data.
```

---

## Selection Screen

```abap
SELECTION-SCREEN BEGIN OF BLOCK b1 WITH FRAME TITLE TEXT-001.
  SELECT-OPTIONS: s_matdoc FOR mseg-mblnr,
                  s_year   FOR mseg-mjahr,
                  s_bwart  FOR mseg-bwart.
  PARAMETERS: p_oper TYPE char20.
SELECTION-SCREEN END OF BLOCK b1.
```

---

## Local Class Definition

```abap
CLASS lcl_dtts_cockpit DEFINITION.
  PUBLIC SECTION.
    TYPES: BEGIN OF ty_alv_data,
             selkz            TYPE char1,
             tran_id          TYPE ztran_id,
             item_no          TYPE numc4,
             zeile            TYPE mblpo,
             product          TYPE matnr,
             prod_name        TYPE maktx,
             prod_qty         TYPE menge_d,
             prod_unit        TYPE meins,
             gtin             TYPE z_dgtin,
             batch            TYPE charg_d,
             exp_date         TYPE vfdat,
             notif_id         TYPE char50,
             tr_response      TYPE string,
             mat_doc          TYPE mblnr,
             mvt_type         TYPE bwart,
             sr_number        TYPE char50,
             created_date     TYPE dats,
             created_time     TYPE tims,
             created_by       TYPE xubname,
             changed_date     TYPE dats,
             changed_time     TYPE tims,
             changed_by       TYPE xubname,
             prod_stat        TYPE char10,
             trans_stat       TYPE char10,
             doc_year         TYPE mjahr,
             item_operation   TYPE char20,
             header_operation TYPE char20,
             frm_gln          TYPE zmm_sst_gln_src,
             to_gln           TYPE zmm_sst_gln_des,
             auth_gln         TYPE zmm_sst_gln_auth,
           END OF ty_alv_data.

    DATA: gt_alv_data  TYPE TABLE OF ty_alv_data,
          go_alv       TYPE REF TO cl_gui_alv_grid,
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
```

---

## Local Class Implementation

### METHOD get_data

Retrieves data from `ZIMMDTTS_4` (view: `ZIMM_DTTS_FY_HELPER` LEFT OUTER JOIN `zmm_sst_dtts_hdr`) based on selection screen criteria.

```abap
METHOD get_data.
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
         hdr~auth_gln
    FROM zimmdtts_4 AS itm
    LEFT OUTER JOIN zmm_sst_dtts_hdr AS hdr
      ON  itm~mat_doc  = hdr~mat_doc
      AND itm~doc_year = hdr~doc_yr
      AND itm~mvt_type = hdr~mvt_type
   WHERE itm~mat_doc  IN @s_matdoc
     AND itm~doc_year IN @s_year
     AND itm~mvt_type IN @s_bwart
    INTO CORRESPONDING FIELDS OF TABLE @gt_alv_data.

  IF sy-subrc <> 0.
    MESSAGE 'No data found for the given selection criteria.' TYPE 'S' DISPLAY LIKE 'E'.
  ENDIF.
ENDMETHOD.
```

---

### METHOD display_alv

Initializes the ALV grid with layout settings, field catalog, and event handlers.

```abap
METHOD display_alv.
  DATA: lt_fcat   TYPE lvc_t_fcat,
        ls_layout TYPE lvc_s_layo.

  IF go_container IS INITIAL.
    CREATE OBJECT go_container
      EXPORTING
        container_name = 'CC_ALV'.

    CREATE OBJECT go_alv
      EXPORTING
        i_parent = go_container.

    ls_layout-sel_mode = 'A'.
    ls_layout-box_fname = 'SELKZ'.

    CALL FUNCTION 'LVC_FIELDCATALOG_MERGE'
      EXPORTING
        i_structure_name = 'ZIMM_DTTS_FY_HELPER'
      CHANGING
        ct_fieldcat      = lt_fcat
      EXCEPTIONS
        OTHERS           = 1.

    DATA ls_fcat LIKE LINE OF lt_fcat.
    CLEAR ls_fcat.
    ls_fcat-fieldname = 'SELKZ'.
    ls_fcat-checkbox  = 'X'.
    ls_fcat-edit      = 'X'.
    APPEND ls_fcat TO lt_fcat.

    LOOP AT lt_fcat ASSIGNING FIELD-SYMBOL(<fs_fcat>).
      <fs_fcat>-edit = 'X'.
    ENDLOOP.

    SET HANDLER me->handle_toolbar      FOR go_alv.
    SET HANDLER me->handle_user_command FOR go_alv.

    go_alv->set_table_for_first_display(
      EXPORTING
        is_layout      = ls_layout
      CHANGING
        it_outtab      = gt_alv_data
        it_fieldcatalog = lt_fcat ).
  ELSE.
    go_alv->refresh_table_display( ).
  ENDIF.
ENDMETHOD.
```

---

### METHOD handle_toolbar

Adds a custom **Reprocess** button to the ALV toolbar.

```abap
METHOD handle_toolbar.
  DATA: ls_toolbar TYPE stb_button.

  CLEAR ls_toolbar.
  ls_toolbar-function  = 'REPROCESS'.
  ls_toolbar-icon      = '@5C@'.
  ls_toolbar-quickinfo = 'Reprocess Selected Items'.
  ls_toolbar-butn_type = 0.
  ls_toolbar-text      = 'Reprocess'.
  APPEND ls_toolbar TO e_object->mt_toolbar.
ENDMETHOD.
```

---

### METHOD handle_user_command

Handles the `REPROCESS` toolbar action.

```abap
METHOD handle_user_command.
  CASE e_ucomm.
    WHEN 'REPROCESS'.
      go_alv->check_changed_data( ).
      me->reprocess_selected_items( ).
  ENDCASE.
ENDMETHOD.
```

---

### METHOD reprocess_selected_items

Core reprocessing logic. Steps:

1. Extract checked rows (`selkz = 'X'`)
2. Remove items with `prod_stat = 'SUCCESS'`
3. Sort by `mat_doc`, `doc_year`, `mvt_type`
4. Deduplicate to get unique document keys
5. For each unique key, load header/items and call DTTS web service dynamically

```abap
METHOD reprocess_selected_items.
  DATA: lt_selected         TYPE TABLE OF ty_alv_data,
        lt_unique           TYPE TABLE OF ty_alv_data,
        lt_header           TYPE TABLE OF zmm_sst_dtts_hdr,
        lt_items            TYPE TABLE OF zmm_sst_dtts_itm,
        lt_mseg             TYPE TABLE OF mseg,
        wa_zmm_dtts_api_con TYPE zmm_dtts_api_con,
        ptab                TYPE abap_parmbind_tab,
        wa_ptab             LIKE LINE OF ptab,
        p_lport             TYPE prx_logical_port_name,
        lo_proxy            TYPE REF TO object.

  " 1. Extract selected lines
  LOOP AT gt_alv_data INTO DATA(ls_alv) WHERE selkz = 'X'.
    APPEND ls_alv TO lt_selected.
  ENDLOOP.

  IF lt_selected IS INITIAL.
    MESSAGE 'Please select at least one item to reprocess.' TYPE 'I'.
    RETURN.
  ENDIF.

  " 2. Remove SUCCESS items
  DELETE lt_selected WHERE prod_stat = 'SUCCESS'.

  IF lt_selected IS INITIAL.
    MESSAGE 'No eligible items to reprocess (all selected were SUCCESS).' TYPE 'I'.
    RETURN.
  ENDIF.

  " 3. Sort and deduplicate
  SORT lt_selected BY mat_doc doc_year mvt_type.
  lt_unique = lt_selected.
  DELETE ADJACENT DUPLICATES FROM lt_unique COMPARING mat_doc doc_year mvt_type.

  " 4. Loop unique documents
  LOOP AT lt_unique INTO DATA(ls_unique).
    CLEAR: lt_header, lt_items.

    SELECT * FROM zmm_sst_dtts_hdr
      INTO TABLE @DATA(lt_hdr_tmp)
      WHERE mat_doc  = @ls_unique-mat_doc
        AND doc_yr   = @ls_unique-doc_year
        AND mvt_type = @ls_unique-mvt_type.
    APPEND LINES OF lt_hdr_tmp TO lt_header.

    DATA(lv_operation) = ls_unique-header_operation.

    LOOP AT lt_selected INTO DATA(ls_sel_item)
         WHERE mat_doc  = ls_unique-mat_doc
           AND doc_year = ls_unique-doc_year
           AND mvt_type = ls_unique-mvt_type.
      DATA: ls_item TYPE zmm_sst_dtts_itm.
      MOVE-CORRESPONDING ls_sel_item TO ls_item.
      APPEND ls_item TO lt_items.
    ENDLOOP.

    " Load API config
    SELECT SINGLE * FROM zmm_dtts_api_con INTO @wa_zmm_dtts_api_con
      WHERE api_name = @lv_operation.

    IF sy-subrc = 0.
      CREATE DATA request_ptr  TYPE (wa_zmm_dtts_api_con-request_structure).
      ASSIGN request_ptr->*  TO FIELD-SYMBOL(<fs_request>).
      CREATE DATA response_ptr TYPE (wa_zmm_dtts_api_con-response_structure).
      ASSIGN response_ptr->* TO FIELD-SYMBOL(<fs_response>).

      " Build request by operation type
      CASE lv_operation.
        WHEN 'ACCEPT'.
          PERFORM accept_request          USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'RETURN'.
          PERFORM return_request          USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'DISPATCH'.
          PERFORM dispatch_request        USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'DISPATCH_CANCEL'.
          PERFORM dispatch_cancel_request USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'TRANSFER'.
          PERFORM transfer_request        USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'TRANSFER_CANCEL'.
          PERFORM transfer_cancel_request USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'CONSUME'.
          PERFORM consume_request         USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'CONSUME_CANCEL'.
          PERFORM consume_cancel_request  USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'DRUG_SALE'.
          PERFORM pharmacy_sale_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'DRUG_SALE_CANCEL'.
          PERFORM pharmacy_sale_cancel_request USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'DEACTIVATE'.
          PERFORM deactivate_request      USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        WHEN 'DEACTIVATE_CANCEL'.
          PERFORM deactivate_cancel_request USING lt_mseg lt_header lt_items CHANGING <fs_request>.
      ENDCASE.

      " Create proxy and call web service
      CLEAR ptab.
      CLEAR wa_ptab.
      wa_ptab-name  = 'LOGICAL_PORT_NAME'.
      wa_ptab-kind  = cl_abap_objectdescr=>exporting.
      p_lport       = wa_zmm_dtts_api_con-logical_port.
      wa_ptab-value = REF #( p_lport ).
      INSERT wa_ptab INTO TABLE ptab.

      TRY.
        CREATE OBJECT lo_proxy TYPE (wa_zmm_dtts_api_con-proxy_class)
          PARAMETER-TABLE ptab.

        CALL METHOD lo_proxy->(wa_zmm_dtts_api_con-method_name)
          EXPORTING input  = <fs_request>
          IMPORTING output = <fs_response>.

        " Process response by operation type
        CASE lv_operation.
          WHEN 'ACCEPT'.
            PERFORM accept_response          USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'RETURN'.
            PERFORM return_response          USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'DISPATCH'.
            PERFORM dispatch_response        USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'DISPATCH_CANCEL'.
            PERFORM dispatch_cancel_response USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'TRANSFER'.
            PERFORM transfer_response        USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'TRANSFER_CANCEL'.
            PERFORM transfer_cancel_response USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'CONSUME'.
            PERFORM consume_response         USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'CONSUME_CANCEL'.
            PERFORM consume_cancel_response  USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'DRUG_SALE'.
            PERFORM pharmacy_sale_response   USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'DRUG_SALE_CANCEL'.
            PERFORM pharmacy_sale_cancel_response USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'DEACTIVATE'.
            PERFORM deactivate_response      USING <fs_response> CHANGING lt_header lt_items.
          WHEN 'DEACTIVATE_CANCEL'.
            PERFORM deactivate_cancel_response USING <fs_response> CHANGING lt_header lt_items.
        ENDCASE.

        " Update header table
        IF lt_header IS NOT INITIAL.
          MODIFY zmm_sst_dtts_hdr FROM TABLE lt_header.
        ENDIF.

        " Update or insert item records into ZMM_SST_DTTSIT2
        LOOP AT lt_items INTO DATA(ls_new_item).
          DATA: ls_dttsit2 TYPE zmm_sst_dttsit2.
          SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @ls_dttsit2
            WHERE tran_id = @ls_new_item-tran_id
              AND item_no = @ls_new_item-item_no.

          IF sy-subrc = 0.
            ls_dttsit2-prod_stat  = ls_new_item-prod_stat.
            ls_dttsit2-trans_stat = ls_new_item-trans_stat.
            MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
          ELSE.
            MOVE-CORRESPONDING ls_new_item TO ls_dttsit2.
            INSERT zmm_sst_dttsit2 FROM ls_dttsit2.
          ENDIF.
        ENDLOOP.

        CATCH cx_ai_application_fault INTO DATA(lx_app_fault).
          PERFORM handle_dtts_application_fault
            USING lx_app_fault lv_operation CHANGING lt_items lt_header.
        CATCH cx_ai_system_fault INTO DATA(lx_sys).
          PERFORM handle_api_error_multiple
            USING lx_sys CHANGING lt_items lt_header.
        CATCH cx_root INTO DATA(lx_root).
          PERFORM handle_generic_error_multiple
            USING lx_root CHANGING lt_items lt_header.
      ENDTRY.
    ENDIF.
  ENDLOOP.

  MESSAGE 'Reprocessing Completed.' TYPE 'S'.
ENDMETHOD.

ENDCLASS.
```

---

## Main Program Execution

```abap
DATA: go_main TYPE REF TO lcl_dtts_cockpit.

START-OF-SELECTION.
  CREATE OBJECT go_main.
  go_main->get_data( ).
  CALL SCREEN 0100.

MODULE status_0100 OUTPUT.
  SET PF-STATUS 'STANDARD'.
  go_main->display_alv( ).
ENDMODULE.

MODULE user_command_0100 INPUT.
  CASE sy-ucomm.
    WHEN 'BACK' OR 'EXIT' OR 'CANC'.
      LEAVE TO SCREEN 0.
  ENDCASE.
ENDMODULE.
```

---

## Section 2: Request Preparation FORMs

### FORM accept_request

```abap
FORM accept_request USING p_mseg_table   TYPE table
                          p_header_table TYPE table
                          p_items_table  TYPE table
                  CHANGING p_request     TYPE zaccept_service_request.

  DATA: lwa_request        TYPE zaccept_service_request,
        lwa_product_line   TYPE zaccept_service_request_produ1,
        lv_gtin_formatted  TYPE string,
        lv_qty_formatted   TYPE string,
        lv_batch_formatted TYPE string,
        lv_exp_formatted   TYPE string,
        lv_from_gln        TYPE zmm_br_gln,
        lv_auth_gln        TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.

  READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
  IF sy-subrc = 0.
    lv_from_gln = <fs_header>-frm_gln.
    lv_auth_gln = <fs_header>-to_gln.
  ENDIF.

  LOOP AT p_items_table ASSIGNING <fs_item>.
    IF <fs_item>-prod_stat EQ 'SUCCESS'. CONTINUE. ENDIF.

    PERFORM format_data USING    <fs_item>-gtin <fs_item>-prod_qty
                                 <fs_item>-batch <fs_item>-exp_date
                        CHANGING lv_gtin_formatted lv_qty_formatted
                                 lv_batch_formatted lv_exp_formatted.

    CLEAR lwa_product_line.
    lwa_product_line-gtin     = lv_gtin_formatted.
    lwa_product_line-quantity = lv_qty_formatted.
    lwa_product_line-bn       = lv_batch_formatted.
    lwa_product_line-xd       = lv_exp_formatted.
    APPEND lwa_product_line TO
      lwa_request-accept_batch_service_request-productlist-product.
  ENDLOOP.

  lwa_request-accept_batch_service_request-fromgln = lv_from_gln.
  lwa_request-accept_batch_service_request-authgln = lv_auth_gln.
  p_request = lwa_request.
ENDFORM.
```

> **Note:** All other request FORMs (`return_request`, `dispatch_request`, `dispatch_cancel_request`, `transfer_request`, `transfer_cancel_request`, `consume_request`, `consume_cancel_request`, `pharmacy_sale_request`, `pharmacy_sale_cancel_request`, `deactivate_request`, `deactivate_cancel_request`) follow the same pattern:
> - Read header for GLN values
> - Loop items, skip `SUCCESS`, call `format_data`, build product line, append to request structure
> - Set GLN and other header fields on request

Special handling in `pharmacy_sale_request`: formats `sy-datum` as `YYYY-MM-DD` for `prescriptiondate`; sets `doctorid`, `patientnationalid`, `prescriptionid` to `'NA'`; sets `togln` to `'0000000000000'` if equal to `authgln` or initial.

Special handling in `deactivate_request`: reads `grund` from MSEG, looks up description from `T157E` for language `'E'`; defaults to reason `'30'` / `'Damaged Product'` if empty.

---

## Section 3: Response Processing FORMs

All response FORMs share a common pattern:

```abap
" Common response processing pattern
lv_notification_id = p_response-<service_response>-notificationid.

LOOP AT p_response-<service_response>-productlist-product INTO lwa_product_resp.
  LOOP AT p_items_table ASSIGNING <fs_item>.
    " Strip leading zeros from GTIN for comparison
    lv_item_gtin = <fs_item>-gtin.
    lv_resp_gtin = lwa_product_resp-gtin.
    SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
    SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

    IF lv_item_gtin = lv_resp_gtin
   AND <fs_item>-batch    = lwa_product_resp-bn
   AND <fs_item>-prod_qty = lwa_product_resp-quantity.  " (or sr_number for serial-tracked ops)
      <fs_item>-notif_id     = lv_notification_id.
      <fs_item>-tr_response  = lwa_product_resp-rc.
      IF lwa_product_resp-rc = '00000'.
        <fs_item>-prod_stat = 'SUCCESS'.
      ELSE.
        <fs_item>-prod_stat  = 'ERROR'.
        lv_all_success       = abap_false.
      ENDIF.
      PERFORM get_error_description USING lwa_product_resp-rc CHANGING lv_description.
      <fs_item>-trans_stat   = lv_description.
      <fs_item>-changed_date = sy-datum.
      <fs_item>-changed_time = sy-uzeit.
      <fs_item>-changed_by   = sy-uname.
      EXIT.
    ENDIF.
  ENDLOOP.
ENDLOOP.

LOOP AT p_header_table ASSIGNING <fs_header>.
  <fs_header>-status       = COND #( WHEN lv_all_success = abap_true THEN 'SUCCESS' ELSE 'ERROR' ).
  <fs_header>-changed_date = sy-datum.
  <fs_header>-changed_time = sy-uzeit.
  <fs_header>-changed_by   = sy-uname.
ENDLOOP.
```

> Item matching for serial-tracked operations (`CONSUME`, `CONSUME_CANCEL`, `DRUG_SALE`, `DRUG_SALE_CANCEL`, `DEACTIVATE`, `DEACTIVATE_CANCEL`) uses `sr_number` instead of `prod_qty`.

---

## Section 4: Exception Handlers & Supporting FORMs

### FORM handle_dtts_application_fault

```abap
FORM handle_dtts_application_fault
  USING    p_exception TYPE REF TO cx_ai_application_fault
           p_operation TYPE char20
  CHANGING p_items_table  TYPE table
           p_header_table TYPE table.

  DATA: lv_response_code TYPE string,
        lv_message       TYPE string.
  FIELD-SYMBOLS: <fs_item>   TYPE zmm_sst_dtts_itm,
                 <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_field>  TYPE any.

  TRY.
    ASSIGN p_exception->('RESPONSE_CODE') TO <fs_field>.
    IF sy-subrc = 0 AND <fs_field> IS ASSIGNED. lv_response_code = <fs_field>. ENDIF.
    UNASSIGN <fs_field>.
    ASSIGN p_exception->('MESSAGE') TO <fs_field>.
    IF sy-subrc = 0 AND <fs_field> IS ASSIGNED. lv_message = <fs_field>. ENDIF.
    CATCH cx_root.
  ENDTRY.

  IF lv_response_code IS INITIAL. lv_response_code = 'APP_FAULT'. ENDIF.
  IF lv_message IS INITIAL.
    lv_message = p_exception->get_text( ).
    IF lv_message IS INITIAL.
      lv_message = |DTTS Application Fault - Operation: { p_operation }|.
    ENDIF.
  ENDIF.

  LOOP AT p_items_table ASSIGNING <fs_item>.
    <fs_item>-tr_response  = lv_response_code.
    <fs_item>-trans_stat   = lv_message.
    <fs_item>-prod_stat    = 'ERROR'.
    <fs_item>-notif_id     = ''.
    <fs_item>-changed_date = sy-datum.
    <fs_item>-changed_time = sy-uzeit.
    <fs_item>-changed_by   = sy-uname.
  ENDLOOP.

  LOOP AT p_header_table ASSIGNING <fs_header>.
    <fs_header>-status       = 'ERROR'.
    <fs_header>-changed_date = sy-datum.
    <fs_header>-changed_time = sy-uzeit.
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

  IF p_items_table  IS NOT INITIAL. MODIFY zmm_sst_dtts_itm FROM TABLE p_items_table. ENDIF.
  IF p_header_table IS NOT INITIAL. MODIFY zmm_sst_dtts_hdr FROM TABLE p_header_table. ENDIF.
ENDFORM.
```

---

### FORM handle_api_error_multiple

```abap
FORM handle_api_error_multiple
  USING    p_exception    TYPE REF TO cx_ai_system_fault
  CHANGING p_items_table  TYPE table
           p_header_table TYPE table.

  DATA: lv_sys_error  TYPE string,
        lv_mpl_id     TYPE string,
        lv_error_code TYPE string.
  FIELD-SYMBOLS: <fs_item>   TYPE zmm_sst_dtts_itm,
                 <fs_header> TYPE zmm_sst_dtts_hdr.

  lv_sys_error = p_exception->get_text( ).

  IF lv_sys_error CS 'MPL ID'.
    FIND REGEX 'MPL ID ([A-Za-z0-9_]+)' IN lv_sys_error SUBMATCHES lv_mpl_id.
  ENDIF.
  IF lv_sys_error CS '<FC>'.
    FIND REGEX '<FC>(\d+)</FC>' IN lv_sys_error SUBMATCHES lv_error_code.
  ENDIF.

  LOOP AT p_items_table ASSIGNING <fs_item>.
    <fs_item>-tr_response  = lv_error_code.
    <fs_item>-prod_stat    = 'ERROR'.
    <fs_item>-trans_stat   = lv_sys_error.
    <fs_item>-changed_date = sy-datum.
    <fs_item>-changed_time = sy-uzeit.
    <fs_item>-changed_by   = sy-uname.
  ENDLOOP.

  LOOP AT p_header_table ASSIGNING <fs_header>.
    <fs_header>-status       = 'ERROR'.
    <fs_header>-changed_date = sy-datum.
    <fs_header>-changed_time = sy-uzeit.
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

  MODIFY zmm_sst_dtts_itm FROM TABLE p_items_table.
  MODIFY zmm_sst_dtts_hdr FROM TABLE p_header_table.
ENDFORM.
```

---

### FORM handle_generic_error_multiple

```abap
FORM handle_generic_error_multiple
  USING    p_exception    TYPE REF TO cx_root
  CHANGING p_items_table  TYPE table
           p_header_table TYPE table.

  DATA: lv_root_error TYPE string.
  FIELD-SYMBOLS: <fs_item>   TYPE zmm_sst_dtts_itm,
                 <fs_header> TYPE zmm_sst_dtts_hdr.

  lv_root_error = p_exception->get_text( ).

  LOOP AT p_items_table ASSIGNING <fs_item>.
    <fs_item>-tr_response  = 'ERROR'.
    <fs_item>-prod_stat    = 'ERROR'.
    <fs_item>-changed_date = sy-datum.
    <fs_item>-changed_time = sy-uzeit.
    <fs_item>-changed_by   = sy-uname.
  ENDLOOP.

  LOOP AT p_header_table ASSIGNING <fs_header>.
    <fs_header>-status       = 'ERROR'.
    <fs_header>-changed_date = sy-datum.
    <fs_header>-changed_time = sy-uzeit.
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

  MODIFY zmm_sst_dtts_itm FROM TABLE p_items_table.
  MODIFY zmm_sst_dtts_hdr FROM TABLE p_header_table.
ENDFORM.
```

---

### FORM format_data

Formats GTIN (14-digit zero-padded), quantity (integer, no decimals), batch (condensed), and expiry date (`YYYY-MM-DD`).

```abap
FORM format_data USING    p_gtin_in     TYPE any
                          p_quantity_in TYPE any
                          p_batch_in    TYPE any
                          p_exp_date_in TYPE any
                 CHANGING p_gtin_out    TYPE string
                          p_quantity_out TYPE string
                          p_batch_out   TYPE string
                          p_exp_date_out TYPE string.

  DATA: lv_len     TYPE i,
        lv_qty_int TYPE string,
        lv_qty_dec TYPE string,
        lv_year(4)  TYPE c,
        lv_month(2) TYPE c,
        lv_day(2)   TYPE c.

  " GTIN — pad to 14 digits
  p_gtin_out = p_gtin_in.
  CONDENSE p_gtin_out NO-GAPS.
  lv_len = strlen( p_gtin_out ).
  IF lv_len < 14.
    p_gtin_out = |{ p_gtin_out WIDTH = 14 PAD = '0' ALIGN = RIGHT }|.
  ENDIF.

  " Quantity — strip decimals
  p_quantity_out = p_quantity_in.
  IF p_quantity_out CS '.'.
    SPLIT p_quantity_out AT '.' INTO lv_qty_int lv_qty_dec.
    p_quantity_out = lv_qty_int.
  ENDIF.
  p_quantity_out = |{ p_quantity_out ALPHA = OUT }|.
  CONDENSE p_quantity_out NO-GAPS.

  " Batch
  p_batch_out = p_batch_in.
  CONDENSE p_batch_out NO-GAPS.

  " Expiry Date — YYYY-MM-DD
  CLEAR p_exp_date_out.
  IF p_exp_date_in IS NOT INITIAL.
    lv_year  = p_exp_date_in+0(4).
    lv_month = p_exp_date_in+4(2).
    lv_day   = p_exp_date_in+6(2).
    p_exp_date_out = |{ lv_year }-{ lv_month }-{ lv_day }|.
  ENDIF.
ENDFORM.
```

---

### FORM get_error_description

```abap
FORM get_error_description USING    p_error_code  TYPE char5
                           CHANGING p_description TYPE char255.

  CLEAR p_description.
  SELECT SINGLE description FROM zdtts_errorlist INTO @p_description
    WHERE error_code = @p_error_code
      AND language   = 'en'.

  IF sy-subrc <> 0.
    p_description = |Error Code: { p_error_code }|.
  ENDIF.
ENDFORM.
```

---

## Key Database Tables

| Table | Purpose |
|---|---|
| `ZIMMDTTS_4` | View: DTTS item helper + header join |
| `ZMM_SST_DTTS_HDR` | DTTS transaction header records |
| `ZMM_SST_DTTS_ITM` | DTTS transaction item records |
| `ZMM_SST_DTTSIT2` | Reprocessed item records (upsert target) |
| `ZMM_DTTS_API_CON` | API configuration (proxy class, method, port, structures) |
| `ZDTTS_ERRORLIST` | Error code to description mapping |
| `T157E` | Movement reason text (for deactivation) |

---

## Supported Operations

| Operation | Description |
|---|---|
| `ACCEPT` | Accept batch from source |
| `RETURN` | Return batch to source |
| `DISPATCH` | Dispatch batch to destination |
| `DISPATCH_CANCEL` | Cancel dispatch |
| `TRANSFER` | Transfer between locations |
| `TRANSFER_CANCEL` | Cancel transfer |
| `CONSUME` | Consume (serial-tracked) |
| `CONSUME_CANCEL` | Cancel consumption |
| `DRUG_SALE` | Pharmacy drug sale |
| `DRUG_SALE_CANCEL` | Cancel pharmacy sale |
| `DEACTIVATE` | Deactivate products |
| `DEACTIVATE_CANCEL` | Cancel deactivation |
