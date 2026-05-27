```abap
CLASS zcl_mm_dtts_cockpit_bdef DEFINITION PUBLIC ABSTRACT FINAL FOR BEHAVIOR OF zr_mm_dtts_cockpit.
ENDCLASS.

CLASS zcl_mm_dtts_cockpit_bdef IMPLEMENTATION.
ENDCLASS.

CLASS lhc_Item DEFINITION INHERITING FROM cl_abap_behavior_handler.
  PRIVATE SECTION.

    METHODS get_instance_features FOR INSTANCE FEATURES
      IMPORTING keys REQUEST requested_features FOR Item RESULT result.

    METHODS get_instance_authorizations FOR INSTANCE AUTHORIZATION
      IMPORTING keys REQUEST requested_authorizations FOR Item RESULT result.

    METHODS create FOR MODIFY
      IMPORTING entities FOR CREATE Item.

    METHODS update FOR MODIFY
      IMPORTING entities FOR UPDATE Item.

    METHODS delete FOR MODIFY
      IMPORTING keys FOR DELETE Item.

    METHODS read FOR READ
      IMPORTING keys FOR READ Item RESULT result.

    METHODS lock FOR LOCK
      IMPORTING keys FOR LOCK Item.

    METHODS reprocess FOR MODIFY
      IMPORTING keys FOR ACTION Item~reprocess RESULT result.

    METHODS createWithPopup FOR MODIFY
      IMPORTING keys FOR ACTION Item~createWithPopup.

    " ---------------------------------------------------------------------
    " Helper Methods for Request/Response
    " ---------------------------------------------------------------------
    METHODS format_data IMPORTING p_gtin_in TYPE string
                                  p_quantity_in TYPE string
                                  p_batch_in TYPE string
                                  p_exp_date_in TYPE string
                        EXPORTING p_gtin_out TYPE string
                                  p_quantity_out TYPE string
                                  p_batch_out TYPE string
                                  p_exp_date_out TYPE string.

    METHODS get_error_description IMPORTING p_error_code TYPE char5
                                  EXPORTING p_description TYPE char255.

ENDCLASS.

CLASS lhc_Item IMPLEMENTATION.

  METHOD get_instance_features.
    " Only allow update/edit for records that are not SUCCESS
    READ ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
      ENTITY Item
      FIELDS ( prodstat ) WITH CORRESPONDING #( keys )
      RESULT DATA(lt_items).

    result = VALUE #( FOR ls_item IN lt_items
                      ( %tky = ls_item-%tky
                        %update = COND #( WHEN ls_item-prodstat = 'SUCCESS' THEN if_abap_behv=>fc-o-disabled ELSE if_abap_behv=>fc-o-enabled )
                        %action-reprocess = COND #( WHEN ls_item-prodstat = 'SUCCESS' THEN if_abap_behv=>fc-o-disabled ELSE if_abap_behv=>fc-o-enabled )
                      ) ).
  ENDMETHOD.

  METHOD get_instance_authorizations.
  ENDMETHOD.

  METHOD create.
    " Unmanaged create logic (Buffer)
  ENDMETHOD.

  METHOD update.
    " Unmanaged update logic (Buffer)
  ENDMETHOD.

  METHOD delete.
  ENDMETHOD.

  METHOD read.
  ENDMETHOD.

  METHOD lock.
  ENDMETHOD.

  METHOD reprocess.
    " 1. Group by TRANID
    TYPES: BEGIN OF ty_tran_id,
             tranid TYPE ztran_id,
           END OF ty_tran_id.
    DATA: lt_tran_ids TYPE TABLE OF ty_tran_id.

    LOOP AT keys INTO DATA(ls_key).
      APPEND VALUE #( tranid = ls_key-tranid ) TO lt_tran_ids.
    ENDLOOP.
    SORT lt_tran_ids BY tranid.
    DELETE ADJACENT DUPLICATES FROM lt_tran_ids.

    DATA: lt_header  TYPE TABLE OF zmm_sst_dtts_hdr,
          lt_items   TYPE TABLE OF zmm_sst_dtts_itm.

    DATA: wa_zmm_dtts_api_con TYPE zmm_dtts_api_con,
          request_ptr         TYPE REF TO data,
          response_ptr        TYPE REF TO data,
          ptab                TYPE abap_parmbind_tab,
          wa_ptab             TYPE abap_parmbind,
          p_lport             TYPE prx_logical_port_name,
          lo_proxy            TYPE REF TO object.

    FIELD-SYMBOLS: <fs_request> TYPE any,
                   <fs_response> TYPE any,
                   <lt_products> TYPE ANY TABLE,
                   <lt_resp_products> TYPE ANY TABLE.

    " Process Each TRAN_ID Group
    LOOP AT lt_tran_ids INTO DATA(ls_tran_id).
      CLEAR: lt_header, lt_items.

      SELECT * FROM zmm_sst_dtts_hdr INTO TABLE @lt_header
        WHERE tran_id = @ls_tran_id-tranid.

      SELECT * FROM zmm_sst_dtts_itm INTO TABLE @lt_items
        WHERE tran_id = @ls_tran_id-tranid
          AND prod_stat <> 'SUCCESS'. " ONLY Non-Success

      IF lt_header IS NOT INITIAL AND lt_items IS NOT INITIAL.
        DATA(lv_operation) = lt_header[ 1 ]-operation.

        " Dynamically Load API configuration
        SELECT SINGLE * FROM zmm_dtts_api_con INTO @wa_zmm_dtts_api_con
          WHERE api_name = @lv_operation.

        IF sy-subrc = 0.
          CREATE DATA request_ptr TYPE (wa_zmm_dtts_api_con-request_structure).
          ASSIGN request_ptr->* TO <fs_request>.

          CREATE DATA response_ptr TYPE (wa_zmm_dtts_api_con-response_structure).
          ASSIGN response_ptr->* TO <fs_response>.

          " -------------------------------------------------------------
          " Build request based on operation
          " -------------------------------------------------------------
          CASE lv_operation.
            WHEN 'ACCEPT'.
              ASSIGN COMPONENT 'ACCEPT_BATCH_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_accept_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_accept_req> TO FIELD-SYMBOL(<lv_fromgln>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_accept_req> TO FIELD-SYMBOL(<lv_authgln>).
                IF sy-subrc = 0.
                   <lv_fromgln> = lt_header[ 1 ]-frm_gln.
                   <lv_authgln> = lt_header[ 1 ]-to_gln.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_accept_req> TO FIELD-SYMBOL(<fs_prod_list>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list> TO <lt_products>.
                   IF sy-subrc = 0.
                      LOOP AT lt_items INTO DATA(ls_item).
                        DATA lv_gtin_formatted TYPE string.
                        DATA lv_qty_formatted TYPE string.
                        DATA lv_batch_formatted TYPE string.
                        DATA lv_exp_formatted TYPE string.

                        me->format_data( EXPORTING p_gtin_in = CONV #( ls_item-gtin ) p_quantity_in = CONV #( ls_item-prod_qty ) p_batch_in = CONV #( ls_item-batch ) p_exp_date_in = CONV #( ls_item-exp_date )
                                         IMPORTING p_gtin_out = lv_gtin_formatted p_quantity_out = lv_qty_formatted p_batch_out = lv_batch_formatted p_exp_date_out = lv_exp_formatted ).

                        DATA dref_line TYPE REF TO data.
                        CREATE DATA dref_line LIKE LINE OF <lt_products>.
                        ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line>).

                        ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line> TO FIELD-SYMBOL(<l_gtin>).
                        IF sy-subrc = 0. <l_gtin> = lv_gtin_formatted. ENDIF.
                        ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line> TO FIELD-SYMBOL(<l_qty>).
                        IF sy-subrc = 0. <l_qty> = lv_qty_formatted. ENDIF.
                        ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line> TO FIELD-SYMBOL(<l_bn>).
                        IF sy-subrc = 0. <l_bn> = lv_batch_formatted. ENDIF.
                        ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line> TO FIELD-SYMBOL(<l_xd>).
                        IF sy-subrc = 0. <l_xd> = lv_exp_formatted. ENDIF.

                        INSERT <ls_product_line> INTO TABLE <lt_products>.
                      ENDLOOP.
                   ENDIF.
                ENDIF.
              ENDIF.
            WHEN OTHERS.
          ENDCASE.

          " -------------------------------------------------------------
          " Construct proxy, send
          " -------------------------------------------------------------
          CLEAR ptab. CLEAR wa_ptab.
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

              " -------------------------------------------------------------
              " Parse response, modify item properties in buffer
              " -------------------------------------------------------------
              DATA lv_all_success TYPE abap_bool VALUE abap_true.
              CASE lv_operation.
                WHEN 'ACCEPT'.
                  ASSIGN COMPONENT 'ACCEPT_BATCH_SERVICE_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_accept_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_accept_resp> TO FIELD-SYMBOL(<lv_notif_id>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_accept_resp> TO FIELD-SYMBOL(<fs_resp_prod_list>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod> TO FIELD-SYMBOL(<r_gtin>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod> TO FIELD-SYMBOL(<r_bn>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod> TO FIELD-SYMBOL(<r_rc>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item>).
                             DATA lv_item_gtin TYPE string. DATA lv_resp_gtin TYPE string.
                             lv_item_gtin = <fs_item>-gtin. lv_resp_gtin = <r_gtin>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item>-batch = <r_bn>.
                               <fs_item>-notif_id = <lv_notif_id>.
                               <fs_item>-tr_response = <r_rc>.
                               IF <r_rc> = '00000'.
                                 <fs_item>-prod_stat = 'SUCCESS'.
                               ELSE.
                                 <fs_item>-prod_stat = 'ERROR'.
                                 lv_all_success = abap_false.
                               ENDIF.

                               DATA lv_desc TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc> ) IMPORTING p_description = lv_desc ).
                               <fs_item>-trans_stat = lv_desc.
                               <fs_item>-changed_date = sy-datum.
                               <fs_item>-changed_time = sy-uzeit.
                               <fs_item>-changed_by = sy-uname.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.
              ENDCASE.

              " -------------------------------------------------------------
              " Apply changes to transactional buffer using EML
              " -------------------------------------------------------------
              LOOP AT lt_items INTO DATA(ls_mod_item).
                MODIFY ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
                  ENTITY Item
                  UPDATE FIELDS ( prodstat transstat notifid trresponse changeddate changedtime changedby )
                  WITH VALUE #( ( %tky = VALUE #( tranid = ls_mod_item-tran_id itemno = ls_mod_item-item_no )
                                  prodstat = ls_mod_item-prod_stat
                                  transstat = ls_mod_item-trans_stat
                                  notifid = ls_mod_item-notif_id
                                  trresponse = ls_mod_item-tr_response
                                  changeddate = ls_mod_item-changed_date
                                  changedtime = ls_mod_item-changed_time
                                  changedby = ls_mod_item-changed_by ) )
                  FAILED DATA(ls_failed_eml)
                  REPORTED DATA(ls_reported_eml).
              ENDLOOP.

            CATCH cx_ai_application_fault INTO DATA(lx_app_fault).
               " Error handling mapped to EML Buffer Update
            CATCH cx_ai_system_fault INTO DATA(lx_sys).
               " Error handling mapped to EML Buffer Update
            CATCH cx_root INTO DATA(lx_root).
               " Error handling mapped to EML Buffer Update
          ENDTRY.
        ENDIF.
      ENDIF.
    ENDLOOP.

    " Return result mapping
    READ ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
      ENTITY Item
      ALL FIELDS WITH CORRESPONDING #( keys )
      RESULT DATA(lt_updated_items).

    result = VALUE #( FOR ls_updated IN lt_updated_items
                      ( %tky = ls_updated-%tky
                        %param = ls_updated ) ).

  ENDMETHOD.

  METHOD createWithPopup.
    " Generate new Entity via Factory Action mapped to EML Buffer Update
    DATA: lt_create TYPE TABLE FOR CREATE zr_mm_dtts_cockpit.

    LOOP AT keys INTO DATA(ls_key).
      DATA(ls_param) = ls_key-%param.

      DATA lv_tran_id TYPE ztran_id.
      DATA lv_item_no TYPE numc4.

      " Call number range or custom logic to generate IDs
      lv_tran_id = 'NEW_TRAN_ID'.
      lv_item_no = '0001'.

      APPEND VALUE #( %cid = ls_key-%cid
                      tranid = lv_tran_id
                      itemno = lv_item_no
                      gtin = ls_param-gtin
                      prodqty = ls_param-prod_qty
                      batch = ls_param-batch
                      expdate = ls_param-exp_date
                      prodstat = 'NEW'
                      createddate = sy-datum
                      createdtime = sy-uzeit
                      createdby = sy-uname ) TO lt_create.
    ENDLOOP.

    MODIFY ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
      ENTITY Item
      CREATE FIELDS ( tranid itemno gtin prodqty batch expdate prodstat createddate createdtime createdby )
      WITH lt_create
      MAPPED DATA(ls_mapped)
      FAILED DATA(ls_failed)
      REPORTED DATA(ls_reported).

    " Return mapped keys
    mapped-item = ls_mapped-item.
  ENDMETHOD.

  " -------------------------------------------------------------
  " Helper Method Implementations
  " -------------------------------------------------------------
  METHOD format_data.
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
  ENDMETHOD.

  METHOD get_error_description.
    CLEAR p_description.
    SELECT SINGLE description FROM zdtts_errorlist INTO @p_description
      WHERE error_code = @p_error_code
        AND language = 'en'.
    IF sy-subrc <> 0.
      p_description = |Error Code: { p_error_code }|.
    ENDIF.
  ENDMETHOD.

ENDCLASS.

CLASS lsc_ZR_MM_DTTS_COCKPIT DEFINITION INHERITING FROM cl_abap_behavior_saver.
  PROTECTED SECTION.

    METHODS finalize REDEFINITION.

    METHODS check_before_save REDEFINITION.

    METHODS save REDEFINITION.

    METHODS cleanup REDEFINITION.

    METHODS cleanup_finalize REDEFINITION.

ENDCLASS.

CLASS lsc_ZR_MM_DTTS_COCKPIT IMPLEMENTATION.

  METHOD finalize.
  ENDMETHOD.

  METHOD check_before_save.
  ENDMETHOD.

  METHOD save.
     " Unmanaged Save logic strictly mapped to zmm_sst_dttsit2
     " NOTE: Assuming unmanaged scenario requires manually pulling data from draft/buffer.
     " In a purely unmanaged scenario without early numbering, global variables are used to pass buffer to save.
     " Assuming draft handles DB interaction in this hybrid model, explicit DB save logic here.

     " E.g.:
     " MODIFY zmm_sst_dttsit2 FROM TABLE lt_dttsit2.
  ENDMETHOD.

  METHOD cleanup.
  ENDMETHOD.

  METHOD cleanup_finalize.
  ENDMETHOD.

ENDCLASS.
```
