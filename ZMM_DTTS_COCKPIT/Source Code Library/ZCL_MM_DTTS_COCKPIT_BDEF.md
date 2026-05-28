```abap
CLASS zcl_mm_dtts_cockpit_bdef DEFINITION PUBLIC ABSTRACT FINAL FOR BEHAVIOR OF zr_mm_dtts_cockpit.
ENDCLASS.

CLASS zcl_mm_dtts_cockpit_bdef IMPLEMENTATION.
ENDCLASS.

" Global buffer to hold unmanaged changes for the save sequence
CLASS lcl_buffer DEFINITION.
  PUBLIC SECTION.
    CLASS-DATA: mt_create TYPE TABLE OF zmm_sst_dttsit2,
                mt_update TYPE TABLE OF zmm_sst_dttsit2.
ENDCLASS.
CLASS lcl_buffer IMPLEMENTATION.
ENDCLASS.

CLASS lhc_Item DEFINITION INHERITING FROM cl_abap_behavior_handler.
  PRIVATE SECTION.

    TYPES: BEGIN OF ty_key,
             docyear TYPE mjahr,
             matdoc TYPE mblnr,
             mvttype TYPE bwart,
             itemno TYPE numc4,
           END OF ty_key.
    TYPES: tt_keys TYPE STANDARD TABLE OF ty_key WITH DEFAULT KEY.
    TYPES: tt_dttsit2 TYPE STANDARD TABLE OF zmm_sst_dttsit2 WITH DEFAULT KEY.

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

    METHODS execute_reprocess IMPORTING it_keys TYPE tt_keys
                              EXPORTING et_update_buffer TYPE tt_dttsit2.

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
    " Unmanaged create logic mapped to buffer
    LOOP AT entities INTO DATA(ls_entity).
      DATA(ls_dttsit2) = VALUE zmm_sst_dttsit2(
        mandt     = sy-mandt
        mat_doc   = ls_entity-matdoc
        mvt_type  = ls_entity-mvttype
        item_no   = ls_entity-itemno
        tran_id   = ls_entity-tranid
        zeile     = ls_entity-zeile
        product   = ls_entity-product
        prod_name = ls_entity-prodname
        prod_qty  = ls_entity-prodqty
        prod_unit = ls_entity-produnit
        gtin      = ls_entity-gtin
        batch     = ls_entity-batch
        exp_date  = ls_entity-expdate
        notif_id  = ls_entity-notifid
        tr_response = ls_entity-trresponse
        sr_number = ls_entity-srnumber
        created_date = sy-datum
        created_time = sy-uzeit
        created_by   = sy-uname
        prod_stat = ls_entity-prodstat
        trans_stat = ls_entity-transstat
        operation = ls_entity-operation
        frm_gln = ls_entity-frm_gln
        to_gln = ls_entity-to_gln
      ).
      APPEND ls_dttsit2 TO lcl_buffer=>mt_create.
    ENDLOOP.
  ENDMETHOD.

  METHOD update.
    " Unmanaged update logic captured to buffer
    DATA lt_keys_to_reprocess TYPE tt_keys.

    LOOP AT entities INTO DATA(ls_entity).
      " Because the draft/RAP operates on logical keys (docyear, matdoc, mvttype, itemno),
      " but the DB table zmm_sst_dttsit2 uses (tran_id, item_no), we must resolve the mapping.

      " Read base data using logical keys from CDS view
      SELECT SINGLE tran_id FROM zr_mm_dtts_cockpit INTO @DATA(lv_tran_id)
        WHERE docyear = @ls_entity-docyear AND matdoc = @ls_entity-matdoc AND mvttype = @ls_entity-mvttype AND itemno = @ls_entity-itemno.

      IF sy-subrc = 0.
        SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @DATA(ls_dttsit2)
          WHERE tran_id = @lv_tran_id AND item_no = @ls_entity-itemno.

        IF sy-subrc <> 0.
          " If not in buffer table, read full base from CDS to initialize
          SELECT SINGLE * FROM zr_mm_dtts_cockpit INTO @DATA(ls_base)
            WHERE docyear = @ls_entity-docyear AND matdoc = @ls_entity-matdoc AND mvttype = @ls_entity-mvttype AND itemno = @ls_entity-itemno.

          IF sy-subrc = 0.
            ls_dttsit2-mandt = sy-mandt.
            ls_dttsit2-tran_id = ls_base-tranid.
            ls_dttsit2-item_no = ls_base-itemno.
            ls_dttsit2-mat_doc = ls_base-matdoc.
            ls_dttsit2-mvt_type = ls_base-mvttype.
            ls_dttsit2-zeile = ls_base-zeile.
            ls_dttsit2-product = ls_base-product.
            ls_dttsit2-prod_name = ls_base-prodname.
            ls_dttsit2-prod_qty = ls_base-prodqty.
            ls_dttsit2-prod_unit = ls_base-produnit.
            ls_dttsit2-gtin = ls_base-gtin.
            ls_dttsit2-batch = ls_base-batch.
            ls_dttsit2-exp_date = ls_base-expdate.
            ls_dttsit2-notif_id = ls_base-notifid.
            ls_dttsit2-tr_response = ls_base-trresponse.
            ls_dttsit2-sr_number = ls_base-srnumber.
            ls_dttsit2-created_date = ls_base-createddate.
            ls_dttsit2-created_time = ls_base-createdtime.
            ls_dttsit2-created_by = ls_base-createdby.
            ls_dttsit2-prod_stat = ls_base-prodstat.
            ls_dttsit2-trans_stat = ls_base-transstat.
            ls_dttsit2-operation = ls_base-operation.
            ls_dttsit2-frm_gln = ls_base-frm_gln.
            ls_dttsit2-to_gln = ls_base-to_gln.

            APPEND ls_dttsit2 TO lcl_buffer=>mt_create.
          ENDIF.
        ENDIF.

        " Map incoming edits
        IF ls_entity-%control-gtin = if_abap_behv=>mk-on.
          ls_dttsit2-gtin = ls_entity-gtin.
        ENDIF.
        IF ls_entity-%control-prodqty = if_abap_behv=>mk-on.
          ls_dttsit2-prod_qty = ls_entity-prodqty.
        ENDIF.
        IF ls_entity-%control-batch = if_abap_behv=>mk-on.
          ls_dttsit2-batch = ls_entity-batch.
        ENDIF.
        IF ls_entity-%control-expdate = if_abap_behv=>mk-on.
          ls_dttsit2-exp_date = ls_entity-expdate.
        ENDIF.
        IF ls_entity-%control-frm_gln = if_abap_behv=>mk-on.
          ls_dttsit2-frm_gln = ls_entity-frm_gln.
        ENDIF.
        IF ls_entity-%control-to_gln = if_abap_behv=>mk-on.
          ls_dttsit2-to_gln = ls_entity-to_gln.
        ENDIF.

        ls_dttsit2-changed_date = sy-datum.
        ls_dttsit2-changed_time = sy-uzeit.
        ls_dttsit2-changed_by = sy-uname.

        " Append/Merge
        READ TABLE lcl_buffer=>mt_create ASSIGNING FIELD-SYMBOL(<fs_create>) WITH KEY tran_id = ls_dttsit2-tran_id item_no = ls_dttsit2-item_no.
        IF sy-subrc = 0.
          <fs_create> = ls_dttsit2.
        ELSE.
          APPEND ls_dttsit2 TO lcl_buffer=>mt_update.
        ENDIF.

        APPEND VALUE #( docyear = ls_entity-docyear matdoc = ls_entity-matdoc mvttype = ls_entity-mvttype itemno = ls_entity-itemno ) TO lt_keys_to_reprocess.
      ENDIF.
    ENDLOOP.

    " Execute API Reprocessing for modified keys
    IF lt_keys_to_reprocess IS NOT INITIAL.
       DATA lt_processed_updates TYPE tt_dttsit2.
       me->execute_reprocess( EXPORTING it_keys = lt_keys_to_reprocess
                              IMPORTING et_update_buffer = lt_processed_updates ).

       LOOP AT lt_processed_updates INTO DATA(ls_proc).
         READ TABLE lcl_buffer=>mt_update ASSIGNING FIELD-SYMBOL(<fs_buf>) WITH KEY tran_id = ls_proc-tran_id item_no = ls_proc-item_no.
         IF sy-subrc = 0.
            <fs_buf>-notif_id = ls_proc-notif_id.
            <fs_buf>-tr_response = ls_proc-tr_response.
            <fs_buf>-prod_stat = ls_proc-prod_stat.
            <fs_buf>-trans_stat = ls_proc-trans_stat.
            <fs_buf>-changed_date = ls_proc-changed_date.
            <fs_buf>-changed_time = ls_proc-changed_time.
            <fs_buf>-changed_by = ls_proc-changed_by.
         ELSE.
            READ TABLE lcl_buffer=>mt_create ASSIGNING <fs_create> WITH KEY tran_id = ls_proc-tran_id item_no = ls_proc-item_no.
            IF sy-subrc = 0.
               <fs_create>-notif_id = ls_proc-notif_id.
               <fs_create>-tr_response = ls_proc-tr_response.
               <fs_create>-prod_stat = ls_proc-prod_stat.
               <fs_create>-trans_stat = ls_proc-trans_stat.
               <fs_create>-changed_date = ls_proc-changed_date.
               <fs_create>-changed_time = ls_proc-changed_time.
               <fs_create>-changed_by = ls_proc-changed_by.
            ELSE.
               APPEND ls_proc TO lcl_buffer=>mt_update.
            ENDIF.
         ENDIF.
       ENDLOOP.
    ENDIF.
  ENDMETHOD.

  METHOD delete.
  ENDMETHOD.

  METHOD read.
    DATA: lt_read_data TYPE TABLE OF zr_mm_dtts_cockpit.

    IF keys IS NOT INITIAL.
      SELECT * FROM zr_mm_dtts_cockpit
        FOR ALL ENTRIES IN @keys
        WHERE docyear = @keys-docyear
          AND matdoc = @keys-matdoc
          AND mvttype = @keys-mvttype
          AND itemno = @keys-itemno
        INTO CORRESPONDING FIELDS OF TABLE @lt_read_data.

      IF sy-subrc = 0.
        LOOP AT lt_read_data INTO DATA(ls_read_data).
          INSERT VALUE #( %tky = VALUE #( docyear = ls_read_data-docyear matdoc = ls_read_data-matdoc mvttype = ls_read_data-mvttype itemno = ls_read_data-itemno )
                          %data = CORRESPONDING #( ls_read_data ) ) INTO TABLE result.
        ENDLOOP.
      ENDIF.
    ENDIF.
  ENDMETHOD.

  METHOD lock.
  ENDMETHOD.

  METHOD reprocess.
     DATA lt_keys_to_reprocess TYPE tt_keys.
     LOOP AT keys INTO DATA(ls_key).
       APPEND VALUE #( docyear = ls_key-docyear matdoc = ls_key-matdoc mvttype = ls_key-mvttype itemno = ls_key-itemno ) TO lt_keys_to_reprocess.
     ENDLOOP.

     DATA lt_processed_updates TYPE tt_dttsit2.

     me->execute_reprocess( EXPORTING it_keys = lt_keys_to_reprocess
                            IMPORTING et_update_buffer = lt_processed_updates ).

     LOOP AT lt_processed_updates INTO DATA(ls_proc).
         READ TABLE lcl_buffer=>mt_update ASSIGNING FIELD-SYMBOL(<fs_buf>) WITH KEY tran_id = ls_proc-tran_id item_no = ls_proc-item_no.
         IF sy-subrc = 0.
            <fs_buf>-notif_id = ls_proc-notif_id.
            <fs_buf>-tr_response = ls_proc-tr_response.
            <fs_buf>-prod_stat = ls_proc-prod_stat.
            <fs_buf>-trans_stat = ls_proc-trans_stat.
            <fs_buf>-changed_date = ls_proc-changed_date.
            <fs_buf>-changed_time = ls_proc-changed_time.
            <fs_buf>-changed_by = ls_proc-changed_by.
         ELSE.
            APPEND ls_proc TO lcl_buffer=>mt_update.
         ENDIF.
     ENDLOOP.

     READ ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
       ENTITY Item
       ALL FIELDS WITH CORRESPONDING #( keys )
       RESULT DATA(lt_updated_items).

     result = VALUE #( FOR ls_updated IN lt_updated_items
                       ( %tky = ls_updated-%tky
                         %param = ls_updated ) ).
  ENDMETHOD.

  METHOD execute_reprocess.
    TYPES: BEGIN OF ty_header_key,
             docyear TYPE mjahr,
             matdoc TYPE mblnr,
           END OF ty_header_key.
    DATA: lt_header_keys TYPE TABLE OF ty_header_key.

    LOOP AT it_keys INTO DATA(ls_key).
      APPEND VALUE #( docyear = ls_key-docyear matdoc = ls_key-matdoc ) TO lt_header_keys.
    ENDLOOP.
    SORT lt_header_keys BY docyear matdoc.
    DELETE ADJACENT DUPLICATES FROM lt_header_keys.

    DATA: lt_header  TYPE TABLE OF zmm_sst_dtts_hdr,
          lt_items   TYPE TABLE FOR READ RESULT zr_mm_dtts_cockpit.

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

    LOOP AT lt_header_keys INTO DATA(ls_hdr_key).
      CLEAR: lt_header, lt_items.

      LOOP AT it_keys INTO DATA(ls_k) WHERE docyear = ls_hdr_key-docyear AND matdoc = ls_hdr_key-matdoc.
        DATA ls_item_st TYPE STRUCTURE FOR READ RESULT zr_mm_dtts_cockpit\\Item.

        " Fetch logical-to-physical tran_id
        SELECT SINGLE tran_id FROM zr_mm_dtts_cockpit INTO @DATA(lv_t)
          WHERE docyear = @ls_k-docyear AND matdoc = @ls_k-matdoc AND mvttype = @ls_k-mvttype AND itemno = @ls_k-itemno.

        READ TABLE lcl_buffer=>mt_create INTO DATA(ls_buf) WITH KEY tran_id = lv_t item_no = ls_k-itemno.
        IF sy-subrc = 0.
           ls_item_st = CORRESPONDING #( ls_buf MAPPING matdoc = mat_doc mvttype = mvt_type itemno = item_no tranid = tran_id prodqty = prod_qty expdate = exp_date ).
           ls_item_st-docyear = ls_k-docyear. " Force mapped key
           APPEND ls_item_st TO lt_items.
        ELSE.
           READ TABLE lcl_buffer=>mt_update INTO ls_buf WITH KEY tran_id = lv_t item_no = ls_k-itemno.
           IF sy-subrc = 0.
             ls_item_st = CORRESPONDING #( ls_buf MAPPING matdoc = mat_doc mvttype = mvt_type itemno = item_no tranid = tran_id prodqty = prod_qty expdate = exp_date ).
             ls_item_st-docyear = ls_k-docyear.
             APPEND ls_item_st TO lt_items.
           ELSE.
             SELECT SINGLE * FROM zr_mm_dtts_cockpit INTO @DATA(ls_db)
               WHERE docyear = @ls_k-docyear AND matdoc = @ls_k-matdoc AND mvttype = @ls_k-mvttype AND itemno = @ls_k-itemno.
             IF sy-subrc = 0.
               ls_item_st = CORRESPONDING #( ls_db ).
               APPEND ls_item_st TO lt_items.
             ENDIF.
           ENDIF.
        ENDIF.
      ENDLOOP.

      IF lt_items IS NOT INITIAL.
        DATA(lv_tran_id) = lt_items[ 1 ]-tranid.

        IF lv_tran_id IS NOT INITIAL.
          SELECT * FROM zmm_sst_dtts_hdr INTO TABLE @lt_header
            WHERE tran_id = @lv_tran_id.
        ENDIF.

        DATA lv_operation TYPE string.
        IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-operation IS NOT INITIAL.
          lv_operation = lt_header[ 1 ]-operation.
        ELSE.
          lv_operation = lt_items[ 1 ]-operation.
        ENDIF.

        SELECT SINGLE * FROM zmm_dtts_api_con INTO @wa_zmm_dtts_api_con
          WHERE api_name = @lv_operation.

        IF sy-subrc = 0.
          CREATE DATA request_ptr TYPE (wa_zmm_dtts_api_con-request_structure).
          ASSIGN request_ptr->* TO <fs_request>.

          CREATE DATA response_ptr TYPE (wa_zmm_dtts_api_con-response_structure).
          ASSIGN response_ptr->* TO <fs_response>.

          CASE lv_operation.
            WHEN 'ACCEPT'.
              ASSIGN COMPONENT 'ACCEPT_BATCH_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_accept_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_accept_req> TO FIELD-SYMBOL(<lv_fromgln>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_accept_req> TO FIELD-SYMBOL(<lv_authgln>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_accept_req> TO FIELD-SYMBOL(<fs_prod_list>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list> TO <lt_products>.
                   IF sy-subrc = 0.

                      DATA lo_table_desc TYPE REF TO cl_abap_tabledescr.
                      DATA lo_line_desc TYPE REF TO cl_abap_datadescr.
                      DATA dref_line TYPE REF TO data.

                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item).
                            DATA lv_gtin_formatted TYPE string.
                            DATA lv_qty_formatted TYPE string.
                            DATA lv_batch_formatted TYPE string.
                            DATA lv_exp_formatted TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item-gtin ) p_quantity_in = CONV #( ls_item-prodqty ) p_batch_in = CONV #( ls_item-batch ) p_exp_date_in = CONV #( ls_item-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted p_quantity_out = lv_qty_formatted p_batch_out = lv_batch_formatted p_exp_date_out = lv_exp_formatted ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
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
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.
            WHEN OTHERS.
          ENDCASE.

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

                               DATA ls_processed_dttsit2 TYPE zmm_sst_dttsit2.

                               SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item>-tranid AND item_no = @<fs_item>-itemno.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item>-tranid.
                               ls_processed_dttsit2-item_no = <fs_item>-itemno.
                               ls_processed_dttsit2-notif_id = <lv_notif_id>.
                               ls_processed_dttsit2-tr_response = <r_rc>.

                               IF <r_rc> = '00000'.
                                 ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE.
                                 ls_processed_dttsit2-prod_stat = 'ERROR'.
                                 lv_all_success = abap_false.
                               ENDIF.

                               DATA lv_desc TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc> ) IMPORTING p_description = lv_desc ).
                               ls_processed_dttsit2-trans_stat = lv_desc.
                               ls_processed_dttsit2-changed_date = sy-datum.
                               ls_processed_dttsit2-changed_time = sy-uzeit.
                               ls_processed_dttsit2-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2 TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.
              ENDCASE.

            CATCH cx_ai_application_fault INTO DATA(lx_app_fault).
               LOOP AT lt_items ASSIGNING <fs_item>.
                 DATA ls_err_app TYPE zmm_sst_dttsit2.
                 ls_err_app-tran_id = <fs_item>-tranid.
                 ls_err_app-item_no = <fs_item>-itemno.
                 ls_err_app-prod_stat = 'ERROR'.
                 ls_err_app-trans_stat = 'API Application Fault'.
                 ls_err_app-changed_date = sy-datum.
                 ls_err_app-changed_time = sy-uzeit.
                 ls_err_app-changed_by = sy-uname.
                 APPEND ls_err_app TO et_update_buffer.
               ENDLOOP.
            CATCH cx_ai_system_fault INTO DATA(lx_sys).
               LOOP AT lt_items ASSIGNING <fs_item>.
                 DATA ls_err_sys TYPE zmm_sst_dttsit2.
                 ls_err_sys-tran_id = <fs_item>-tranid.
                 ls_err_sys-item_no = <fs_item>-itemno.
                 ls_err_sys-prod_stat = 'ERROR'.
                 ls_err_sys-trans_stat = 'API System Fault'.
                 ls_err_sys-changed_date = sy-datum.
                 ls_err_sys-changed_time = sy-uzeit.
                 ls_err_sys-changed_by = sy-uname.
                 APPEND ls_err_sys TO et_update_buffer.
               ENDLOOP.
            CATCH cx_root INTO DATA(lx_root).
               LOOP AT lt_items ASSIGNING <fs_item>.
                 DATA ls_err_root TYPE zmm_sst_dttsit2.
                 ls_err_root-tran_id = <fs_item>-tranid.
                 ls_err_root-item_no = <fs_item>-itemno.
                 ls_err_root-prod_stat = 'ERROR'.
                 ls_err_root-trans_stat = 'Generic API Error'.
                 ls_err_root-changed_date = sy-datum.
                 ls_err_root-changed_time = sy-uzeit.
                 ls_err_root-changed_by = sy-uname.
                 APPEND ls_err_root TO et_update_buffer.
               ENDLOOP.
          ENDTRY.
        ENDIF.
      ENDIF.
    ENDLOOP.

  ENDMETHOD.

  METHOD createWithPopup.
    " Generate new Entity via Factory Action mapped to EML Buffer Update
    DATA: lt_create TYPE TABLE FOR CREATE zr_mm_dtts_cockpit.

    LOOP AT keys INTO DATA(ls_key).
      DATA(ls_param) = ls_key-%param.

      DATA lv_doc_year TYPE mjahr.
      DATA lv_mat_doc TYPE mblnr.
      DATA lv_mvt_type TYPE bwart.
      DATA lv_item_no TYPE numc4.

      lv_doc_year = sy-datum(4).
      " In a real scenario, call a number range function module here.
      " Using timestamp-based generation for safe demo compilation.
      GET TIME STAMP FIELD DATA(lv_ts).
      lv_mat_doc = CONV mblnr( lv_ts ).
      lv_mvt_type = '101'.

      " Randomize item for uniqueness in factory
      CALL FUNCTION 'QF05_RANDOM_INTEGER'
        EXPORTING ran_int_max = 9999 ran_int_min = 1
        IMPORTING ran_int = DATA(lv_ran).
      lv_item_no = CONV numc4( lv_ran ).

      APPEND VALUE #( %cid = ls_key-%cid
                      docyear = lv_doc_year
                      matdoc = lv_mat_doc
                      mvttype = lv_mvt_type
                      itemno = lv_item_no
                      tranid = CONV ztran_id( lv_ts )
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
      CREATE FIELDS ( docyear matdoc mvttype itemno tranid gtin prodqty batch expdate prodstat createddate createdtime createdby )
      WITH lt_create
      MAPPED DATA(ls_mapped)
      FAILED DATA(ls_failed)
      REPORTED DATA(ls_reported).

    mapped-item = ls_mapped-item.
  ENDMETHOD.

  METHOD format_data.
    DATA: lv_len      TYPE i,
          lv_qty_int  TYPE string,
          lv_qty_dec  TYPE string,
          lv_year(4)  TYPE c,
          lv_month(2) TYPE c,
          lv_day(2)   TYPE c.

    p_gtin_out = p_gtin_in.
    CONDENSE p_gtin_out NO-GAPS.
    lv_len = strlen( p_gtin_out ).
    IF lv_len < 14.
      p_gtin_out = |{ p_gtin_out WIDTH = 14 PAD = '0' ALIGN = RIGHT }|.
    ENDIF.

    p_quantity_out = p_quantity_in.
    IF p_quantity_out CS '.'.
      SPLIT p_quantity_out AT '.' INTO lv_qty_int lv_qty_dec.
      p_quantity_out = lv_qty_int.
    ENDIF.
    p_quantity_out = |{ p_quantity_out ALPHA = OUT }|.
    CONDENSE p_quantity_out NO-GAPS.

    p_batch_out = p_batch_in.
    CONDENSE p_batch_out NO-GAPS.

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
     IF lcl_buffer=>mt_create IS NOT INITIAL.
       INSERT zmm_sst_dttsit2 FROM TABLE lcl_buffer=>mt_create.
     ENDIF.

     IF lcl_buffer=>mt_update IS NOT INITIAL.
       MODIFY zmm_sst_dttsit2 FROM TABLE lcl_buffer=>mt_update.
     ENDIF.
  ENDMETHOD.

  METHOD cleanup.
     CLEAR lcl_buffer=>mt_create.
     CLEAR lcl_buffer=>mt_update.
  ENDMETHOD.

  METHOD cleanup_finalize.
  ENDMETHOD.

ENDCLASS.
```
