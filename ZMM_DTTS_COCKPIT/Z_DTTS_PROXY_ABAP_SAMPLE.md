```abap
*&---------------------------------------------------------------------*
*& Report Z_DTTS_PROXY_ABAP_SAMPLE
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT Z_DTTS_PROXY_ABAP_SAMPLE.

TABLES: mseg.

*" Variables for dynamic proxy-based web service call (config-driven via ZMM_DTTS_API_CON)

*----------------------------------------------------------------------*
* SELECTION SCREEN
*----------------------------------------------------------------------*
SELECTION-SCREEN BEGIN OF BLOCK b1 WITH FRAME TITLE TEXT-001.
  SELECT-OPTIONS: s_matdoc FOR mseg-mblnr,
                  s_year   FOR mseg-mjahr,
                  s_bwart  FOR mseg-bwart.
  PARAMETERS: p_oper TYPE char20.
SELECTION-SCREEN END OF BLOCK b1.

*----------------------------------------------------------------------*
* LOCAL CLASS DEFINITION
*----------------------------------------------------------------------*
CLASS lcl_dtts_cockpit DEFINITION.
  PUBLIC SECTION.
    DATA: request_ptr         TYPE REF TO data,              "Dynamic request structure pointer
          response_ptr        TYPE REF TO data,              "Dynamic response structure pointer
          lo_proxy            TYPE REF TO object,            "Web service proxy object
          p_lport             TYPE prx_logical_port_name,    "Logical port name for proxy
          ptab                TYPE abap_parmbind_tab,        "Parameter binding table for proxy
          wa_ptab             TYPE abap_parmbind,            "Single parameter binding entry
          wa_zmm_dtts_api_con TYPE zmm_dtts_api_con.        "API config row (proxy class, method etc.)
    TYPES: BEGIN OF ty_alv_data,
             selkz            TYPE char1,
             "mandt            TYPE mandt,
             tran_id          TYPE char20,
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
             doc_yr           TYPE mjahr,
             item_operation   TYPE char20,
             header_operation TYPE char20,
             frm_gln          TYPE zmm_sst_gln_src,
             to_gln           TYPE zmm_sst_gln_des,
             auth_gln         TYPE zmm_sst_gln_auth,

           END OF ty_alv_data.

    DATA: gt_alv_data TYPE TABLE OF ty_alv_data.

    DATA: go_alv       TYPE REF TO cl_gui_alv_grid,
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
    " ZIMMDTTS_4 is a view mapping to ZIMM_DTTS_FY_HELPER left outer join zmm_sst_dtts_hdr
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
           hdr~doc_yr,
           itm~item_operation,
           hdr~operation AS header_operation,
           hdr~frm_gln,
           hdr~to_gln,
           hdr~auth_gln

      FROM zimmdtts_4 AS itm
      LEFT OUTER JOIN zmm_sst_dtts_hdr AS hdr ON  itm~mat_doc  = hdr~mat_doc
                                              AND itm~doc_year = hdr~doc_yr
                                              AND itm~mvt_type = hdr~mvt_type
      WHERE itm~mat_doc IN @s_matdoc
        AND itm~doc_year IN @s_year
        AND itm~mvt_type IN @s_bwart
        ""AND hdr~operation = @p_oper
      INTO CORRESPONDING FIELDS OF TABLE @gt_alv_data.


    IF sy-subrc <> 0.
      MESSAGE 'No data found for the given selection criteria.' TYPE 'S' DISPLAY LIKE 'E'.
    ENDIF.
  ENDMETHOD.

  METHOD display_alv.
    DATA: lt_fcat   TYPE lvc_t_fcat,
          ls_layout TYPE lvc_s_layo.

    IF go_container IS INITIAL.
      " Need to create a screen 0100 for this ALV or use full screen CL_SALV_TABLE.
      " For simplicity in full screen without screen painter, we use cl_gui_alv_grid with default full screen container.
*      CREATE OBJECT go_alv
*        EXPORTING
*          i_parent = cl_gui_container=>screen0.
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
          i_structure_name = 'ZIMM_DTTS_FY_HELPER' " Approximation, manual setup is better for custom fields
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
          is_layout       = ls_layout
        CHANGING
          it_outtab       = gt_alv_data
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

    " 2. Remove items that have status SUCCESS
    DELETE lt_selected WHERE prod_stat = 'SUCCESS'.

    IF lt_selected IS INITIAL.
      MESSAGE 'No eligible items to reprocess (all selected were SUCCESS).' TYPE 'I'.
      RETURN.
    ENDIF.

    " 3. Sort selected items using key matdoc, mjahr and movement type
    SORT lt_selected BY mat_doc doc_yr mvt_type.

    " 4. Create a new table with only unique matdoc, mjahr and movement type
    lt_unique = lt_selected.
    DELETE ADJACENT DUPLICATES FROM lt_unique COMPARING mat_doc doc_yr mvt_type.

    " 5. Loop in this unique table
    LOOP AT lt_unique INTO DATA(ls_unique).
      CLEAR: lt_header, lt_items.

      " Get the header row from header table and append it
      SELECT * FROM zmm_sst_dtts_hdr
        INTO TABLE @DATA(lt_hdr_tmp)
        WHERE mat_doc = @ls_unique-mat_doc
          AND doc_yr  = @ls_unique-doc_yr
          AND mvt_type = @ls_unique-mvt_type.
      APPEND LINES OF lt_hdr_tmp TO lt_header.

      DATA(lv_operation) = ls_unique-header_operation.

      " Loop at the selected items table for the item lines and append to lt_items
      LOOP AT lt_selected INTO DATA(ls_sel_item)
           WHERE mat_doc = ls_unique-mat_doc
             AND doc_yr = ls_unique-doc_yr
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
            PERFORM accept_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'RETURN'.
            PERFORM return_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'DISPATCH'.
            PERFORM dispatch_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'DISPATCH_CANCEL'.
            PERFORM dispatch_cancel_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'TRANSFER'.
            PERFORM transfer_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'TRANSFER_CANCEL'.
            PERFORM transfer_cancel_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'CONSUME'.
            PERFORM consume_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'CONSUME_CANCEL'.
            PERFORM consume_cancel_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'DRUG_SALE'.
            PERFORM pharmacy_sale_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'DRUG_SALE_CANCEL'.
            PERFORM pharmacy_sale_cancel_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'DEACTIVATE'.
            PERFORM deactivate_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
          WHEN 'DEACTIVATE_CANCEL'.
            PERFORM deactivate_cancel_request   USING lt_mseg lt_header lt_items CHANGING <fs_request>.
        ENDCASE.

        " =============================================================
        " CREATE PROXY AND CALL DTTS WEB SERVICE
        " =============================================================
        CLEAR ptab.
        CLEAR wa_ptab.
        wa_ptab-name  = 'LOGICAL_PORT_NAME'.
        wa_ptab-kind  = cl_abap_objectdescr=>exporting.
        p_lport = wa_zmm_dtts_api_con-logical_port.
        wa_ptab-value  = REF #( p_lport ).
        INSERT wa_ptab INTO TABLE ptab.

        TRY.
            CREATE OBJECT lo_proxy TYPE (wa_zmm_dtts_api_con-proxy_class)
              PARAMETER-TABLE ptab.

            CALL METHOD lo_proxy->(wa_zmm_dtts_api_con-method_name)
              EXPORTING
                input  = <fs_request>
              IMPORTING
                output = <fs_response>.
            MESSAGE 'Reprocessing Completed.' TYPE 'S'.
            " ==========================================================
            " PROCESS API RESPONSE AND UPDATE Z-TABLE RECORDS
            " ==========================================================
            CASE lv_operation.
              WHEN 'ACCEPT'.
                PERFORM accept_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'RETURN'.
                PERFORM return_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'DISPATCH'.
                PERFORM dispatch_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'DISPATCH_CANCEL'.
                PERFORM dispatch_cancel_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'TRANSFER'.
                PERFORM transfer_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'TRANSFER_CANCEL'.
                PERFORM transfer_cancel_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'CONSUME'.
                PERFORM consume_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'CONSUME_CANCEL'.
                PERFORM consume_cancel_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'DRUG_SALE'.
                PERFORM pharmacy_sale_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'DRUG_SALE_CANCEL'.
                PERFORM pharmacy_sale_cancel_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'DEACTIVATE'.
                PERFORM deactivate_response   USING <fs_response> CHANGING lt_header lt_items.
              WHEN 'DEACTIVATE_CANCEL'.
                PERFORM deactivate_cancel_response   USING <fs_response> CHANGING lt_header lt_items.
            ENDCASE.

            " Custom Table updates for reprocess
*            IF lt_header IS NOT INITIAL.
*              MODIFY zmm_sst_dtts_hdr FROM TABLE lt_header.
*            ENDIF.

            " Instead of ZMM_SST_DTTS_ITM, we append a new line to ZMM_SST_DTTSIT2 if it does not exist,
            " else modify the status alone. The new line will have same data as old table except PROD_STAT and Trans Status.
            LOOP AT lt_items INTO DATA(ls_new_item).
              DATA: ls_dttsit2 TYPE zmm_sst_dttsit2.

              " Check if line exists
              SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @ls_dttsit2
                "WHERE mandt   = @ls_new_item-mandt
                  WHERE mat_doc = @ls_new_item-mat_doc
                   AND  doc_year = @ls_new_item-tran_id+11(4)
                  AND mvt_type = @ls_new_item-mvt_type.

              IF sy-subrc = 0.
                " Record exists, just modify status
                "DATA ls_header like line of lt_header.
                "ls_header = lt_header[ 1 ].
                "MOVE-CORRESPONDING ls_header to ls_dttsit2 .
                ls_dttsit2-prod_stat  = ls_new_item-prod_stat.
                ls_dttsit2-trans_stat = ls_new_item-trans_stat.

                MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
              ELSE.
                " Record doesn't exist, append new line using data from old table with new status
                MOVE-CORRESPONDING ls_new_item TO ls_dttsit2.
                DATA ls_header LIKE LINE OF lt_header.
                ls_header = lt_header[ 1 ].
*                MOVE-CORRESPONDING ls_header TO ls_dttsit2 .
                ls_dttsit2-operation = ls_header-operation.
                ls_dttsit2-frm_gln = ls_header-frm_gln.
                ls_dttsit2-to_gln = ls_header-to_gln.
                ls_dttsit2-doc_year = ls_header-doc_yr.
                CALL FUNCTION 'CONVERSION_EXIT_ALPHA_OUTPUT'
                  EXPORTING
                    input  = ls_dttsit2-tran_id
                  IMPORTING
                    output = ls_dttsit2-tran_id.

                " Set new PROD_STAT and TRANS_STAT handled by response FORM previously
                MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
              ENDIF.
            ENDLOOP.

          CATCH cx_ai_application_fault INTO DATA(lx_app_fault).
*            PERFORM handle_dtts_application_fault   USING lx_app_fault lv_operation CHANGING lt_items lt_header.
            LOOP AT lt_items INTO ls_new_item.
*              DATA: ls_dttsit2 TYPE zmm_sst_dttsit2.

              " Check if line exists
              SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @ls_dttsit2
                "WHERE mandt   = @ls_new_item-mandt
                  WHERE mat_doc = @ls_new_item-mat_doc
                   AND  doc_year = @ls_new_item-tran_id+11(4)
                  AND mvt_type = @ls_new_item-mvt_type.

              IF sy-subrc = 0.
                " Record exists, just modify status
                "DATA ls_header like line of lt_header.
                "ls_header = lt_header[ 1 ].
                "MOVE-CORRESPONDING ls_header to ls_dttsit2 .
                ls_dttsit2-prod_stat  = ls_new_item-prod_stat.
                ls_dttsit2-trans_stat = ls_new_item-trans_stat.

                MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
              ELSE.
                " Record doesn't exist, append new line using data from old table with new status
                MOVE-CORRESPONDING ls_new_item TO ls_dttsit2.
*                DATA ls_header LIKE LINE OF lt_header.
                ls_header = lt_header[ 1 ].
*                MOVE-CORRESPONDING ls_header TO ls_dttsit2 .
                ls_dttsit2-operation = ls_header-operation.
                ls_dttsit2-frm_gln = ls_header-frm_gln.
                ls_dttsit2-to_gln = ls_header-to_gln.
                ls_dttsit2-doc_year = ls_header-doc_yr.
                CALL FUNCTION 'CONVERSION_EXIT_ALPHA_OUTPUT'
                  EXPORTING
                    input  = ls_dttsit2-tran_id
                  IMPORTING
                    output = ls_dttsit2-tran_id.

                " Set new PROD_STAT and TRANS_STAT handled by response FORM previously
                MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
              ENDIF.
            ENDLOOP.
          CATCH cx_ai_system_fault INTO DATA(lx_sys).
*            PERFORM handle_api_error_multiple   USING lx_sys CHANGING lt_items lt_header.
            LOOP AT lt_items INTO ls_new_item.
*              DATA: ls_dttsit2 TYPE zmm_sst_dttsit2.

              " Check if line exists
              SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @ls_dttsit2
                "WHERE mandt   = @ls_new_item-mandt
                  WHERE mat_doc = @ls_new_item-mat_doc
                   AND  doc_year = @ls_new_item-tran_id+11(4)
                  AND mvt_type = @ls_new_item-mvt_type.

              IF sy-subrc = 0.
                " Record exists, just modify status
                "DATA ls_header like line of lt_header.
                "ls_header = lt_header[ 1 ].
                "MOVE-CORRESPONDING ls_header to ls_dttsit2 .
                ls_dttsit2-prod_stat  = ls_new_item-prod_stat.
                ls_dttsit2-trans_stat = ls_new_item-trans_stat.

                MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
              ELSE.
                " Record doesn't exist, append new line using data from old table with new status
                MOVE-CORRESPONDING ls_new_item TO ls_dttsit2.
*                DATA ls_header LIKE LINE OF lt_header.
                ls_header = lt_header[ 1 ].
*                MOVE-CORRESPONDING ls_header TO ls_dttsit2 .
                ls_dttsit2-operation = ls_header-operation.
                ls_dttsit2-frm_gln = ls_header-frm_gln.
                ls_dttsit2-to_gln = ls_header-to_gln.
                ls_dttsit2-doc_year = ls_header-doc_yr.
                CALL FUNCTION 'CONVERSION_EXIT_ALPHA_OUTPUT'
                  EXPORTING
                    input  = ls_dttsit2-tran_id
                  IMPORTING
                    output = ls_dttsit2-tran_id.

                " Set new PROD_STAT and TRANS_STAT handled by response FORM previously
                MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
              ENDIF.
            ENDLOOP.
          CATCH cx_root INTO DATA(lx_root).
*            PERFORM handle_generic_error_multiple   USING lx_root CHANGING lt_items lt_header.
            LOOP AT lt_items INTO ls_new_item.
*              DATA: ls_dttsit2 TYPE zmm_sst_dttsit2.

              " Check if line exists
              SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @ls_dttsit2
                "WHERE mandt   = @ls_new_item-mandt
                  WHERE mat_doc = @ls_new_item-mat_doc
                   AND  doc_year = @ls_new_item-tran_id+11(4)
                  AND mvt_type = @ls_new_item-mvt_type.

              IF sy-subrc = 0.
                " Record exists, just modify status
                "DATA ls_header like line of lt_header.
                "ls_header = lt_header[ 1 ].
                "MOVE-CORRESPONDING ls_header to ls_dttsit2 .
                ls_dttsit2-prod_stat  = ls_new_item-prod_stat.
                ls_dttsit2-trans_stat = ls_new_item-trans_stat.

                MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
              ELSE.
                " Record doesn't exist, append new line using data from old table with new status
                MOVE-CORRESPONDING ls_new_item TO ls_dttsit2.
*                DATA ls_header LIKE LINE OF lt_header.
                ls_header = lt_header[ 1 ].
*                MOVE-CORRESPONDING ls_header TO ls_dttsit2 .
                ls_dttsit2-operation = ls_header-operation.
                ls_dttsit2-frm_gln = ls_header-frm_gln.
                ls_dttsit2-to_gln = ls_header-to_gln.
                ls_dttsit2-doc_year = ls_header-doc_yr.
                CALL FUNCTION 'CONVERSION_EXIT_ALPHA_OUTPUT'
                  EXPORTING
                    input  = ls_dttsit2-tran_id
                  IMPORTING
                    output = ls_dttsit2-tran_id.

                " Set new PROD_STAT and TRANS_STAT handled by response FORM previously
                MODIFY zmm_sst_dttsit2 FROM ls_dttsit2.
              ENDIF.
            ENDLOOP.
        ENDTRY.
      ENDIF.
    ENDLOOP.


  ENDMETHOD.


ENDCLASS.

*----------------------------------------------------------------------*
* MAIN PROGRAM EXECUTION
*----------------------------------------------------------------------*
DATA: go_main TYPE REF TO lcl_dtts_cockpit.

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
*& Form  ACCEPT_REQUEST
*&---------------------------------------------------------------------*
FORM accept_request  USING p_mseg_table TYPE table
                           p_header_table TYPE table
                           p_items_table TYPE table
                     CHANGING p_request TYPE zaccept_service_request.

  DATA: lwa_request           TYPE zaccept_service_request,
        lwa_product_line      TYPE zaccept_service_request_produ1,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_from_gln           TYPE zmm_br_gln,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


  " Get GLNs from header record
  READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
  IF sy-subrc = 0.
    lv_from_gln = <fs_header>-frm_gln.
    lv_auth_gln = <fs_header>-to_gln.
  ENDIF.

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
    lwa_product_line-gtin     = lv_gtin_formatted.
    lwa_product_line-quantity = lv_quantity_formatted.
    lwa_product_line-bn       = lv_batch_formatted.
    lwa_product_line-xd       = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-accept_batch_service_request-productlist-product.

  ENDLOOP.

  lwa_request-accept_batch_service_request-fromgln = lv_from_gln.
  lwa_request-accept_batch_service_request-authgln = lv_auth_gln.

  p_request = lwa_request.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  RETURN_REQUEST
*&---------------------------------------------------------------------*
FORM return_request  USING p_mseg_table TYPE table
                           p_header_table TYPE table
                           p_items_table TYPE table
                     CHANGING p_request TYPE zreturn_batch_service_request.

  DATA: lwa_request           TYPE zreturn_batch_service_request,
        lwa_product_line      TYPE zreturn_batch_service_request3,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_to_gln             TYPE zmm_br_gln,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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

    PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
                              <fs_item>-batch <fs_item>-exp_date
        CHANGING lv_gtin_formatted lv_quantity_formatted
                 lv_batch_formatted lv_exp_date_formatted.

    CLEAR lwa_product_line.
    lwa_product_line-gtin     = lv_gtin_formatted.
    lwa_product_line-quantity = lv_quantity_formatted.
    lwa_product_line-bn       = lv_batch_formatted.
    lwa_product_line-xd       = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-return_batch_service-productlist-product.

  ENDLOOP.

  lwa_request-return_batch_service-togln = lv_to_gln.
  lwa_request-return_batch_service-authgln = lv_auth_gln.

  p_request = lwa_request.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  DISPATCH_REQUEST
*&---------------------------------------------------------------------*
FORM dispatch_request  USING p_mseg_table TYPE table
                             p_header_table TYPE table
                             p_items_table TYPE table
                       CHANGING p_request TYPE zdispatch_batch_service_reque3.

  DATA: lwa_request           TYPE zdispatch_batch_service_reque3,
        lwa_product_line      TYPE zdispatch_batch_service_reque1,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_to_gln             TYPE zmm_br_gln,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
    PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
                              <fs_item>-batch <fs_item>-exp_date
        CHANGING lv_gtin_formatted lv_quantity_formatted
                 lv_batch_formatted lv_exp_date_formatted.

    CLEAR lwa_product_line.
    lwa_product_line-gtin     = lv_gtin_formatted.
    lwa_product_line-quantity = lv_quantity_formatted.
    lwa_product_line-bn       = lv_batch_formatted.
    lwa_product_line-xd       = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-dispatch_batch_service-productlist-product.

  ENDLOOP.

  lwa_request-dispatch_batch_service-togln = lv_to_gln.
  lwa_request-dispatch_batch_service-authgln = lv_auth_gln.

  p_request = lwa_request.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  DISPATCH_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM dispatch_cancel_request  USING p_mseg_table TYPE table
                                    p_header_table TYPE table
                                    p_items_table TYPE table
                              CHANGING p_request TYPE zdispatch_cancel_request.

  DATA: lwa_request           TYPE zdispatch_cancel_request,
        lwa_product_line      TYPE zdispatch_cancel_request_prod1,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_to_gln             TYPE zmm_br_gln,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


  READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
  IF sy-subrc = 0.
    lv_to_gln = <fs_header>-frm_gln.
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
    lwa_product_line-gtin     = lv_gtin_formatted.
    lwa_product_line-quantity = lv_quantity_formatted.
    lwa_product_line-bn       = lv_batch_formatted.
    lwa_product_line-xd       = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-dispatch_cancel-productlist-product.

  ENDLOOP.

  lwa_request-dispatch_cancel-togln = lv_to_gln.
  lwa_request-dispatch_cancel-authgln = lv_auth_gln.

  p_request = lwa_request.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  TRANSFER_REQUEST
*&---------------------------------------------------------------------*
FORM transfer_request  USING p_mseg_table TYPE table
                             p_header_table TYPE table
                             p_items_table TYPE table
                       CHANGING p_request TYPE ztransfer_batch_service_reque3.

  DATA: lwa_request           TYPE ztransfer_batch_service_reque3,
        lwa_product_line      TYPE ztransfer_batch_service_reque2,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_to_gln             TYPE zmm_br_gln,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
    PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
                              <fs_item>-batch <fs_item>-exp_date
        CHANGING lv_gtin_formatted lv_quantity_formatted
                 lv_batch_formatted lv_exp_date_formatted.

    CLEAR lwa_product_line.
    lwa_product_line-gtin     = lv_gtin_formatted.
    lwa_product_line-quantity = lv_quantity_formatted.
    lwa_product_line-bn       = lv_batch_formatted.
    lwa_product_line-xd       = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-transfer_batch_service-productlist-product.

  ENDLOOP.

  lwa_request-transfer_batch_service-togln = lv_to_gln.
  lwa_request-transfer_batch_service-authgln = lv_auth_gln.

  p_request = lwa_request.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  TRANSFER_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM transfer_cancel_request  USING p_mseg_table TYPE table
                                    p_header_table TYPE table
                                    p_items_table TYPE table
                              CHANGING p_request TYPE ztransfer_cancel_request.

  DATA: lwa_request           TYPE ztransfer_cancel_request,
        lwa_product_line      TYPE ztransfer_cancel_request_prod1,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_to_gln             TYPE zmm_br_gln,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
    PERFORM format_data USING <fs_item>-gtin <fs_item>-prod_qty
                            <fs_item>-batch <fs_item>-exp_date
      CHANGING lv_gtin_formatted lv_quantity_formatted
               lv_batch_formatted lv_exp_date_formatted.

    CLEAR lwa_product_line.
    lwa_product_line-gtin     = lv_gtin_formatted.
    lwa_product_line-quantity = lv_quantity_formatted.
    lwa_product_line-bn       = lv_batch_formatted.
    lwa_product_line-xd       = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-transfer_cancel-productlist-product.

  ENDLOOP.

  lwa_request-transfer_cancel-togln = lv_to_gln.
  lwa_request-transfer_cancel-authgln = lv_auth_gln.

  p_request = lwa_request.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  CONSUME_REQUEST
*&---------------------------------------------------------------------*
FORM consume_request  USING p_mseg_table TYPE table
                            p_header_table TYPE table
                            p_items_table TYPE table
                      CHANGING p_request TYPE zconsume_service_request.

  DATA: lwa_request           TYPE zconsume_service_request,
        lwa_product_line      TYPE zconsume_service_request_prod1,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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

    CLEAR lwa_product_line.
    lwa_product_line-gtin = lv_gtin_formatted.
    lwa_product_line-sn = <fs_item>-sr_number.
    lwa_product_line-bn   = lv_batch_formatted.
    lwa_product_line-xd   = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-consume_service-productlist-product.

  ENDLOOP.

  lwa_request-consume_service-authgln = lv_auth_gln.

  p_request = lwa_request.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  CONSUME_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM consume_cancel_request  USING p_mseg_table TYPE table
                                   p_header_table TYPE table
                                   p_items_table TYPE table
                             CHANGING p_request TYPE zconsume_cancel_request.

  DATA: lwa_request           TYPE zconsume_cancel_request,
        lwa_product_line      TYPE zconsume_cancel_request_produ1,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
    lwa_product_line-bn   = lv_batch_formatted.
    lwa_product_line-xd   = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-consume_cancel-productlist-product.

  ENDLOOP.

  lwa_request-consume_cancel-authgln = lv_auth_gln.

  p_request = lwa_request.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  PHARMACY_SALE_REQUEST
*&---------------------------------------------------------------------*
FORM pharmacy_sale_request  USING p_mseg_table TYPE table
                                  p_header_table TYPE table
                                  p_items_table TYPE table
                            CHANGING p_request TYPE zpharmacy_sale_request.

  DATA: lwa_request           TYPE zpharmacy_sale_request,
        lwa_product_line      TYPE zpharmacy_sale_request_produc1,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_to_gln             TYPE zmm_br_gln,
        lv_auth_gln           TYPE zmm_br_gln,
        lv_prescription_date  TYPE string,
        lv_year(4)            TYPE c,
        lv_month(2)           TYPE c,
        lv_day(2)             TYPE c.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


  READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
  IF sy-subrc = 0.
    lv_to_gln = <fs_header>-to_gln.
    lv_auth_gln = <fs_header>-frm_gln.
  ENDIF.

  " Format current date as YYYY-MM-DD for prescription date
  lv_year  = sy-datum+0(4).
  lv_month = sy-datum+4(2).
  lv_day   = sy-datum+6(2).
  lv_prescription_date = |{ lv_year }-{ lv_month }-{ lv_day }|.

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
    lwa_product_line-bn   = lv_batch_formatted.
    lwa_product_line-xd   = lv_exp_date_formatted.

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
*& Form  PHARMACY_SALE_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM pharmacy_sale_cancel_request USING p_mseg_table TYPE table
                                        p_header_table TYPE table
                                        p_items_table TYPE table
                                  CHANGING p_request TYPE zpharmacy_sale_cancel_request3.

  DATA: lwa_request           TYPE zpharmacy_sale_cancel_request3,
        lwa_product_line      TYPE zpharmacy_sale_cancel_request2,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_to_gln             TYPE zmm_br_gln,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


  READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
  IF sy-subrc = 0.
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
    lwa_product_line-bn   = lv_batch_formatted.
    lwa_product_line-xd   = lv_exp_date_formatted.

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
*& Form  DEACTIVATE_REQUEST
*&---------------------------------------------------------------------*
FORM deactivate_request  USING p_mseg_table TYPE table
                               p_header_table TYPE table
                               p_items_table TYPE table
                         CHANGING p_request TYPE zdeactivation_service_request3.

  DATA: lwa_request           TYPE zdeactivation_service_request3,
        lwa_product_line      TYPE zdeactivation_service_request1,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_auth_gln           TYPE zmm_br_gln,
        lv_grund              TYPE mb_grbew,
        lv_grund_desc         TYPE grtxt.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm,
                 <fs_mseg>   TYPE matdoc.


  READ TABLE p_header_table ASSIGNING <fs_header> INDEX 1.
  IF sy-subrc = 0.
    lv_auth_gln = <fs_header>-frm_gln.
  ENDIF.

  READ TABLE p_mseg_table ASSIGNING <fs_mseg> INDEX 1.
  IF sy-subrc = 0 AND <fs_mseg>-grund IS NOT INITIAL.
    lv_grund = <fs_mseg>-grund.

    " Get description from T157E table for English language
    SELECT SINGLE grtxt FROM t157e WHERE spras = 'E'
        AND bwart = @<fs_mseg>-bwart AND grund = @lv_grund  INTO @lv_grund_desc.

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
    lwa_product_line-bn   = lv_batch_formatted.
    lwa_product_line-xd   = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-deactivation_request-productlist-product.

  ENDLOOP.
  SHIFT lv_grund LEFT DELETING LEADING '0'.
  lwa_request-deactivation_request-authgln = lv_auth_gln.
  lwa_request-deactivation_request-dr = lv_grund.
  lwa_request-deactivation_request-explanation = lv_grund_desc.

  p_request = lwa_request.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  DEACTIVATE_CANCEL_REQUEST
*&---------------------------------------------------------------------*
FORM deactivate_cancel_request  USING p_mseg_table TYPE table
                                      p_header_table TYPE table
                                      p_items_table TYPE table
                                CHANGING p_request TYPE zdeactivation_cancel_request.

  DATA: lwa_request           TYPE zdeactivation_cancel_request,
        lwa_product_line      TYPE zdeactivation_cancel_request_1,
        lv_gtin_formatted     TYPE string,
        lv_quantity_formatted TYPE string,
        lv_batch_formatted    TYPE string,
        lv_exp_date_formatted TYPE string,
        lv_auth_gln           TYPE zmm_br_gln.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
    lwa_product_line-bn   = lv_batch_formatted.
    lwa_product_line-sn = <fs_item>-sr_number.
    lwa_product_line-xd   = lv_exp_date_formatted.

    APPEND lwa_product_line TO lwa_request-deactivation_cancel-productlist-product.

  ENDLOOP.

  lwa_request-deactivation_cancel-authgln = lv_auth_gln.

  p_request = lwa_request.

ENDFORM.
*&---------------------------------------------------------------------*
*& SECTION 3: RESPONSE PROCESSING FORMS
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*

*&---------------------------------------------------------------------*
*& Form  ACCEPT_RESPONSE
*&---------------------------------------------------------------------*
FORM accept_response  USING p_response TYPE zaccept_service_response
                      CHANGING p_header_table TYPE table
                               p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zaccept_service_response_prod1,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  RETURN_RESPONSE
*&---------------------------------------------------------------------*
FORM return_response USING p_response TYPE zreturn_batch_service_response
                     CHANGING p_header_table TYPE table
                              p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zreturn_batch_service_respons3,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  DISPATCH_RESPONSE
*&---------------------------------------------------------------------*
FORM dispatch_response  USING p_response TYPE zdispatch_batch_service_respo3
                        CHANGING p_header_table TYPE table
                                 p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zdispatch_batch_service_respo1,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.

  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


  lv_notification_id = p_response-dispatch_batch_service_respons-notificationid.

  LOOP AT p_response-dispatch_batch_service_respons-productlist-product
       INTO lwa_product_resp.

    LOOP AT p_items_table ASSIGNING <fs_item>.
      lv_item_gtin = <fs_item>-gtin.
      lv_resp_gtin = lwa_product_resp-gtin.
      SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
      SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

      IF lv_item_gtin = lv_resp_gtin
   AND <fs_item>-batch = lwa_product_resp-bn
   AND <fs_item>-prod_qty = lwa_product_resp-quantity.
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  DISPATCH_CANCEL_RESPONSE
*&---------------------------------------------------------------------*
FORM dispatch_cancel_response USING p_response TYPE zdispatch_cancel_response
                              CHANGING p_header_table TYPE table
                                       p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zdispatch_cancel_response_pro1,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.


ENDFORM.

*&---------------------------------------------------------------------*
*& Form  TRANSFER_RESPONSE
*&---------------------------------------------------------------------*
FORM transfer_response USING p_response TYPE ztransfer_batch_service_respo3
                       CHANGING p_header_table TYPE table
                                p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE ztransfer_batch_service_respo2,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  TRANSFER_CANCEL_RESPONSE
*&---------------------------------------------------------------------*
FORM transfer_cancel_response USING p_response TYPE ztransfer_cancel_response
                              CHANGING p_header_table TYPE table
                                       p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE ztransfer_cancel_response_pro1,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


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
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  CONSUME_RESPONSE
*&---------------------------------------------------------------------*
FORM consume_response USING p_response TYPE zconsume_service_response
                      CHANGING p_header_table TYPE table
                               p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zconsume_service_response_pro1,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


  lv_notification_id = p_response-consume_service_response-notificationid.

  LOOP AT p_response-consume_service_response-productlist-product
       INTO lwa_product_resp.

    LOOP AT p_items_table ASSIGNING <fs_item>.
      lv_item_gtin = <fs_item>-gtin.
      lv_resp_gtin = lwa_product_resp-gtin.
      SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
      SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

      IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs_item>-sr_number = lwa_product_resp-sn.
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  CONSUME_CANCEL_RESPONSE
*&---------------------------------------------------------------------*
FORM consume_cancel_response USING p_response TYPE zconsume_cancel_response
                             CHANGING p_header_table TYPE table
                                      p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zconsume_cancel_response_prod1,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


  lv_notification_id = p_response-consume_cancel_service_respons-notificationid.

  LOOP AT p_response-consume_cancel_service_respons-productlist-product
       INTO lwa_product_resp.

    LOOP AT p_items_table ASSIGNING <fs_item>.
      lv_item_gtin = <fs_item>-gtin.
      lv_resp_gtin = lwa_product_resp-gtin.
      SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
      SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

      IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs_item>-sr_number = lwa_product_resp-sn.
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.
ENDFORM.

*&---------------------------------------------------------------------*
*& Form  PHARMACY_SALE_RESPONSE
*&---------------------------------------------------------------------*
FORM pharmacy_sale_response USING p_response TYPE zpharmacy_sale_response
                            CHANGING p_header_table TYPE table
                                     p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zpharmacy_sale_response_produ1,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.

  lv_notification_id = p_response-pharmacy_sale_service_response-notificationid.

  LOOP AT p_response-pharmacy_sale_service_response-productlist-product
       INTO lwa_product_resp.

    LOOP AT p_items_table ASSIGNING <fs_item>.
      lv_item_gtin = <fs_item>-gtin.
      lv_resp_gtin = lwa_product_resp-gtin.
      SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
      SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

      IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs_item>-sr_number = lwa_product_resp-sn.
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  PHARMACY_SALE_CANCEL_RESPONSE
*&---------------------------------------------------------------------*
FORM pharmacy_sale_cancel_response
                                  USING p_response TYPE zpharmacy_sale_cancel_respons3
                                  CHANGING p_header_table TYPE table
                                           p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zpharmacy_sale_cancel_respons2,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.

  lv_notification_id = p_response-pharmacy_sale_cancel_response-notificationid.

  LOOP AT p_response-pharmacy_sale_cancel_response-productlist-product
       INTO lwa_product_resp.

    LOOP AT p_items_table ASSIGNING <fs_item>.
      lv_item_gtin = <fs_item>-gtin.
      lv_resp_gtin = lwa_product_resp-gtin.
      SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
      SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

      IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs_item>-sr_number = lwa_product_resp-sn.
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  DEACTIVATE_RESPONSE
*&---------------------------------------------------------------------*
FORM deactivate_response  USING p_response TYPE zdeactivation_service_respons3
                          CHANGING p_header_table TYPE table
                                   p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zdeactivation_service_respons1,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


  lv_notification_id = p_response-deactivation_response-notificationid.

  LOOP AT p_response-deactivation_response-productlist-product
       INTO lwa_product_resp.

    LOOP AT p_items_table ASSIGNING <fs_item>.
      lv_item_gtin = <fs_item>-gtin.
      lv_resp_gtin = lwa_product_resp-gtin.
      SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
      SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

      IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs_item>-sr_number = lwa_product_resp-sn.
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  DEACTIVATE_CANCEL_RESPONSE
*&---------------------------------------------------------------------*
FORM deactivate_cancel_response USING p_response TYPE zdeactivation_cancel_response3
                              CHANGING p_header_table TYPE table
                                       p_items_table TYPE table.

  DATA: lwa_product_resp   TYPE zdeactivation_cancel_response1,
        lv_error_code      TYPE char5,
        lv_description     TYPE char255,
        lv_notification_id TYPE string,
        lv_all_success     TYPE abap_bool VALUE abap_true.
  DATA: lv_item_gtin TYPE string, lv_resp_gtin TYPE string.
  FIELD-SYMBOLS: <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_item>   TYPE zmm_sst_dtts_itm.


  lv_notification_id = p_response-deactivation_cancel_response-notificationid.

  LOOP AT p_response-deactivation_cancel_response-productlist-product
       INTO lwa_product_resp.

    LOOP AT p_items_table ASSIGNING <fs_item>.
      lv_item_gtin = <fs_item>-gtin.
      lv_resp_gtin = lwa_product_resp-gtin.
      SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
      SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

      IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = lwa_product_resp-bn AND <fs_item>-sr_number = lwa_product_resp-sn.
        <fs_item>-notif_id    = lv_notification_id.
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

        <fs_item>-trans_stat  = lv_description.
        <fs_item>-changed_date = sy-datum.
        <fs_item>-changed_time = sy-uzeit.
        <fs_item>-changed_by   = sy-uname.
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
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

ENDFORM.
*&---------------------------------------------------------------------*
*& SECTION 4: EXCEPTION HANDLERS & SUPPORTING PERFORMS
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*& Form  HANDLE_DTTS_APPLICATION_FAULT
*&---------------------------------------------------------------------*
*  Generic handler using config table fault attribute
FORM handle_dtts_application_fault USING p_exception TYPE REF TO cx_ai_application_fault
                                         p_operation TYPE char20
                                   CHANGING p_items_table TYPE table
                                            p_header_table TYPE table.

  DATA: lv_response_code TYPE string,
        lv_message       TYPE string.

  FIELD-SYMBOLS: <fs_item>   TYPE zmm_sst_dtts_itm,
                 <fs_header> TYPE zmm_sst_dtts_hdr,
                 <fs_field>  TYPE any.

  " ========== Extract Fault Details (Direct Access - Flat Structure) ==========

  TRY.
      " Try to access RESPONSE_CODE directly
      ASSIGN p_exception->('RESPONSE_CODE') TO <fs_field>.
      IF sy-subrc = 0 AND <fs_field> IS ASSIGNED.
        lv_response_code = <fs_field>.
      ENDIF.

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
    <fs_item>-trans_stat  = lv_message.
    <fs_item>-prod_stat   = 'ERROR'.
    <fs_item>-notif_id    = ''.

    " Update item timestamp
    <fs_item>-changed_date = sy-datum.
    <fs_item>-changed_time = sy-uzeit.
    <fs_item>-changed_by   = sy-uname.
  ENDLOOP.

  " Update headers with timestamp and STATUS
  LOOP AT p_header_table ASSIGNING <fs_header>.
    <fs_header>-status = 'ERROR'.
    <fs_header>-changed_date = sy-datum.
    <fs_header>-changed_time = sy-uzeit.
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

  " Save to database
*  IF p_items_table IS NOT INITIAL.
*    MODIFY zmm_sst_dtts_itm FROM TABLE p_items_table.
*  ENDIF.
*
*  IF p_header_table IS NOT INITIAL.
*    MODIFY zmm_sst_dtts_hdr FROM TABLE p_header_table.
*  ENDIF.

ENDFORM.



*&---------------------------------------------------------------------*
*& Form  HANDLE_API_ERROR_MULTIPLE
*&---------------------------------------------------------------------*
FORM handle_api_error_multiple USING p_exception TYPE REF TO cx_ai_system_fault
                               CHANGING p_items_table TYPE table
                                           p_header_table TYPE table.

  DATA: lv_sys_error  TYPE string,
        lv_mpl_id     TYPE string,
        lv_error_code TYPE string.

  FIELD-SYMBOLS: <fs_item>   TYPE zmm_sst_dtts_itm,
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
    <fs_item>-trans_stat  = lv_sys_error.
    " Update item timestamp
    <fs_item>-changed_date = sy-datum.
    <fs_item>-changed_time = sy-uzeit.
    <fs_item>-changed_by   = sy-uname.
  ENDLOOP.

  "  Update headers
  LOOP AT p_header_table ASSIGNING <fs_header>.
    <fs_header>-status = 'ERROR'.
    <fs_header>-changed_date = sy-datum.
    <fs_header>-changed_time = sy-uzeit.
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

  " Save  error records to database
  MODIFY zmm_sst_dtts_itm FROM TABLE p_items_table.
  MODIFY zmm_sst_dtts_hdr FROM TABLE p_header_table.

ENDFORM.

*&---------------------------------------------------------------------*
*& Form  HANDLE_GENERIC_ERROR_MULTIPLE
*&---------------------------------------------------------------------*
FORM handle_generic_error_multiple USING p_exception TYPE REF TO cx_root
                                  CHANGING p_items_table TYPE table
                                           p_header_table TYPE table.


  DATA: lv_root_error TYPE string.

  FIELD-SYMBOLS: <fs_item>   TYPE zmm_sst_dtts_itm,
                 <fs_header> TYPE zmm_sst_dtts_hdr.

  " Get error message
  lv_root_error = p_exception->get_text( ).

  " Update ALL items with generic error
  LOOP AT p_items_table ASSIGNING <fs_item>.
    <fs_item>-tr_response = 'ERROR'.
    <fs_item>-prod_stat = 'ERROR'.

    "  Update item timestamp
    <fs_item>-changed_date = sy-datum.
    <fs_item>-changed_time = sy-uzeit.
    <fs_item>-changed_by   = sy-uname.
  ENDLOOP.

  " Update headers
  LOOP AT p_header_table ASSIGNING <fs_header>.
    <fs_header>-status = 'ERROR'.
    <fs_header>-changed_date = sy-datum.
    <fs_header>-changed_time = sy-uzeit.
    <fs_header>-changed_by   = sy-uname.
  ENDLOOP.

  " Save ALL  records
  MODIFY zmm_sst_dtts_itm FROM TABLE p_items_table.
  MODIFY zmm_sst_dtts_hdr FROM TABLE p_header_table.


ENDFORM.

*&---------------------------------------------------------------------*
*& Form  FORMAT_DATA
*&---------------------------------------------------------------------*
FORM format_data USING p_gtin_in TYPE any
                       p_quantity_in TYPE any
                       p_batch_in TYPE any
                       p_exp_date_in TYPE any
                 CHANGING p_gtin_out TYPE string
                          p_quantity_out TYPE string
                          p_batch_out TYPE string
                          p_exp_date_out TYPE string.

  DATA: lv_len      TYPE i,
        lv_qty_int  TYPE string,
        lv_qty_dec  TYPE string,
        lv_year(4)  TYPE c,
        lv_month(2) TYPE c,
        lv_day(2)   TYPE c.

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
    lv_year  = p_exp_date_in+0(4).
    lv_month = p_exp_date_in+4(2).
    lv_day   = p_exp_date_in+6(2).
    p_exp_date_out = |{ lv_year }-{ lv_month }-{ lv_day }|.
  ENDIF.

ENDFORM.
*&---------------------------------------------------------------------*
*& Form  GET_ERROR_DESCRIPTION
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
```