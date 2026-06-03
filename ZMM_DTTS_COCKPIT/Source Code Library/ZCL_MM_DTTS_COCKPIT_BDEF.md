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

    METHODS populate_full_error_record IMPORTING is_item TYPE STRUCTURE FOR READ RESULT zr_mm_dtts_cockpit\\Item
                                                 iv_trans_stat TYPE string
                                                 it_header TYPE ANY TABLE
                                       RETURNING VALUE(rs_err) TYPE zmm_sst_dttsit2.

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

            " Fetch Header Fields
            SELECT SINGLE operation, frm_gln, to_gln FROM zmm_sst_dtts_hdr INTO (@ls_dttsit2-operation, @ls_dttsit2-frm_gln, @ls_dttsit2-to_gln)
              WHERE mat_doc = @ls_entity-matdoc AND doc_yr = @ls_entity-docyear AND mvt_type = @ls_entity-mvttype.

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
            " Ensure all specified fields are overwritten in the buffer from the execute_reprocess result
            <fs_buf>-zeile = ls_proc-zeile.
            <fs_buf>-product = ls_proc-product.
            <fs_buf>-prod_name = ls_proc-prod_name.
            <fs_buf>-prod_qty = ls_proc-prod_qty.
            <fs_buf>-prod_unit = ls_proc-prod_unit.
            <fs_buf>-gtin = ls_proc-gtin.
            <fs_buf>-batch = ls_proc-batch.
            <fs_buf>-exp_date = ls_proc-exp_date.
            <fs_buf>-notif_id = ls_proc-notif_id.
            <fs_buf>-tr_response = ls_proc-tr_response.
            <fs_buf>-mat_doc = ls_proc-mat_doc.
            <fs_buf>-mvt_type = ls_proc-mvt_type.
            <fs_buf>-operation = ls_proc-operation.
            <fs_buf>-frm_gln = ls_proc-frm_gln.
            <fs_buf>-to_gln = ls_proc-to_gln.

            <fs_buf>-prod_stat = ls_proc-prod_stat.
            <fs_buf>-trans_stat = ls_proc-trans_stat.
            <fs_buf>-changed_date = ls_proc-changed_date.
            <fs_buf>-changed_time = ls_proc-changed_time.
            <fs_buf>-changed_by = ls_proc-changed_by.
         ELSE.
            READ TABLE lcl_buffer=>mt_create ASSIGNING <fs_create> WITH KEY tran_id = ls_proc-tran_id item_no = ls_proc-item_no.
            IF sy-subrc = 0.
               <fs_create>-zeile = ls_proc-zeile.
               <fs_create>-product = ls_proc-product.
               <fs_create>-prod_name = ls_proc-prod_name.
               <fs_create>-prod_qty = ls_proc-prod_qty.
               <fs_create>-prod_unit = ls_proc-prod_unit.
               <fs_create>-gtin = ls_proc-gtin.
               <fs_create>-batch = ls_proc-batch.
               <fs_create>-exp_date = ls_proc-exp_date.
               <fs_create>-notif_id = ls_proc-notif_id.
               <fs_create>-tr_response = ls_proc-tr_response.
               <fs_create>-mat_doc = ls_proc-mat_doc.
               <fs_create>-mvt_type = ls_proc-mvt_type.
               <fs_create>-operation = ls_proc-operation.
               <fs_create>-frm_gln = ls_proc-frm_gln.
               <fs_create>-to_gln = ls_proc-to_gln.

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
            <fs_buf>-zeile = ls_proc-zeile.
            <fs_buf>-product = ls_proc-product.
            <fs_buf>-prod_name = ls_proc-prod_name.
            <fs_buf>-prod_qty = ls_proc-prod_qty.
            <fs_buf>-prod_unit = ls_proc-prod_unit.
            <fs_buf>-gtin = ls_proc-gtin.
            <fs_buf>-batch = ls_proc-batch.
            <fs_buf>-exp_date = ls_proc-exp_date.
            <fs_buf>-notif_id = ls_proc-notif_id.
            <fs_buf>-tr_response = ls_proc-tr_response.
            <fs_buf>-mat_doc = ls_proc-mat_doc.
            <fs_buf>-mvt_type = ls_proc-mvt_type.
            <fs_buf>-operation = ls_proc-operation.
            <fs_buf>-frm_gln = ls_proc-frm_gln.
            <fs_buf>-to_gln = ls_proc-to_gln.

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

  METHOD populate_full_error_record.
     " Helper to preserve all fields when an API exception occurs so we don't wipe data in ZMM_SST_DTTSIT2
     SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @rs_err
       WHERE tran_id = @is_item-tranid AND item_no = @is_item-itemno.

     rs_err-mandt = sy-mandt.
     rs_err-tran_id = is_item-tranid.
     rs_err-item_no = is_item-itemno.
     rs_err-zeile = is_item-zeile.
     rs_err-product = is_item-product.
     rs_err-prod_name = is_item-prodname.
     rs_err-prod_qty = is_item-prodqty.
     rs_err-prod_unit = is_item-produnit.
     rs_err-gtin = is_item-gtin.
     rs_err-batch = is_item-batch.
     rs_err-exp_date = is_item-expdate.
     rs_err-mat_doc = is_item-matdoc.
     rs_err-mvt_type = is_item-mvttype.

     IF it_header IS NOT INITIAL.
       ASSIGN it_header[ 1 ] TO FIELD-SYMBOL(<fs_hdr>).
       IF sy-subrc = 0.
         ASSIGN COMPONENT 'OPERATION' OF STRUCTURE <fs_hdr> TO FIELD-SYMBOL(<op>).
         IF sy-subrc = 0. rs_err-operation = <op>. ENDIF.
         ASSIGN COMPONENT 'FRM_GLN' OF STRUCTURE <fs_hdr> TO FIELD-SYMBOL(<fg>).
         IF sy-subrc = 0. rs_err-frm_gln = <fg>. ENDIF.
         ASSIGN COMPONENT 'TO_GLN' OF STRUCTURE <fs_hdr> TO FIELD-SYMBOL(<tg>).
         IF sy-subrc = 0. rs_err-to_gln = <tg>. ENDIF.
       ENDIF.
     ENDIF.

     rs_err-prod_stat = 'ERROR'.
     rs_err-trans_stat = iv_trans_stat.
     rs_err-changed_date = sy-datum.
     rs_err-changed_time = sy-uzeit.
     rs_err-changed_by = sy-uname.
  ENDMETHOD.

  METHOD execute_reprocess.
    TYPES: BEGIN OF ty_header_key,
             docyear TYPE mjahr,
             matdoc TYPE mblnr,
             mvttype TYPE bwart,
           END OF ty_header_key.
    DATA: lt_header_keys TYPE TABLE OF ty_header_key.

    LOOP AT it_keys INTO DATA(ls_key).
      APPEND VALUE #( docyear = ls_key-docyear matdoc = ls_key-matdoc mvttype = ls_key-mvttype ) TO lt_header_keys.
    ENDLOOP.
    SORT lt_header_keys BY docyear matdoc mvttype.
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

      LOOP AT it_keys INTO DATA(ls_k) WHERE docyear = ls_hdr_key-docyear AND matdoc = ls_hdr_key-matdoc AND mvttype = ls_hdr_key-mvttype.
        DATA ls_item_st TYPE STRUCTURE FOR READ RESULT zr_mm_dtts_cockpit\\Item.

        " Fetch logical-to-physical tran_id
        SELECT SINGLE tran_id FROM zr_mm_dtts_cockpit INTO @DATA(lv_t)
          WHERE docyear = @ls_k-docyear AND matdoc = @ls_k-matdoc AND mvttype = @ls_k-mvttype AND itemno = @ls_k-itemno.

        READ TABLE lcl_buffer=>mt_create INTO DATA(ls_buf) WITH KEY tran_id = lv_t item_no = ls_k-itemno.
        IF sy-subrc = 0.
           ls_item_st = CORRESPONDING #( ls_buf MAPPING matdoc = mat_doc mvttype = mvt_type itemno = item_no tranid = tran_id prodname = prod_name prodqty = prod_qty produnit = prod_unit expdate = exp_date notifid = notif_id trresponse = tr_response srnumber = sr_number createddate = created_date createdtime = created_time createdby = created_by changeddate = changed_date changedtime = changed_time changedby = changed_by prodstat = prod_stat transstat = trans_stat ).
           ls_item_st-docyear = ls_k-docyear. " Force mapped key
           APPEND ls_item_st TO lt_items.
        ELSE.
           READ TABLE lcl_buffer=>mt_update INTO ls_buf WITH KEY tran_id = lv_t item_no = ls_k-itemno.
           IF sy-subrc = 0.
             ls_item_st = CORRESPONDING #( ls_buf MAPPING matdoc = mat_doc mvttype = mvt_type itemno = item_no tranid = tran_id prodname = prod_name prodqty = prod_qty produnit = prod_unit expdate = exp_date notifid = notif_id trresponse = tr_response srnumber = sr_number createddate = created_date createdtime = created_time createdby = created_by changeddate = changed_date changedtime = changed_time changedby = changed_by prodstat = prod_stat transstat = trans_stat ).
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
        SELECT * FROM zmm_sst_dtts_hdr INTO TABLE @lt_header
          WHERE mat_doc = @ls_hdr_key-matdoc AND doc_yr = @ls_hdr_key-docyear AND mvt_type = @ls_hdr_key-mvttype.

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

            WHEN 'RETURN'.
              ASSIGN COMPONENT 'RETURN_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_return_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<lv_fromgln_return>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_return> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_return> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<lv_togln_return>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_return> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_return> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<lv_authgln_return>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_return> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_return> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<fs_prod_list_return>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_return> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_return).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_return-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_return TYPE string. DATA lv_qty_f_return TYPE string. DATA lv_batch_f_return TYPE string. DATA lv_exp_f_return TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_return-gtin ) p_quantity_in = CONV #( ls_item_return-prodqty ) p_batch_in = CONV #( ls_item_return-batch ) p_exp_date_in = CONV #( ls_item_return-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_return p_quantity_out = lv_qty_f_return p_batch_out = lv_batch_f_return p_exp_date_out = lv_exp_f_return ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_return>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_gtin_return>).
                            IF sy-subrc = 0. <l_gtin_return> = lv_gtin_f_return. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_qty_return>).
                            IF sy-subrc = 0. <l_qty_return> = lv_qty_f_return. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_bn_return>).
                            IF sy-subrc = 0. <l_bn_return> = lv_batch_f_return. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_xd_return>).
                            IF sy-subrc = 0. <l_xd_return> = lv_exp_f_return. ENDIF.

                            INSERT <ls_product_line_return> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DISPATCH'.
              ASSIGN COMPONENT 'DISPATCH_BATCH_SERVICE_REQUE3' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_dispatch_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<lv_fromgln_dispatch>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_dispatch> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_dispatch> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<lv_togln_dispatch>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_dispatch> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_dispatch> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<lv_authgln_dispatch>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_dispatch> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_dispatch> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<fs_prod_list_dispatch>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_dispatch> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_dispatch).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_dispatch-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_dispatch TYPE string. DATA lv_qty_f_dispatch TYPE string. DATA lv_batch_f_dispatch TYPE string. DATA lv_exp_f_dispatch TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_dispatch-gtin ) p_quantity_in = CONV #( ls_item_dispatch-prodqty ) p_batch_in = CONV #( ls_item_dispatch-batch ) p_exp_date_in = CONV #( ls_item_dispatch-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_dispatch p_quantity_out = lv_qty_f_dispatch p_batch_out = lv_batch_f_dispatch p_exp_date_out = lv_exp_f_dispatch ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_dispatch>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_gtin_dispatch>).
                            IF sy-subrc = 0. <l_gtin_dispatch> = lv_gtin_f_dispatch. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_qty_dispatch>).
                            IF sy-subrc = 0. <l_qty_dispatch> = lv_qty_f_dispatch. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_bn_dispatch>).
                            IF sy-subrc = 0. <l_bn_dispatch> = lv_batch_f_dispatch. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_xd_dispatch>).
                            IF sy-subrc = 0. <l_xd_dispatch> = lv_exp_f_dispatch. ENDIF.

                            INSERT <ls_product_line_dispatch> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DISPATCH_CANCEL'.
              ASSIGN COMPONENT 'DISPATCH_CANCEL_SERVICE_REQUE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_dispatch_cancel_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_dispatch_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_dispatch_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_dispatch_cancel> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<lv_togln_dispatch_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_dispatch_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_dispatch_cancel> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<lv_authgln_dispatch_cancel>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_dispatch_cancel> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_dispatch_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_dispatch_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_dispatch_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_dispatch_cancel).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_dispatch_cancel-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_dispatch_cancel TYPE string. DATA lv_qty_f_dispatch_cancel TYPE string. DATA lv_batch_f_dispatch_cancel TYPE string. DATA lv_exp_f_dispatch_cancel TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_dispatch_cancel-gtin ) p_quantity_in = CONV #( ls_item_dispatch_cancel-prodqty ) p_batch_in = CONV #( ls_item_dispatch_cancel-batch ) p_exp_date_in = CONV #( ls_item_dispatch_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_dispatch_cancel p_quantity_out = lv_qty_f_dispatch_cancel p_batch_out = lv_batch_f_dispatch_cancel p_exp_date_out = lv_exp_f_dispatch_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_dispatch_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_gtin_dispatch_cancel>).
                            IF sy-subrc = 0. <l_gtin_dispatch_cancel> = lv_gtin_f_dispatch_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_qty_dispatch_cancel>).
                            IF sy-subrc = 0. <l_qty_dispatch_cancel> = lv_qty_f_dispatch_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_bn_dispatch_cancel>).
                            IF sy-subrc = 0. <l_bn_dispatch_cancel> = lv_batch_f_dispatch_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_xd_dispatch_cancel>).
                            IF sy-subrc = 0. <l_xd_dispatch_cancel> = lv_exp_f_dispatch_cancel. ENDIF.

                            INSERT <ls_product_line_dispatch_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'TRANSFER'.
              ASSIGN COMPONENT 'TRANSFER_BATCH_SERVICE_REQUES' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_transfer_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<lv_fromgln_transfer>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_transfer> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_transfer> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<lv_togln_transfer>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_transfer> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_transfer> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<lv_authgln_transfer>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_transfer> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_transfer> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<fs_prod_list_transfer>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_transfer> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_transfer).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_transfer-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_transfer TYPE string. DATA lv_qty_f_transfer TYPE string. DATA lv_batch_f_transfer TYPE string. DATA lv_exp_f_transfer TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_transfer-gtin ) p_quantity_in = CONV #( ls_item_transfer-prodqty ) p_batch_in = CONV #( ls_item_transfer-batch ) p_exp_date_in = CONV #( ls_item_transfer-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_transfer p_quantity_out = lv_qty_f_transfer p_batch_out = lv_batch_f_transfer p_exp_date_out = lv_exp_f_transfer ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_transfer>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_gtin_transfer>).
                            IF sy-subrc = 0. <l_gtin_transfer> = lv_gtin_f_transfer. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_qty_transfer>).
                            IF sy-subrc = 0. <l_qty_transfer> = lv_qty_f_transfer. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_bn_transfer>).
                            IF sy-subrc = 0. <l_bn_transfer> = lv_batch_f_transfer. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_xd_transfer>).
                            IF sy-subrc = 0. <l_xd_transfer> = lv_exp_f_transfer. ENDIF.

                            INSERT <ls_product_line_transfer> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'TRANSFER_CANCEL'.
              ASSIGN COMPONENT 'TRANSFER_CANCEL_SERVICE_REQUE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_transfer_cancel_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_transfer_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_transfer_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_transfer_cancel> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<lv_togln_transfer_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_transfer_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_transfer_cancel> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<lv_authgln_transfer_cancel>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_transfer_cancel> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_transfer_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_transfer_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_transfer_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_transfer_cancel).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_transfer_cancel-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_transfer_cancel TYPE string. DATA lv_qty_f_transfer_cancel TYPE string. DATA lv_batch_f_transfer_cancel TYPE string. DATA lv_exp_f_transfer_cancel TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_transfer_cancel-gtin ) p_quantity_in = CONV #( ls_item_transfer_cancel-prodqty ) p_batch_in = CONV #( ls_item_transfer_cancel-batch ) p_exp_date_in = CONV #( ls_item_transfer_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_transfer_cancel p_quantity_out = lv_qty_f_transfer_cancel p_batch_out = lv_batch_f_transfer_cancel p_exp_date_out = lv_exp_f_transfer_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_transfer_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_gtin_transfer_cancel>).
                            IF sy-subrc = 0. <l_gtin_transfer_cancel> = lv_gtin_f_transfer_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_qty_transfer_cancel>).
                            IF sy-subrc = 0. <l_qty_transfer_cancel> = lv_qty_f_transfer_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_bn_transfer_cancel>).
                            IF sy-subrc = 0. <l_bn_transfer_cancel> = lv_batch_f_transfer_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_xd_transfer_cancel>).
                            IF sy-subrc = 0. <l_xd_transfer_cancel> = lv_exp_f_transfer_cancel. ENDIF.

                            INSERT <ls_product_line_transfer_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'CONSUME'.
              ASSIGN COMPONENT 'CONSUME_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_consume_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<lv_fromgln_consume>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_consume> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_consume> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<lv_togln_consume>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_consume> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_consume> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<lv_authgln_consume>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_consume> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_consume> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<fs_prod_list_consume>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_consume> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_consume).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_consume-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_consume TYPE string. DATA lv_qty_f_consume TYPE string. DATA lv_batch_f_consume TYPE string. DATA lv_exp_f_consume TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_consume-gtin ) p_quantity_in = CONV #( ls_item_consume-prodqty ) p_batch_in = CONV #( ls_item_consume-batch ) p_exp_date_in = CONV #( ls_item_consume-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_consume p_quantity_out = lv_qty_f_consume p_batch_out = lv_batch_f_consume p_exp_date_out = lv_exp_f_consume ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_consume>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_gtin_consume>).
                            IF sy-subrc = 0. <l_gtin_consume> = lv_gtin_f_consume. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_qty_consume>).
                            IF sy-subrc = 0. <l_qty_consume> = lv_qty_f_consume. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_bn_consume>).
                            IF sy-subrc = 0. <l_bn_consume> = lv_batch_f_consume. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_xd_consume>).
                            IF sy-subrc = 0. <l_xd_consume> = lv_exp_f_consume. ENDIF.

                            INSERT <ls_product_line_consume> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'CONSUME_CANCEL'.
              ASSIGN COMPONENT 'CONSUME_CANCEL_SERVICE_REQUES' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_consume_cancel_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_consume_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_consume_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_consume_cancel> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<lv_togln_consume_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_consume_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_consume_cancel> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<lv_authgln_consume_cancel>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_consume_cancel> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_consume_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_consume_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_consume_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_consume_cancel).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_consume_cancel-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_consume_cancel TYPE string. DATA lv_qty_f_consume_cancel TYPE string. DATA lv_batch_f_consume_cancel TYPE string. DATA lv_exp_f_consume_cancel TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_consume_cancel-gtin ) p_quantity_in = CONV #( ls_item_consume_cancel-prodqty ) p_batch_in = CONV #( ls_item_consume_cancel-batch ) p_exp_date_in = CONV #( ls_item_consume_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_consume_cancel p_quantity_out = lv_qty_f_consume_cancel p_batch_out = lv_batch_f_consume_cancel p_exp_date_out = lv_exp_f_consume_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_consume_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_gtin_consume_cancel>).
                            IF sy-subrc = 0. <l_gtin_consume_cancel> = lv_gtin_f_consume_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_qty_consume_cancel>).
                            IF sy-subrc = 0. <l_qty_consume_cancel> = lv_qty_f_consume_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_bn_consume_cancel>).
                            IF sy-subrc = 0. <l_bn_consume_cancel> = lv_batch_f_consume_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_xd_consume_cancel>).
                            IF sy-subrc = 0. <l_xd_consume_cancel> = lv_exp_f_consume_cancel. ENDIF.

                            INSERT <ls_product_line_consume_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DRUG_SALE'.
              ASSIGN COMPONENT 'PHARMACY_SALE_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_drug_sale_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<lv_fromgln_drug_sale>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_drug_sale> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_drug_sale> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<lv_togln_drug_sale>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_drug_sale> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_drug_sale> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<lv_authgln_drug_sale>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_drug_sale> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_drug_sale> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<fs_prod_list_drug_sale>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_drug_sale> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_drug_sale).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_drug_sale-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_drug_sale TYPE string. DATA lv_qty_f_drug_sale TYPE string. DATA lv_batch_f_drug_sale TYPE string. DATA lv_exp_f_drug_sale TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_drug_sale-gtin ) p_quantity_in = CONV #( ls_item_drug_sale-prodqty ) p_batch_in = CONV #( ls_item_drug_sale-batch ) p_exp_date_in = CONV #( ls_item_drug_sale-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_drug_sale p_quantity_out = lv_qty_f_drug_sale p_batch_out = lv_batch_f_drug_sale p_exp_date_out = lv_exp_f_drug_sale ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_drug_sale>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_gtin_drug_sale>).
                            IF sy-subrc = 0. <l_gtin_drug_sale> = lv_gtin_f_drug_sale. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_qty_drug_sale>).
                            IF sy-subrc = 0. <l_qty_drug_sale> = lv_qty_f_drug_sale. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_bn_drug_sale>).
                            IF sy-subrc = 0. <l_bn_drug_sale> = lv_batch_f_drug_sale. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_xd_drug_sale>).
                            IF sy-subrc = 0. <l_xd_drug_sale> = lv_exp_f_drug_sale. ENDIF.

                            INSERT <ls_product_line_drug_sale> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DRUG_SALE_CANCEL'.
              ASSIGN COMPONENT 'PHARMACY_SALE_CANCEL_SERVICE2' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_drug_sale_cancel_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_drug_sale_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_drug_sale_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_drug_sale_cancel> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<lv_togln_drug_sale_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_drug_sale_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_drug_sale_cancel> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<lv_authgln_drug_sale_cancel>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_drug_sale_cancel> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_drug_sale_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_drug_sale_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_drug_sale_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_drug_sale_cancel).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_drug_sale_cancel-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_drug_sale_cancel TYPE string. DATA lv_qty_f_drug_sale_cancel TYPE string. DATA lv_batch_f_drug_sale_cancel TYPE string. DATA lv_exp_f_drug_sale_cancel TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_drug_sale_cancel-gtin ) p_quantity_in = CONV #( ls_item_drug_sale_cancel-prodqty ) p_batch_in = CONV #( ls_item_drug_sale_cancel-batch ) p_exp_date_in = CONV #( ls_item_drug_sale_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_drug_sale_cancel p_quantity_out = lv_qty_f_drug_sale_cancel p_batch_out = lv_batch_f_drug_sale_cancel p_exp_date_out = lv_exp_f_drug_sale_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_drug_sale_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_gtin_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_gtin_drug_sale_cancel> = lv_gtin_f_drug_sale_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_qty_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_qty_drug_sale_cancel> = lv_qty_f_drug_sale_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_bn_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_bn_drug_sale_cancel> = lv_batch_f_drug_sale_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_xd_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_xd_drug_sale_cancel> = lv_exp_f_drug_sale_cancel. ENDIF.

                            INSERT <ls_product_line_drug_sale_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DEACTIVATE'.
              ASSIGN COMPONENT 'DEACTIVATE_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_deactivate_req>).
              IF sy-subrc = 0.
                " Assign GLNs based on typical structures. Adjust if some ops don't have them.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<lv_fromgln_deactivate>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_deactivate> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_deactivate> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<lv_togln_deactivate>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_deactivate> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_deactivate> = lt_header[ 1 ]-to_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<lv_authgln_deactivate>).
                IF sy-subrc = 0.
                   " Usually AUTHGLN logic varies. We will default to from_gln or header auth_gln
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_deactivate> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_deactivate> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<fs_prod_list_deactivate>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_deactivate> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_deactivate).
                            " Skip already success records just in case, though normally handled prior
                            IF ls_item_deactivate-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            DATA lv_gtin_f_deactivate TYPE string. DATA lv_qty_f_deactivate TYPE string. DATA lv_batch_f_deactivate TYPE string. DATA lv_exp_f_deactivate TYPE string.
                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_deactivate-gtin ) p_quantity_in = CONV #( ls_item_deactivate-prodqty ) p_batch_in = CONV #( ls_item_deactivate-batch ) p_exp_date_in = CONV #( ls_item_deactivate-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_f_deactivate p_quantity_out = lv_qty_f_deactivate p_batch_out = lv_batch_f_deactivate p_exp_date_out = lv_exp_f_deactivate ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_deactivate>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_gtin_deactivate>).
                            IF sy-subrc = 0. <l_gtin_deactivate> = lv_gtin_f_deactivate. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_qty_deactivate>).
                            IF sy-subrc = 0. <l_qty_deactivate> = lv_qty_f_deactivate. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_bn_deactivate>).
                            IF sy-subrc = 0. <l_bn_deactivate> = lv_batch_f_deactivate. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_xd_deactivate>).
                            IF sy-subrc = 0. <l_xd_deactivate> = lv_exp_f_deactivate. ENDIF.

                            INSERT <ls_product_line_deactivate> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'RETURN'.
              ASSIGN COMPONENT 'RETURN_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_return_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<lv_fromgln_return>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<lv_authgln_return>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_return> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_return> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_return> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_return> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<fs_prod_list_return>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_return> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_return).
                            DATA lv_gtin_formatted_return TYPE string.
                            DATA lv_qty_formatted_return TYPE string.
                            DATA lv_batch_formatted_return TYPE string.
                            DATA lv_exp_formatted_return TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_return-gtin ) p_quantity_in = CONV #( ls_item_return-prodqty ) p_batch_in = CONV #( ls_item_return-batch ) p_exp_date_in = CONV #( ls_item_return-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_return p_quantity_out = lv_qty_formatted_return p_batch_out = lv_batch_formatted_return p_exp_date_out = lv_exp_formatted_return ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_return>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_gtin_return>).
                            IF sy-subrc = 0. <l_gtin_return> = lv_gtin_formatted_return. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_qty_return>).
                            IF sy-subrc = 0. <l_qty_return> = lv_qty_formatted_return. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_bn_return>).
                            IF sy-subrc = 0. <l_bn_return> = lv_batch_formatted_return. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_xd_return>).
                            IF sy-subrc = 0. <l_xd_return> = lv_exp_formatted_return. ENDIF.

                            INSERT <ls_product_line_return> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DISPATCH'.
              ASSIGN COMPONENT 'DISPATCH_BATCH_SERVICE_REQUE3' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_dispatch_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<lv_fromgln_dispatch>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<lv_authgln_dispatch>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_dispatch> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_dispatch> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_dispatch> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_dispatch> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<fs_prod_list_dispatch>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_dispatch> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_dispatch).
                            DATA lv_gtin_formatted_dispatch TYPE string.
                            DATA lv_qty_formatted_dispatch TYPE string.
                            DATA lv_batch_formatted_dispatch TYPE string.
                            DATA lv_exp_formatted_dispatch TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_dispatch-gtin ) p_quantity_in = CONV #( ls_item_dispatch-prodqty ) p_batch_in = CONV #( ls_item_dispatch-batch ) p_exp_date_in = CONV #( ls_item_dispatch-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_dispatch p_quantity_out = lv_qty_formatted_dispatch p_batch_out = lv_batch_formatted_dispatch p_exp_date_out = lv_exp_formatted_dispatch ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_dispatch>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_gtin_dispatch>).
                            IF sy-subrc = 0. <l_gtin_dispatch> = lv_gtin_formatted_dispatch. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_qty_dispatch>).
                            IF sy-subrc = 0. <l_qty_dispatch> = lv_qty_formatted_dispatch. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_bn_dispatch>).
                            IF sy-subrc = 0. <l_bn_dispatch> = lv_batch_formatted_dispatch. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_xd_dispatch>).
                            IF sy-subrc = 0. <l_xd_dispatch> = lv_exp_formatted_dispatch. ENDIF.

                            INSERT <ls_product_line_dispatch> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DISPATCH_CANCEL'.
              ASSIGN COMPONENT 'DISPATCH_CANCEL_SERVICE_REQUE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_dispatch_cancel_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_dispatch_cancel>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<lv_authgln_dispatch_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_dispatch_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_dispatch_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_dispatch_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_dispatch_cancel> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_dispatch_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_dispatch_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_dispatch_cancel).
                            DATA lv_gtin_formatted_dispatch_cancel TYPE string.
                            DATA lv_qty_formatted_dispatch_cancel TYPE string.
                            DATA lv_batch_formatted_dispatch_cancel TYPE string.
                            DATA lv_exp_formatted_dispatch_cancel TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_dispatch_cancel-gtin ) p_quantity_in = CONV #( ls_item_dispatch_cancel-prodqty ) p_batch_in = CONV #( ls_item_dispatch_cancel-batch ) p_exp_date_in = CONV #( ls_item_dispatch_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_dispatch_cancel p_quantity_out = lv_qty_formatted_dispatch_cancel p_batch_out = lv_batch_formatted_dispatch_cancel p_exp_date_out = lv_exp_formatted_dispatch_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_dispatch_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_gtin_dispatch_cancel>).
                            IF sy-subrc = 0. <l_gtin_dispatch_cancel> = lv_gtin_formatted_dispatch_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_qty_dispatch_cancel>).
                            IF sy-subrc = 0. <l_qty_dispatch_cancel> = lv_qty_formatted_dispatch_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_bn_dispatch_cancel>).
                            IF sy-subrc = 0. <l_bn_dispatch_cancel> = lv_batch_formatted_dispatch_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_xd_dispatch_cancel>).
                            IF sy-subrc = 0. <l_xd_dispatch_cancel> = lv_exp_formatted_dispatch_cancel. ENDIF.

                            INSERT <ls_product_line_dispatch_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'TRANSFER'.
              ASSIGN COMPONENT 'TRANSFER_BATCH_SERVICE_REQUES' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_transfer_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<lv_fromgln_transfer>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<lv_authgln_transfer>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_transfer> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_transfer> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_transfer> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_transfer> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<fs_prod_list_transfer>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_transfer> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_transfer).
                            DATA lv_gtin_formatted_transfer TYPE string.
                            DATA lv_qty_formatted_transfer TYPE string.
                            DATA lv_batch_formatted_transfer TYPE string.
                            DATA lv_exp_formatted_transfer TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_transfer-gtin ) p_quantity_in = CONV #( ls_item_transfer-prodqty ) p_batch_in = CONV #( ls_item_transfer-batch ) p_exp_date_in = CONV #( ls_item_transfer-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_transfer p_quantity_out = lv_qty_formatted_transfer p_batch_out = lv_batch_formatted_transfer p_exp_date_out = lv_exp_formatted_transfer ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_transfer>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_gtin_transfer>).
                            IF sy-subrc = 0. <l_gtin_transfer> = lv_gtin_formatted_transfer. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_qty_transfer>).
                            IF sy-subrc = 0. <l_qty_transfer> = lv_qty_formatted_transfer. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_bn_transfer>).
                            IF sy-subrc = 0. <l_bn_transfer> = lv_batch_formatted_transfer. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_xd_transfer>).
                            IF sy-subrc = 0. <l_xd_transfer> = lv_exp_formatted_transfer. ENDIF.

                            INSERT <ls_product_line_transfer> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'TRANSFER_CANCEL'.
              ASSIGN COMPONENT 'TRANSFER_CANCEL_SERVICE_REQUE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_transfer_cancel_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_transfer_cancel>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<lv_authgln_transfer_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_transfer_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_transfer_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_transfer_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_transfer_cancel> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_transfer_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_transfer_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_transfer_cancel).
                            DATA lv_gtin_formatted_transfer_cancel TYPE string.
                            DATA lv_qty_formatted_transfer_cancel TYPE string.
                            DATA lv_batch_formatted_transfer_cancel TYPE string.
                            DATA lv_exp_formatted_transfer_cancel TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_transfer_cancel-gtin ) p_quantity_in = CONV #( ls_item_transfer_cancel-prodqty ) p_batch_in = CONV #( ls_item_transfer_cancel-batch ) p_exp_date_in = CONV #( ls_item_transfer_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_transfer_cancel p_quantity_out = lv_qty_formatted_transfer_cancel p_batch_out = lv_batch_formatted_transfer_cancel p_exp_date_out = lv_exp_formatted_transfer_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_transfer_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_gtin_transfer_cancel>).
                            IF sy-subrc = 0. <l_gtin_transfer_cancel> = lv_gtin_formatted_transfer_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_qty_transfer_cancel>).
                            IF sy-subrc = 0. <l_qty_transfer_cancel> = lv_qty_formatted_transfer_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_bn_transfer_cancel>).
                            IF sy-subrc = 0. <l_bn_transfer_cancel> = lv_batch_formatted_transfer_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_xd_transfer_cancel>).
                            IF sy-subrc = 0. <l_xd_transfer_cancel> = lv_exp_formatted_transfer_cancel. ENDIF.

                            INSERT <ls_product_line_transfer_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'CONSUME'.
              ASSIGN COMPONENT 'CONSUME_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_consume_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<lv_fromgln_consume>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<lv_authgln_consume>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_consume> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_consume> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_consume> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_consume> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<fs_prod_list_consume>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_consume> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_consume).
                            DATA lv_gtin_formatted_consume TYPE string.
                            DATA lv_qty_formatted_consume TYPE string.
                            DATA lv_batch_formatted_consume TYPE string.
                            DATA lv_exp_formatted_consume TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_consume-gtin ) p_quantity_in = CONV #( ls_item_consume-prodqty ) p_batch_in = CONV #( ls_item_consume-batch ) p_exp_date_in = CONV #( ls_item_consume-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_consume p_quantity_out = lv_qty_formatted_consume p_batch_out = lv_batch_formatted_consume p_exp_date_out = lv_exp_formatted_consume ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_consume>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_gtin_consume>).
                            IF sy-subrc = 0. <l_gtin_consume> = lv_gtin_formatted_consume. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_qty_consume>).
                            IF sy-subrc = 0. <l_qty_consume> = lv_qty_formatted_consume. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_bn_consume>).
                            IF sy-subrc = 0. <l_bn_consume> = lv_batch_formatted_consume. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_xd_consume>).
                            IF sy-subrc = 0. <l_xd_consume> = lv_exp_formatted_consume. ENDIF.

                            INSERT <ls_product_line_consume> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'CONSUME_CANCEL'.
              ASSIGN COMPONENT 'CONSUME_CANCEL_SERVICE_REQUES' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_consume_cancel_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_consume_cancel>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<lv_authgln_consume_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_consume_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_consume_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_consume_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_consume_cancel> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_consume_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_consume_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_consume_cancel).
                            DATA lv_gtin_formatted_consume_cancel TYPE string.
                            DATA lv_qty_formatted_consume_cancel TYPE string.
                            DATA lv_batch_formatted_consume_cancel TYPE string.
                            DATA lv_exp_formatted_consume_cancel TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_consume_cancel-gtin ) p_quantity_in = CONV #( ls_item_consume_cancel-prodqty ) p_batch_in = CONV #( ls_item_consume_cancel-batch ) p_exp_date_in = CONV #( ls_item_consume_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_consume_cancel p_quantity_out = lv_qty_formatted_consume_cancel p_batch_out = lv_batch_formatted_consume_cancel p_exp_date_out = lv_exp_formatted_consume_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_consume_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_gtin_consume_cancel>).
                            IF sy-subrc = 0. <l_gtin_consume_cancel> = lv_gtin_formatted_consume_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_qty_consume_cancel>).
                            IF sy-subrc = 0. <l_qty_consume_cancel> = lv_qty_formatted_consume_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_bn_consume_cancel>).
                            IF sy-subrc = 0. <l_bn_consume_cancel> = lv_batch_formatted_consume_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_xd_consume_cancel>).
                            IF sy-subrc = 0. <l_xd_consume_cancel> = lv_exp_formatted_consume_cancel. ENDIF.

                            INSERT <ls_product_line_consume_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DRUG_SALE'.
              ASSIGN COMPONENT 'PHARMACY_SALE_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_drug_sale_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<lv_fromgln_drug_sale>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<lv_authgln_drug_sale>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_drug_sale> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_drug_sale> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_drug_sale> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_drug_sale> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<fs_prod_list_drug_sale>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_drug_sale> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_drug_sale).
                            DATA lv_gtin_formatted_drug_sale TYPE string.
                            DATA lv_qty_formatted_drug_sale TYPE string.
                            DATA lv_batch_formatted_drug_sale TYPE string.
                            DATA lv_exp_formatted_drug_sale TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_drug_sale-gtin ) p_quantity_in = CONV #( ls_item_drug_sale-prodqty ) p_batch_in = CONV #( ls_item_drug_sale-batch ) p_exp_date_in = CONV #( ls_item_drug_sale-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_drug_sale p_quantity_out = lv_qty_formatted_drug_sale p_batch_out = lv_batch_formatted_drug_sale p_exp_date_out = lv_exp_formatted_drug_sale ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_drug_sale>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_gtin_drug_sale>).
                            IF sy-subrc = 0. <l_gtin_drug_sale> = lv_gtin_formatted_drug_sale. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_qty_drug_sale>).
                            IF sy-subrc = 0. <l_qty_drug_sale> = lv_qty_formatted_drug_sale. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_bn_drug_sale>).
                            IF sy-subrc = 0. <l_bn_drug_sale> = lv_batch_formatted_drug_sale. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_xd_drug_sale>).
                            IF sy-subrc = 0. <l_xd_drug_sale> = lv_exp_formatted_drug_sale. ENDIF.

                            INSERT <ls_product_line_drug_sale> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DRUG_SALE_CANCEL'.
              ASSIGN COMPONENT 'PHARMACY_SALE_CANCEL_SERVICE2' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_drug_sale_cancel_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_drug_sale_cancel>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<lv_authgln_drug_sale_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_drug_sale_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_drug_sale_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_drug_sale_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_drug_sale_cancel> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_drug_sale_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_drug_sale_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_drug_sale_cancel).
                            DATA lv_gtin_formatted_drug_sale_cancel TYPE string.
                            DATA lv_qty_formatted_drug_sale_cancel TYPE string.
                            DATA lv_batch_formatted_drug_sale_cancel TYPE string.
                            DATA lv_exp_formatted_drug_sale_cancel TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_drug_sale_cancel-gtin ) p_quantity_in = CONV #( ls_item_drug_sale_cancel-prodqty ) p_batch_in = CONV #( ls_item_drug_sale_cancel-batch ) p_exp_date_in = CONV #( ls_item_drug_sale_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_drug_sale_cancel p_quantity_out = lv_qty_formatted_drug_sale_cancel p_batch_out = lv_batch_formatted_drug_sale_cancel p_exp_date_out = lv_exp_formatted_drug_sale_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_drug_sale_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_gtin_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_gtin_drug_sale_cancel> = lv_gtin_formatted_drug_sale_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_qty_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_qty_drug_sale_cancel> = lv_qty_formatted_drug_sale_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_bn_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_bn_drug_sale_cancel> = lv_batch_formatted_drug_sale_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_xd_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_xd_drug_sale_cancel> = lv_exp_formatted_drug_sale_cancel. ENDIF.

                            INSERT <ls_product_line_drug_sale_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DEACTIVATE'.
              ASSIGN COMPONENT 'DEACTIVATE_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_deactivate_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<lv_fromgln_deactivate>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<lv_authgln_deactivate>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_deactivate> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_deactivate> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln_deactivate> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_deactivate> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<fs_prod_list_deactivate>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_deactivate> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_deactivate).
                            DATA lv_gtin_formatted_deactivate TYPE string.
                            DATA lv_qty_formatted_deactivate TYPE string.
                            DATA lv_batch_formatted_deactivate TYPE string.
                            DATA lv_exp_formatted_deactivate TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_deactivate-gtin ) p_quantity_in = CONV #( ls_item_deactivate-prodqty ) p_batch_in = CONV #( ls_item_deactivate-batch ) p_exp_date_in = CONV #( ls_item_deactivate-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_deactivate p_quantity_out = lv_qty_formatted_deactivate p_batch_out = lv_batch_formatted_deactivate p_exp_date_out = lv_exp_formatted_deactivate ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_deactivate>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_gtin_deactivate>).
                            IF sy-subrc = 0. <l_gtin_deactivate> = lv_gtin_formatted_deactivate. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_qty_deactivate>).
                            IF sy-subrc = 0. <l_qty_deactivate> = lv_qty_formatted_deactivate. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_bn_deactivate>).
                            IF sy-subrc = 0. <l_bn_deactivate> = lv_batch_formatted_deactivate. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_xd_deactivate>).
                            IF sy-subrc = 0. <l_xd_deactivate> = lv_exp_formatted_deactivate. ENDIF.

                            INSERT <ls_product_line_deactivate> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'RETURN'.
              ASSIGN COMPONENT 'RETURN_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_return_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<lv_fromgln_return>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_return> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_return> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<lv_togln_return>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_return> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_return> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<lv_authgln_return>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_return> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_return> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_return_req> TO FIELD-SYMBOL(<fs_prod_list_return>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_return> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_return).
                            DATA lv_gtin_formatted_return TYPE string.
                            DATA lv_qty_formatted_return TYPE string.
                            DATA lv_batch_formatted_return TYPE string.
                            DATA lv_exp_formatted_return TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_return-gtin ) p_quantity_in = CONV #( ls_item_return-prodqty ) p_batch_in = CONV #( ls_item_return-batch ) p_exp_date_in = CONV #( ls_item_return-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_return p_quantity_out = lv_qty_formatted_return p_batch_out = lv_batch_formatted_return p_exp_date_out = lv_exp_formatted_return ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_return>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_gtin_return>).
                            IF sy-subrc = 0. <l_gtin_return> = lv_gtin_formatted_return. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_qty_return>).
                            IF sy-subrc = 0. <l_qty_return> = lv_qty_formatted_return. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_bn_return>).
                            IF sy-subrc = 0. <l_bn_return> = lv_batch_formatted_return. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_return> TO FIELD-SYMBOL(<l_xd_return>).
                            IF sy-subrc = 0. <l_xd_return> = lv_exp_formatted_return. ENDIF.

                            INSERT <ls_product_line_return> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DISPATCH'.
              ASSIGN COMPONENT 'DISPATCH_BATCH_SERVICE_REQUE3' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_dispatch_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<lv_fromgln_dispatch>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_dispatch> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_dispatch> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<lv_togln_dispatch>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_dispatch> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_dispatch> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<lv_authgln_dispatch>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_dispatch> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_dispatch> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_dispatch_req> TO FIELD-SYMBOL(<fs_prod_list_dispatch>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_dispatch> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_dispatch).
                            DATA lv_gtin_formatted_dispatch TYPE string.
                            DATA lv_qty_formatted_dispatch TYPE string.
                            DATA lv_batch_formatted_dispatch TYPE string.
                            DATA lv_exp_formatted_dispatch TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_dispatch-gtin ) p_quantity_in = CONV #( ls_item_dispatch-prodqty ) p_batch_in = CONV #( ls_item_dispatch-batch ) p_exp_date_in = CONV #( ls_item_dispatch-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_dispatch p_quantity_out = lv_qty_formatted_dispatch p_batch_out = lv_batch_formatted_dispatch p_exp_date_out = lv_exp_formatted_dispatch ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_dispatch>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_gtin_dispatch>).
                            IF sy-subrc = 0. <l_gtin_dispatch> = lv_gtin_formatted_dispatch. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_qty_dispatch>).
                            IF sy-subrc = 0. <l_qty_dispatch> = lv_qty_formatted_dispatch. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_bn_dispatch>).
                            IF sy-subrc = 0. <l_bn_dispatch> = lv_batch_formatted_dispatch. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_dispatch> TO FIELD-SYMBOL(<l_xd_dispatch>).
                            IF sy-subrc = 0. <l_xd_dispatch> = lv_exp_formatted_dispatch. ENDIF.

                            INSERT <ls_product_line_dispatch> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DISPATCH_CANCEL'.
              ASSIGN COMPONENT 'DISPATCH_CANCEL_SERVICE_REQUE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_dispatch_cancel_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_dispatch_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_dispatch_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_dispatch_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<lv_togln_dispatch_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_dispatch_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_dispatch_cancel> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<lv_authgln_dispatch_cancel>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_dispatch_cancel> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_dispatch_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_dispatch_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_dispatch_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_dispatch_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_dispatch_cancel).
                            DATA lv_gtin_formatted_dispatch_cancel TYPE string.
                            DATA lv_qty_formatted_dispatch_cancel TYPE string.
                            DATA lv_batch_formatted_dispatch_cancel TYPE string.
                            DATA lv_exp_formatted_dispatch_cancel TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_dispatch_cancel-gtin ) p_quantity_in = CONV #( ls_item_dispatch_cancel-prodqty ) p_batch_in = CONV #( ls_item_dispatch_cancel-batch ) p_exp_date_in = CONV #( ls_item_dispatch_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_dispatch_cancel p_quantity_out = lv_qty_formatted_dispatch_cancel p_batch_out = lv_batch_formatted_dispatch_cancel p_exp_date_out = lv_exp_formatted_dispatch_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_dispatch_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_gtin_dispatch_cancel>).
                            IF sy-subrc = 0. <l_gtin_dispatch_cancel> = lv_gtin_formatted_dispatch_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_qty_dispatch_cancel>).
                            IF sy-subrc = 0. <l_qty_dispatch_cancel> = lv_qty_formatted_dispatch_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_bn_dispatch_cancel>).
                            IF sy-subrc = 0. <l_bn_dispatch_cancel> = lv_batch_formatted_dispatch_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_dispatch_cancel> TO FIELD-SYMBOL(<l_xd_dispatch_cancel>).
                            IF sy-subrc = 0. <l_xd_dispatch_cancel> = lv_exp_formatted_dispatch_cancel. ENDIF.

                            INSERT <ls_product_line_dispatch_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'TRANSFER'.
              ASSIGN COMPONENT 'TRANSFER_BATCH_SERVICE_REQUES' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_transfer_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<lv_fromgln_transfer>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_transfer> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_transfer> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<lv_togln_transfer>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_transfer> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_transfer> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<lv_authgln_transfer>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_transfer> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_transfer> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_transfer_req> TO FIELD-SYMBOL(<fs_prod_list_transfer>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_transfer> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_transfer).
                            DATA lv_gtin_formatted_transfer TYPE string.
                            DATA lv_qty_formatted_transfer TYPE string.
                            DATA lv_batch_formatted_transfer TYPE string.
                            DATA lv_exp_formatted_transfer TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_transfer-gtin ) p_quantity_in = CONV #( ls_item_transfer-prodqty ) p_batch_in = CONV #( ls_item_transfer-batch ) p_exp_date_in = CONV #( ls_item_transfer-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_transfer p_quantity_out = lv_qty_formatted_transfer p_batch_out = lv_batch_formatted_transfer p_exp_date_out = lv_exp_formatted_transfer ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_transfer>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_gtin_transfer>).
                            IF sy-subrc = 0. <l_gtin_transfer> = lv_gtin_formatted_transfer. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_qty_transfer>).
                            IF sy-subrc = 0. <l_qty_transfer> = lv_qty_formatted_transfer. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_bn_transfer>).
                            IF sy-subrc = 0. <l_bn_transfer> = lv_batch_formatted_transfer. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_transfer> TO FIELD-SYMBOL(<l_xd_transfer>).
                            IF sy-subrc = 0. <l_xd_transfer> = lv_exp_formatted_transfer. ENDIF.

                            INSERT <ls_product_line_transfer> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'TRANSFER_CANCEL'.
              ASSIGN COMPONENT 'TRANSFER_CANCEL_SERVICE_REQUE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_transfer_cancel_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_transfer_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_transfer_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_transfer_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<lv_togln_transfer_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_transfer_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_transfer_cancel> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<lv_authgln_transfer_cancel>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_transfer_cancel> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_transfer_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_transfer_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_transfer_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_transfer_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_transfer_cancel).
                            DATA lv_gtin_formatted_transfer_cancel TYPE string.
                            DATA lv_qty_formatted_transfer_cancel TYPE string.
                            DATA lv_batch_formatted_transfer_cancel TYPE string.
                            DATA lv_exp_formatted_transfer_cancel TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_transfer_cancel-gtin ) p_quantity_in = CONV #( ls_item_transfer_cancel-prodqty ) p_batch_in = CONV #( ls_item_transfer_cancel-batch ) p_exp_date_in = CONV #( ls_item_transfer_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_transfer_cancel p_quantity_out = lv_qty_formatted_transfer_cancel p_batch_out = lv_batch_formatted_transfer_cancel p_exp_date_out = lv_exp_formatted_transfer_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_transfer_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_gtin_transfer_cancel>).
                            IF sy-subrc = 0. <l_gtin_transfer_cancel> = lv_gtin_formatted_transfer_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_qty_transfer_cancel>).
                            IF sy-subrc = 0. <l_qty_transfer_cancel> = lv_qty_formatted_transfer_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_bn_transfer_cancel>).
                            IF sy-subrc = 0. <l_bn_transfer_cancel> = lv_batch_formatted_transfer_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_transfer_cancel> TO FIELD-SYMBOL(<l_xd_transfer_cancel>).
                            IF sy-subrc = 0. <l_xd_transfer_cancel> = lv_exp_formatted_transfer_cancel. ENDIF.

                            INSERT <ls_product_line_transfer_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'CONSUME'.
              ASSIGN COMPONENT 'CONSUME_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_consume_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<lv_fromgln_consume>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_consume> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_consume> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<lv_togln_consume>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_consume> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_consume> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<lv_authgln_consume>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_consume> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_consume> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_consume_req> TO FIELD-SYMBOL(<fs_prod_list_consume>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_consume> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_consume).
                            DATA lv_gtin_formatted_consume TYPE string.
                            DATA lv_qty_formatted_consume TYPE string.
                            DATA lv_batch_formatted_consume TYPE string.
                            DATA lv_exp_formatted_consume TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_consume-gtin ) p_quantity_in = CONV #( ls_item_consume-prodqty ) p_batch_in = CONV #( ls_item_consume-batch ) p_exp_date_in = CONV #( ls_item_consume-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_consume p_quantity_out = lv_qty_formatted_consume p_batch_out = lv_batch_formatted_consume p_exp_date_out = lv_exp_formatted_consume ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_consume>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_gtin_consume>).
                            IF sy-subrc = 0. <l_gtin_consume> = lv_gtin_formatted_consume. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_qty_consume>).
                            IF sy-subrc = 0. <l_qty_consume> = lv_qty_formatted_consume. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_bn_consume>).
                            IF sy-subrc = 0. <l_bn_consume> = lv_batch_formatted_consume. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_consume> TO FIELD-SYMBOL(<l_xd_consume>).
                            IF sy-subrc = 0. <l_xd_consume> = lv_exp_formatted_consume. ENDIF.

                            INSERT <ls_product_line_consume> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'CONSUME_CANCEL'.
              ASSIGN COMPONENT 'CONSUME_CANCEL_SERVICE_REQUES' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_consume_cancel_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_consume_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_consume_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_consume_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<lv_togln_consume_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_consume_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_consume_cancel> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<lv_authgln_consume_cancel>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_consume_cancel> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_consume_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_consume_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_consume_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_consume_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_consume_cancel).
                            DATA lv_gtin_formatted_consume_cancel TYPE string.
                            DATA lv_qty_formatted_consume_cancel TYPE string.
                            DATA lv_batch_formatted_consume_cancel TYPE string.
                            DATA lv_exp_formatted_consume_cancel TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_consume_cancel-gtin ) p_quantity_in = CONV #( ls_item_consume_cancel-prodqty ) p_batch_in = CONV #( ls_item_consume_cancel-batch ) p_exp_date_in = CONV #( ls_item_consume_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_consume_cancel p_quantity_out = lv_qty_formatted_consume_cancel p_batch_out = lv_batch_formatted_consume_cancel p_exp_date_out = lv_exp_formatted_consume_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_consume_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_gtin_consume_cancel>).
                            IF sy-subrc = 0. <l_gtin_consume_cancel> = lv_gtin_formatted_consume_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_qty_consume_cancel>).
                            IF sy-subrc = 0. <l_qty_consume_cancel> = lv_qty_formatted_consume_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_bn_consume_cancel>).
                            IF sy-subrc = 0. <l_bn_consume_cancel> = lv_batch_formatted_consume_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_consume_cancel> TO FIELD-SYMBOL(<l_xd_consume_cancel>).
                            IF sy-subrc = 0. <l_xd_consume_cancel> = lv_exp_formatted_consume_cancel. ENDIF.

                            INSERT <ls_product_line_consume_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DRUG_SALE'.
              ASSIGN COMPONENT 'PHARMACY_SALE_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_drug_sale_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<lv_fromgln_drug_sale>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_drug_sale> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_drug_sale> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<lv_togln_drug_sale>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_drug_sale> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_drug_sale> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<lv_authgln_drug_sale>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_drug_sale> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_drug_sale> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_drug_sale_req> TO FIELD-SYMBOL(<fs_prod_list_drug_sale>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_drug_sale> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_drug_sale).
                            DATA lv_gtin_formatted_drug_sale TYPE string.
                            DATA lv_qty_formatted_drug_sale TYPE string.
                            DATA lv_batch_formatted_drug_sale TYPE string.
                            DATA lv_exp_formatted_drug_sale TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_drug_sale-gtin ) p_quantity_in = CONV #( ls_item_drug_sale-prodqty ) p_batch_in = CONV #( ls_item_drug_sale-batch ) p_exp_date_in = CONV #( ls_item_drug_sale-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_drug_sale p_quantity_out = lv_qty_formatted_drug_sale p_batch_out = lv_batch_formatted_drug_sale p_exp_date_out = lv_exp_formatted_drug_sale ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_drug_sale>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_gtin_drug_sale>).
                            IF sy-subrc = 0. <l_gtin_drug_sale> = lv_gtin_formatted_drug_sale. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_qty_drug_sale>).
                            IF sy-subrc = 0. <l_qty_drug_sale> = lv_qty_formatted_drug_sale. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_bn_drug_sale>).
                            IF sy-subrc = 0. <l_bn_drug_sale> = lv_batch_formatted_drug_sale. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_drug_sale> TO FIELD-SYMBOL(<l_xd_drug_sale>).
                            IF sy-subrc = 0. <l_xd_drug_sale> = lv_exp_formatted_drug_sale. ENDIF.

                            INSERT <ls_product_line_drug_sale> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DRUG_SALE_CANCEL'.
              ASSIGN COMPONENT 'PHARMACY_SALE_CANCEL_SERVICE2' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_drug_sale_cancel_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<lv_fromgln_drug_sale_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_drug_sale_cancel> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_drug_sale_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<lv_togln_drug_sale_cancel>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_drug_sale_cancel> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_drug_sale_cancel> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<lv_authgln_drug_sale_cancel>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_drug_sale_cancel> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_drug_sale_cancel> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_drug_sale_cancel_req> TO FIELD-SYMBOL(<fs_prod_list_drug_sale_cancel>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_drug_sale_cancel> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_drug_sale_cancel).
                            DATA lv_gtin_formatted_drug_sale_cancel TYPE string.
                            DATA lv_qty_formatted_drug_sale_cancel TYPE string.
                            DATA lv_batch_formatted_drug_sale_cancel TYPE string.
                            DATA lv_exp_formatted_drug_sale_cancel TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_drug_sale_cancel-gtin ) p_quantity_in = CONV #( ls_item_drug_sale_cancel-prodqty ) p_batch_in = CONV #( ls_item_drug_sale_cancel-batch ) p_exp_date_in = CONV #( ls_item_drug_sale_cancel-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_drug_sale_cancel p_quantity_out = lv_qty_formatted_drug_sale_cancel p_batch_out = lv_batch_formatted_drug_sale_cancel p_exp_date_out = lv_exp_formatted_drug_sale_cancel ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_drug_sale_cancel>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_gtin_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_gtin_drug_sale_cancel> = lv_gtin_formatted_drug_sale_cancel. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_qty_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_qty_drug_sale_cancel> = lv_qty_formatted_drug_sale_cancel. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_bn_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_bn_drug_sale_cancel> = lv_batch_formatted_drug_sale_cancel. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_drug_sale_cancel> TO FIELD-SYMBOL(<l_xd_drug_sale_cancel>).
                            IF sy-subrc = 0. <l_xd_drug_sale_cancel> = lv_exp_formatted_drug_sale_cancel. ENDIF.

                            INSERT <ls_product_line_drug_sale_cancel> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DEACTIVATE'.
              ASSIGN COMPONENT 'DEACTIVATE_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_deactivate_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<lv_fromgln_deactivate>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln_deactivate> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_fromgln_deactivate> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<lv_togln_deactivate>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_togln_deactivate> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_togln_deactivate> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<lv_authgln_deactivate>).
                IF sy-subrc = 0.
                   IF lt_header IS NOT INITIAL AND lt_header[ 1 ]-auth_gln IS NOT INITIAL.
                     <lv_authgln_deactivate> = lt_header[ 1 ]-auth_gln.
                   ELSEIF lt_header IS NOT INITIAL.
                     <lv_authgln_deactivate> = lt_header[ 1 ]-frm_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_deactivate_req> TO FIELD-SYMBOL(<fs_prod_list_deactivate>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_deactivate> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_deactivate).
                            DATA lv_gtin_formatted_deactivate TYPE string.
                            DATA lv_qty_formatted_deactivate TYPE string.
                            DATA lv_batch_formatted_deactivate TYPE string.
                            DATA lv_exp_formatted_deactivate TYPE string.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_deactivate-gtin ) p_quantity_in = CONV #( ls_item_deactivate-prodqty ) p_batch_in = CONV #( ls_item_deactivate-batch ) p_exp_date_in = CONV #( ls_item_deactivate-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_formatted_deactivate p_quantity_out = lv_qty_formatted_deactivate p_batch_out = lv_batch_formatted_deactivate p_exp_date_out = lv_exp_formatted_deactivate ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_deactivate>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_gtin_deactivate>).
                            IF sy-subrc = 0. <l_gtin_deactivate> = lv_gtin_formatted_deactivate. ENDIF.
                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_qty_deactivate>).
                            IF sy-subrc = 0. <l_qty_deactivate> = lv_qty_formatted_deactivate. ENDIF.
                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_bn_deactivate>).
                            IF sy-subrc = 0. <l_bn_deactivate> = lv_batch_formatted_deactivate. ENDIF.
                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_deactivate> TO FIELD-SYMBOL(<l_xd_deactivate>).
                            IF sy-subrc = 0. <l_xd_deactivate> = lv_exp_formatted_deactivate. ENDIF.

                            INSERT <ls_product_line_deactivate> INTO TABLE <lt_products>.
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

                               " Fetch base data from base table zmm_sst_dtts_itm (or via buffer if exists)
                               " to ensure all fields requested are transferred
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item>-tranid AND item_no = @<fs_item>-itemno.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item>-tranid.
                               ls_processed_dttsit2-item_no = <fs_item>-itemno.

                               " Item Fields (override with any buffered changes if needed, else fallback to ITM)
                               ls_processed_dttsit2-zeile = <fs_item>-zeile.
                               ls_processed_dttsit2-product = <fs_item>-product.
                               ls_processed_dttsit2-prod_name = <fs_item>-prodname.
                               ls_processed_dttsit2-prod_qty = <fs_item>-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item>-produnit.
                               ls_processed_dttsit2-gtin = <fs_item>-gtin.
                               ls_processed_dttsit2-batch = <fs_item>-batch.
                               ls_processed_dttsit2-exp_date = <fs_item>-expdate.
                               ls_processed_dttsit2-notif_id = <lv_notif_id>.
                               ls_processed_dttsit2-tr_response = <r_rc>.
                               ls_processed_dttsit2-mat_doc = <fs_item>-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item>-mvttype.

                               " Header Fields
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.

                               " Status Fields
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

                WHEN 'RETURN'.
                  ASSIGN COMPONENT 'RETURN_SERVICE_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_return_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_return_resp> TO FIELD-SYMBOL(<lv_notif_id_return>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_return_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_return>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_return> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_return>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_return> TO FIELD-SYMBOL(<r_gtin_return>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_return> TO FIELD-SYMBOL(<r_bn_return>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_return> TO FIELD-SYMBOL(<r_rc_return>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_return>).
                             IF <fs_item_return>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_return TYPE string. DATA lv_resp_gtin_return TYPE string.
                             lv_item_gtin_return = <fs_item_return>-gtin. lv_resp_gtin_return = <r_gtin_return>.
                             SHIFT lv_item_gtin_return LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_return LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_return = lv_resp_gtin_return AND <fs_item_return>-batch = <r_bn_return>.
                               DATA ls_processed_dttsit2_return TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_return
                                 WHERE tran_id = @<fs_item_return>-tranid AND item_no = @<fs_item_return>-itemno.

                               ls_processed_dttsit2_return-mandt = sy-mandt.
                               ls_processed_dttsit2_return-tran_id = <fs_item_return>-tranid.
                               ls_processed_dttsit2_return-item_no = <fs_item_return>-itemno.
                               ls_processed_dttsit2_return-zeile = <fs_item_return>-zeile.
                               ls_processed_dttsit2_return-product = <fs_item_return>-product.
                               ls_processed_dttsit2_return-prod_name = <fs_item_return>-prodname.
                               ls_processed_dttsit2_return-prod_qty = <fs_item_return>-prodqty.
                               ls_processed_dttsit2_return-prod_unit = <fs_item_return>-produnit.
                               ls_processed_dttsit2_return-gtin = <fs_item_return>-gtin.
                               ls_processed_dttsit2_return-batch = <fs_item_return>-batch.
                               ls_processed_dttsit2_return-exp_date = <fs_item_return>-expdate.
                               IF <lv_notif_id_return> IS ASSIGNED. ls_processed_dttsit2_return-notif_id = <lv_notif_id_return>. ENDIF.
                               IF <r_rc_return> IS ASSIGNED. ls_processed_dttsit2_return-tr_response = <r_rc_return>. ENDIF.
                               ls_processed_dttsit2_return-mat_doc = <fs_item_return>-matdoc.
                               ls_processed_dttsit2_return-mvt_type = <fs_item_return>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_return-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_return-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_return-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_return> = '00000'. ls_processed_dttsit2_return-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_return-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_return TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_return> ) IMPORTING p_description = lv_desc_return ).
                               ls_processed_dttsit2_return-trans_stat = lv_desc_return.
                               ls_processed_dttsit2_return-changed_date = sy-datum.
                               ls_processed_dttsit2_return-changed_time = sy-uzeit.
                               ls_processed_dttsit2_return-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_return TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

                WHEN 'DISPATCH'.
                  ASSIGN COMPONENT 'DISPATCH_BATCH_SERVICE_REQUE1' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_dispatch_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_dispatch_resp> TO FIELD-SYMBOL(<lv_notif_id_dispatch>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_dispatch_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_dispatch>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_dispatch> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_dispatch>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_dispatch> TO FIELD-SYMBOL(<r_gtin_dispatch>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_dispatch> TO FIELD-SYMBOL(<r_bn_dispatch>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_dispatch> TO FIELD-SYMBOL(<r_rc_dispatch>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_dispatch>).
                             IF <fs_item_dispatch>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_dispatch TYPE string. DATA lv_resp_gtin_dispatch TYPE string.
                             lv_item_gtin_dispatch = <fs_item_dispatch>-gtin. lv_resp_gtin_dispatch = <r_gtin_dispatch>.
                             SHIFT lv_item_gtin_dispatch LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_dispatch LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_dispatch = lv_resp_gtin_dispatch AND <fs_item_dispatch>-batch = <r_bn_dispatch>.
                               DATA ls_processed_dttsit2_dispatch TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_dispatch
                                 WHERE tran_id = @<fs_item_dispatch>-tranid AND item_no = @<fs_item_dispatch>-itemno.

                               ls_processed_dttsit2_dispatch-mandt = sy-mandt.
                               ls_processed_dttsit2_dispatch-tran_id = <fs_item_dispatch>-tranid.
                               ls_processed_dttsit2_dispatch-item_no = <fs_item_dispatch>-itemno.
                               ls_processed_dttsit2_dispatch-zeile = <fs_item_dispatch>-zeile.
                               ls_processed_dttsit2_dispatch-product = <fs_item_dispatch>-product.
                               ls_processed_dttsit2_dispatch-prod_name = <fs_item_dispatch>-prodname.
                               ls_processed_dttsit2_dispatch-prod_qty = <fs_item_dispatch>-prodqty.
                               ls_processed_dttsit2_dispatch-prod_unit = <fs_item_dispatch>-produnit.
                               ls_processed_dttsit2_dispatch-gtin = <fs_item_dispatch>-gtin.
                               ls_processed_dttsit2_dispatch-batch = <fs_item_dispatch>-batch.
                               ls_processed_dttsit2_dispatch-exp_date = <fs_item_dispatch>-expdate.
                               IF <lv_notif_id_dispatch> IS ASSIGNED. ls_processed_dttsit2_dispatch-notif_id = <lv_notif_id_dispatch>. ENDIF.
                               IF <r_rc_dispatch> IS ASSIGNED. ls_processed_dttsit2_dispatch-tr_response = <r_rc_dispatch>. ENDIF.
                               ls_processed_dttsit2_dispatch-mat_doc = <fs_item_dispatch>-matdoc.
                               ls_processed_dttsit2_dispatch-mvt_type = <fs_item_dispatch>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_dispatch-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_dispatch-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_dispatch-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_dispatch> = '00000'. ls_processed_dttsit2_dispatch-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_dispatch-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_dispatch TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_dispatch> ) IMPORTING p_description = lv_desc_dispatch ).
                               ls_processed_dttsit2_dispatch-trans_stat = lv_desc_dispatch.
                               ls_processed_dttsit2_dispatch-changed_date = sy-datum.
                               ls_processed_dttsit2_dispatch-changed_time = sy-uzeit.
                               ls_processed_dttsit2_dispatch-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_dispatch TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

                WHEN 'DISPATCH_CANCEL'.
                  ASSIGN COMPONENT 'DISPATCH_CANCEL_SERVICE_RESPO' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_dispatch_cancel_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_dispatch_cancel_resp> TO FIELD-SYMBOL(<lv_notif_id_dispatch_cancel>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_dispatch_cancel_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_dispatch_cancel>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_dispatch_cancel> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_dispatch_cancel>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_dispatch_cancel> TO FIELD-SYMBOL(<r_gtin_dispatch_cancel>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_dispatch_cancel> TO FIELD-SYMBOL(<r_bn_dispatch_cancel>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_dispatch_cancel> TO FIELD-SYMBOL(<r_rc_dispatch_cancel>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_dispatch_cancel>).
                             IF <fs_item_dispatch_cancel>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_dispatch_cancel TYPE string. DATA lv_resp_gtin_dispatch_cancel TYPE string.
                             lv_item_gtin_dispatch_cancel = <fs_item_dispatch_cancel>-gtin. lv_resp_gtin_dispatch_cancel = <r_gtin_dispatch_cancel>.
                             SHIFT lv_item_gtin_dispatch_cancel LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_dispatch_cancel LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_dispatch_cancel = lv_resp_gtin_dispatch_cancel AND <fs_item_dispatch_cancel>-batch = <r_bn_dispatch_cancel>.
                               DATA ls_processed_dttsit2_dispatch_cancel TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_dispatch_cancel
                                 WHERE tran_id = @<fs_item_dispatch_cancel>-tranid AND item_no = @<fs_item_dispatch_cancel>-itemno.

                               ls_processed_dttsit2_dispatch_cancel-mandt = sy-mandt.
                               ls_processed_dttsit2_dispatch_cancel-tran_id = <fs_item_dispatch_cancel>-tranid.
                               ls_processed_dttsit2_dispatch_cancel-item_no = <fs_item_dispatch_cancel>-itemno.
                               ls_processed_dttsit2_dispatch_cancel-zeile = <fs_item_dispatch_cancel>-zeile.
                               ls_processed_dttsit2_dispatch_cancel-product = <fs_item_dispatch_cancel>-product.
                               ls_processed_dttsit2_dispatch_cancel-prod_name = <fs_item_dispatch_cancel>-prodname.
                               ls_processed_dttsit2_dispatch_cancel-prod_qty = <fs_item_dispatch_cancel>-prodqty.
                               ls_processed_dttsit2_dispatch_cancel-prod_unit = <fs_item_dispatch_cancel>-produnit.
                               ls_processed_dttsit2_dispatch_cancel-gtin = <fs_item_dispatch_cancel>-gtin.
                               ls_processed_dttsit2_dispatch_cancel-batch = <fs_item_dispatch_cancel>-batch.
                               ls_processed_dttsit2_dispatch_cancel-exp_date = <fs_item_dispatch_cancel>-expdate.
                               IF <lv_notif_id_dispatch_cancel> IS ASSIGNED. ls_processed_dttsit2_dispatch_cancel-notif_id = <lv_notif_id_dispatch_cancel>. ENDIF.
                               IF <r_rc_dispatch_cancel> IS ASSIGNED. ls_processed_dttsit2_dispatch_cancel-tr_response = <r_rc_dispatch_cancel>. ENDIF.
                               ls_processed_dttsit2_dispatch_cancel-mat_doc = <fs_item_dispatch_cancel>-matdoc.
                               ls_processed_dttsit2_dispatch_cancel-mvt_type = <fs_item_dispatch_cancel>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_dispatch_cancel-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_dispatch_cancel-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_dispatch_cancel-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_dispatch_cancel> = '00000'. ls_processed_dttsit2_dispatch_cancel-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_dispatch_cancel-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_dispatch_cancel TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_dispatch_cancel> ) IMPORTING p_description = lv_desc_dispatch_cancel ).
                               ls_processed_dttsit2_dispatch_cancel-trans_stat = lv_desc_dispatch_cancel.
                               ls_processed_dttsit2_dispatch_cancel-changed_date = sy-datum.
                               ls_processed_dttsit2_dispatch_cancel-changed_time = sy-uzeit.
                               ls_processed_dttsit2_dispatch_cancel-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_dispatch_cancel TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

                WHEN 'TRANSFER'.
                  ASSIGN COMPONENT 'TRANSFER_BATCH_SERVICE_RESPON' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_transfer_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_transfer_resp> TO FIELD-SYMBOL(<lv_notif_id_transfer>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_transfer_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_transfer>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_transfer> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_transfer>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_transfer> TO FIELD-SYMBOL(<r_gtin_transfer>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_transfer> TO FIELD-SYMBOL(<r_bn_transfer>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_transfer> TO FIELD-SYMBOL(<r_rc_transfer>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_transfer>).
                             IF <fs_item_transfer>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_transfer TYPE string. DATA lv_resp_gtin_transfer TYPE string.
                             lv_item_gtin_transfer = <fs_item_transfer>-gtin. lv_resp_gtin_transfer = <r_gtin_transfer>.
                             SHIFT lv_item_gtin_transfer LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_transfer LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_transfer = lv_resp_gtin_transfer AND <fs_item_transfer>-batch = <r_bn_transfer>.
                               DATA ls_processed_dttsit2_transfer TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_transfer
                                 WHERE tran_id = @<fs_item_transfer>-tranid AND item_no = @<fs_item_transfer>-itemno.

                               ls_processed_dttsit2_transfer-mandt = sy-mandt.
                               ls_processed_dttsit2_transfer-tran_id = <fs_item_transfer>-tranid.
                               ls_processed_dttsit2_transfer-item_no = <fs_item_transfer>-itemno.
                               ls_processed_dttsit2_transfer-zeile = <fs_item_transfer>-zeile.
                               ls_processed_dttsit2_transfer-product = <fs_item_transfer>-product.
                               ls_processed_dttsit2_transfer-prod_name = <fs_item_transfer>-prodname.
                               ls_processed_dttsit2_transfer-prod_qty = <fs_item_transfer>-prodqty.
                               ls_processed_dttsit2_transfer-prod_unit = <fs_item_transfer>-produnit.
                               ls_processed_dttsit2_transfer-gtin = <fs_item_transfer>-gtin.
                               ls_processed_dttsit2_transfer-batch = <fs_item_transfer>-batch.
                               ls_processed_dttsit2_transfer-exp_date = <fs_item_transfer>-expdate.
                               IF <lv_notif_id_transfer> IS ASSIGNED. ls_processed_dttsit2_transfer-notif_id = <lv_notif_id_transfer>. ENDIF.
                               IF <r_rc_transfer> IS ASSIGNED. ls_processed_dttsit2_transfer-tr_response = <r_rc_transfer>. ENDIF.
                               ls_processed_dttsit2_transfer-mat_doc = <fs_item_transfer>-matdoc.
                               ls_processed_dttsit2_transfer-mvt_type = <fs_item_transfer>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_transfer-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_transfer-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_transfer-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_transfer> = '00000'. ls_processed_dttsit2_transfer-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_transfer-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_transfer TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_transfer> ) IMPORTING p_description = lv_desc_transfer ).
                               ls_processed_dttsit2_transfer-trans_stat = lv_desc_transfer.
                               ls_processed_dttsit2_transfer-changed_date = sy-datum.
                               ls_processed_dttsit2_transfer-changed_time = sy-uzeit.
                               ls_processed_dttsit2_transfer-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_transfer TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

                WHEN 'TRANSFER_CANCEL'.
                  ASSIGN COMPONENT 'TRANSFER_CANCEL_SERVICE_RESPO' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_transfer_cancel_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_transfer_cancel_resp> TO FIELD-SYMBOL(<lv_notif_id_transfer_cancel>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_transfer_cancel_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_transfer_cancel>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_transfer_cancel> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_transfer_cancel>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_transfer_cancel> TO FIELD-SYMBOL(<r_gtin_transfer_cancel>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_transfer_cancel> TO FIELD-SYMBOL(<r_bn_transfer_cancel>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_transfer_cancel> TO FIELD-SYMBOL(<r_rc_transfer_cancel>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_transfer_cancel>).
                             IF <fs_item_transfer_cancel>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_transfer_cancel TYPE string. DATA lv_resp_gtin_transfer_cancel TYPE string.
                             lv_item_gtin_transfer_cancel = <fs_item_transfer_cancel>-gtin. lv_resp_gtin_transfer_cancel = <r_gtin_transfer_cancel>.
                             SHIFT lv_item_gtin_transfer_cancel LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_transfer_cancel LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_transfer_cancel = lv_resp_gtin_transfer_cancel AND <fs_item_transfer_cancel>-batch = <r_bn_transfer_cancel>.
                               DATA ls_processed_dttsit2_transfer_cancel TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_transfer_cancel
                                 WHERE tran_id = @<fs_item_transfer_cancel>-tranid AND item_no = @<fs_item_transfer_cancel>-itemno.

                               ls_processed_dttsit2_transfer_cancel-mandt = sy-mandt.
                               ls_processed_dttsit2_transfer_cancel-tran_id = <fs_item_transfer_cancel>-tranid.
                               ls_processed_dttsit2_transfer_cancel-item_no = <fs_item_transfer_cancel>-itemno.
                               ls_processed_dttsit2_transfer_cancel-zeile = <fs_item_transfer_cancel>-zeile.
                               ls_processed_dttsit2_transfer_cancel-product = <fs_item_transfer_cancel>-product.
                               ls_processed_dttsit2_transfer_cancel-prod_name = <fs_item_transfer_cancel>-prodname.
                               ls_processed_dttsit2_transfer_cancel-prod_qty = <fs_item_transfer_cancel>-prodqty.
                               ls_processed_dttsit2_transfer_cancel-prod_unit = <fs_item_transfer_cancel>-produnit.
                               ls_processed_dttsit2_transfer_cancel-gtin = <fs_item_transfer_cancel>-gtin.
                               ls_processed_dttsit2_transfer_cancel-batch = <fs_item_transfer_cancel>-batch.
                               ls_processed_dttsit2_transfer_cancel-exp_date = <fs_item_transfer_cancel>-expdate.
                               IF <lv_notif_id_transfer_cancel> IS ASSIGNED. ls_processed_dttsit2_transfer_cancel-notif_id = <lv_notif_id_transfer_cancel>. ENDIF.
                               IF <r_rc_transfer_cancel> IS ASSIGNED. ls_processed_dttsit2_transfer_cancel-tr_response = <r_rc_transfer_cancel>. ENDIF.
                               ls_processed_dttsit2_transfer_cancel-mat_doc = <fs_item_transfer_cancel>-matdoc.
                               ls_processed_dttsit2_transfer_cancel-mvt_type = <fs_item_transfer_cancel>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_transfer_cancel-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_transfer_cancel-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_transfer_cancel-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_transfer_cancel> = '00000'. ls_processed_dttsit2_transfer_cancel-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_transfer_cancel-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_transfer_cancel TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_transfer_cancel> ) IMPORTING p_description = lv_desc_transfer_cancel ).
                               ls_processed_dttsit2_transfer_cancel-trans_stat = lv_desc_transfer_cancel.
                               ls_processed_dttsit2_transfer_cancel-changed_date = sy-datum.
                               ls_processed_dttsit2_transfer_cancel-changed_time = sy-uzeit.
                               ls_processed_dttsit2_transfer_cancel-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_transfer_cancel TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

                WHEN 'CONSUME'.
                  ASSIGN COMPONENT 'CONSUME_SERVICE_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_consume_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_consume_resp> TO FIELD-SYMBOL(<lv_notif_id_consume>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_consume_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_consume>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_consume> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_consume>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_consume> TO FIELD-SYMBOL(<r_gtin_consume>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_consume> TO FIELD-SYMBOL(<r_bn_consume>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_consume> TO FIELD-SYMBOL(<r_rc_consume>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_consume>).
                             IF <fs_item_consume>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_consume TYPE string. DATA lv_resp_gtin_consume TYPE string.
                             lv_item_gtin_consume = <fs_item_consume>-gtin. lv_resp_gtin_consume = <r_gtin_consume>.
                             SHIFT lv_item_gtin_consume LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_consume LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_consume = lv_resp_gtin_consume AND <fs_item_consume>-batch = <r_bn_consume>.
                               DATA ls_processed_dttsit2_consume TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_consume
                                 WHERE tran_id = @<fs_item_consume>-tranid AND item_no = @<fs_item_consume>-itemno.

                               ls_processed_dttsit2_consume-mandt = sy-mandt.
                               ls_processed_dttsit2_consume-tran_id = <fs_item_consume>-tranid.
                               ls_processed_dttsit2_consume-item_no = <fs_item_consume>-itemno.
                               ls_processed_dttsit2_consume-zeile = <fs_item_consume>-zeile.
                               ls_processed_dttsit2_consume-product = <fs_item_consume>-product.
                               ls_processed_dttsit2_consume-prod_name = <fs_item_consume>-prodname.
                               ls_processed_dttsit2_consume-prod_qty = <fs_item_consume>-prodqty.
                               ls_processed_dttsit2_consume-prod_unit = <fs_item_consume>-produnit.
                               ls_processed_dttsit2_consume-gtin = <fs_item_consume>-gtin.
                               ls_processed_dttsit2_consume-batch = <fs_item_consume>-batch.
                               ls_processed_dttsit2_consume-exp_date = <fs_item_consume>-expdate.
                               IF <lv_notif_id_consume> IS ASSIGNED. ls_processed_dttsit2_consume-notif_id = <lv_notif_id_consume>. ENDIF.
                               IF <r_rc_consume> IS ASSIGNED. ls_processed_dttsit2_consume-tr_response = <r_rc_consume>. ENDIF.
                               ls_processed_dttsit2_consume-mat_doc = <fs_item_consume>-matdoc.
                               ls_processed_dttsit2_consume-mvt_type = <fs_item_consume>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_consume-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_consume-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_consume-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_consume> = '00000'. ls_processed_dttsit2_consume-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_consume-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_consume TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_consume> ) IMPORTING p_description = lv_desc_consume ).
                               ls_processed_dttsit2_consume-trans_stat = lv_desc_consume.
                               ls_processed_dttsit2_consume-changed_date = sy-datum.
                               ls_processed_dttsit2_consume-changed_time = sy-uzeit.
                               ls_processed_dttsit2_consume-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_consume TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

                WHEN 'CONSUME_CANCEL'.
                  ASSIGN COMPONENT 'CONSUME_CANCEL_SERVICE_RESPON' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_consume_cancel_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_consume_cancel_resp> TO FIELD-SYMBOL(<lv_notif_id_consume_cancel>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_consume_cancel_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_consume_cancel>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_consume_cancel> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_consume_cancel>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_consume_cancel> TO FIELD-SYMBOL(<r_gtin_consume_cancel>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_consume_cancel> TO FIELD-SYMBOL(<r_bn_consume_cancel>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_consume_cancel> TO FIELD-SYMBOL(<r_rc_consume_cancel>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_consume_cancel>).
                             IF <fs_item_consume_cancel>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_consume_cancel TYPE string. DATA lv_resp_gtin_consume_cancel TYPE string.
                             lv_item_gtin_consume_cancel = <fs_item_consume_cancel>-gtin. lv_resp_gtin_consume_cancel = <r_gtin_consume_cancel>.
                             SHIFT lv_item_gtin_consume_cancel LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_consume_cancel LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_consume_cancel = lv_resp_gtin_consume_cancel AND <fs_item_consume_cancel>-batch = <r_bn_consume_cancel>.
                               DATA ls_processed_dttsit2_consume_cancel TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_consume_cancel
                                 WHERE tran_id = @<fs_item_consume_cancel>-tranid AND item_no = @<fs_item_consume_cancel>-itemno.

                               ls_processed_dttsit2_consume_cancel-mandt = sy-mandt.
                               ls_processed_dttsit2_consume_cancel-tran_id = <fs_item_consume_cancel>-tranid.
                               ls_processed_dttsit2_consume_cancel-item_no = <fs_item_consume_cancel>-itemno.
                               ls_processed_dttsit2_consume_cancel-zeile = <fs_item_consume_cancel>-zeile.
                               ls_processed_dttsit2_consume_cancel-product = <fs_item_consume_cancel>-product.
                               ls_processed_dttsit2_consume_cancel-prod_name = <fs_item_consume_cancel>-prodname.
                               ls_processed_dttsit2_consume_cancel-prod_qty = <fs_item_consume_cancel>-prodqty.
                               ls_processed_dttsit2_consume_cancel-prod_unit = <fs_item_consume_cancel>-produnit.
                               ls_processed_dttsit2_consume_cancel-gtin = <fs_item_consume_cancel>-gtin.
                               ls_processed_dttsit2_consume_cancel-batch = <fs_item_consume_cancel>-batch.
                               ls_processed_dttsit2_consume_cancel-exp_date = <fs_item_consume_cancel>-expdate.
                               IF <lv_notif_id_consume_cancel> IS ASSIGNED. ls_processed_dttsit2_consume_cancel-notif_id = <lv_notif_id_consume_cancel>. ENDIF.
                               IF <r_rc_consume_cancel> IS ASSIGNED. ls_processed_dttsit2_consume_cancel-tr_response = <r_rc_consume_cancel>. ENDIF.
                               ls_processed_dttsit2_consume_cancel-mat_doc = <fs_item_consume_cancel>-matdoc.
                               ls_processed_dttsit2_consume_cancel-mvt_type = <fs_item_consume_cancel>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_consume_cancel-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_consume_cancel-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_consume_cancel-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_consume_cancel> = '00000'. ls_processed_dttsit2_consume_cancel-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_consume_cancel-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_consume_cancel TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_consume_cancel> ) IMPORTING p_description = lv_desc_consume_cancel ).
                               ls_processed_dttsit2_consume_cancel-trans_stat = lv_desc_consume_cancel.
                               ls_processed_dttsit2_consume_cancel-changed_date = sy-datum.
                               ls_processed_dttsit2_consume_cancel-changed_time = sy-uzeit.
                               ls_processed_dttsit2_consume_cancel-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_consume_cancel TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

                WHEN 'DRUG_SALE'.
                  ASSIGN COMPONENT 'PHARMACY_SALE_SERVICE_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_drug_sale_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_drug_sale_resp> TO FIELD-SYMBOL(<lv_notif_id_drug_sale>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_drug_sale_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_drug_sale>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_drug_sale> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_drug_sale>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_drug_sale> TO FIELD-SYMBOL(<r_gtin_drug_sale>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_drug_sale> TO FIELD-SYMBOL(<r_bn_drug_sale>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_drug_sale> TO FIELD-SYMBOL(<r_rc_drug_sale>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_drug_sale>).
                             IF <fs_item_drug_sale>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_drug_sale TYPE string. DATA lv_resp_gtin_drug_sale TYPE string.
                             lv_item_gtin_drug_sale = <fs_item_drug_sale>-gtin. lv_resp_gtin_drug_sale = <r_gtin_drug_sale>.
                             SHIFT lv_item_gtin_drug_sale LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_drug_sale LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_drug_sale = lv_resp_gtin_drug_sale AND <fs_item_drug_sale>-batch = <r_bn_drug_sale>.
                               DATA ls_processed_dttsit2_drug_sale TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_drug_sale
                                 WHERE tran_id = @<fs_item_drug_sale>-tranid AND item_no = @<fs_item_drug_sale>-itemno.

                               ls_processed_dttsit2_drug_sale-mandt = sy-mandt.
                               ls_processed_dttsit2_drug_sale-tran_id = <fs_item_drug_sale>-tranid.
                               ls_processed_dttsit2_drug_sale-item_no = <fs_item_drug_sale>-itemno.
                               ls_processed_dttsit2_drug_sale-zeile = <fs_item_drug_sale>-zeile.
                               ls_processed_dttsit2_drug_sale-product = <fs_item_drug_sale>-product.
                               ls_processed_dttsit2_drug_sale-prod_name = <fs_item_drug_sale>-prodname.
                               ls_processed_dttsit2_drug_sale-prod_qty = <fs_item_drug_sale>-prodqty.
                               ls_processed_dttsit2_drug_sale-prod_unit = <fs_item_drug_sale>-produnit.
                               ls_processed_dttsit2_drug_sale-gtin = <fs_item_drug_sale>-gtin.
                               ls_processed_dttsit2_drug_sale-batch = <fs_item_drug_sale>-batch.
                               ls_processed_dttsit2_drug_sale-exp_date = <fs_item_drug_sale>-expdate.
                               IF <lv_notif_id_drug_sale> IS ASSIGNED. ls_processed_dttsit2_drug_sale-notif_id = <lv_notif_id_drug_sale>. ENDIF.
                               IF <r_rc_drug_sale> IS ASSIGNED. ls_processed_dttsit2_drug_sale-tr_response = <r_rc_drug_sale>. ENDIF.
                               ls_processed_dttsit2_drug_sale-mat_doc = <fs_item_drug_sale>-matdoc.
                               ls_processed_dttsit2_drug_sale-mvt_type = <fs_item_drug_sale>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_drug_sale-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_drug_sale-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_drug_sale-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_drug_sale> = '00000'. ls_processed_dttsit2_drug_sale-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_drug_sale-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_drug_sale TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_drug_sale> ) IMPORTING p_description = lv_desc_drug_sale ).
                               ls_processed_dttsit2_drug_sale-trans_stat = lv_desc_drug_sale.
                               ls_processed_dttsit2_drug_sale-changed_date = sy-datum.
                               ls_processed_dttsit2_drug_sale-changed_time = sy-uzeit.
                               ls_processed_dttsit2_drug_sale-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_drug_sale TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

                WHEN 'DRUG_SALE_CANCEL'.
                  ASSIGN COMPONENT 'PHARMACY_SALE_CANCEL_SERVICE1' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_drug_sale_cancel_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_drug_sale_cancel_resp> TO FIELD-SYMBOL(<lv_notif_id_drug_sale_cancel>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_drug_sale_cancel_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_drug_sale_cancel>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_drug_sale_cancel> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_drug_sale_cancel>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_drug_sale_cancel> TO FIELD-SYMBOL(<r_gtin_drug_sale_cancel>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_drug_sale_cancel> TO FIELD-SYMBOL(<r_bn_drug_sale_cancel>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_drug_sale_cancel> TO FIELD-SYMBOL(<r_rc_drug_sale_cancel>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_drug_sale_cancel>).
                             IF <fs_item_drug_sale_cancel>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_drug_sale_cancel TYPE string. DATA lv_resp_gtin_drug_sale_cancel TYPE string.
                             lv_item_gtin_drug_sale_cancel = <fs_item_drug_sale_cancel>-gtin. lv_resp_gtin_drug_sale_cancel = <r_gtin_drug_sale_cancel>.
                             SHIFT lv_item_gtin_drug_sale_cancel LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_drug_sale_cancel LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_drug_sale_cancel = lv_resp_gtin_drug_sale_cancel AND <fs_item_drug_sale_cancel>-batch = <r_bn_drug_sale_cancel>.
                               DATA ls_processed_dttsit2_drug_sale_cancel TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_drug_sale_cancel
                                 WHERE tran_id = @<fs_item_drug_sale_cancel>-tranid AND item_no = @<fs_item_drug_sale_cancel>-itemno.

                               ls_processed_dttsit2_drug_sale_cancel-mandt = sy-mandt.
                               ls_processed_dttsit2_drug_sale_cancel-tran_id = <fs_item_drug_sale_cancel>-tranid.
                               ls_processed_dttsit2_drug_sale_cancel-item_no = <fs_item_drug_sale_cancel>-itemno.
                               ls_processed_dttsit2_drug_sale_cancel-zeile = <fs_item_drug_sale_cancel>-zeile.
                               ls_processed_dttsit2_drug_sale_cancel-product = <fs_item_drug_sale_cancel>-product.
                               ls_processed_dttsit2_drug_sale_cancel-prod_name = <fs_item_drug_sale_cancel>-prodname.
                               ls_processed_dttsit2_drug_sale_cancel-prod_qty = <fs_item_drug_sale_cancel>-prodqty.
                               ls_processed_dttsit2_drug_sale_cancel-prod_unit = <fs_item_drug_sale_cancel>-produnit.
                               ls_processed_dttsit2_drug_sale_cancel-gtin = <fs_item_drug_sale_cancel>-gtin.
                               ls_processed_dttsit2_drug_sale_cancel-batch = <fs_item_drug_sale_cancel>-batch.
                               ls_processed_dttsit2_drug_sale_cancel-exp_date = <fs_item_drug_sale_cancel>-expdate.
                               IF <lv_notif_id_drug_sale_cancel> IS ASSIGNED. ls_processed_dttsit2_drug_sale_cancel-notif_id = <lv_notif_id_drug_sale_cancel>. ENDIF.
                               IF <r_rc_drug_sale_cancel> IS ASSIGNED. ls_processed_dttsit2_drug_sale_cancel-tr_response = <r_rc_drug_sale_cancel>. ENDIF.
                               ls_processed_dttsit2_drug_sale_cancel-mat_doc = <fs_item_drug_sale_cancel>-matdoc.
                               ls_processed_dttsit2_drug_sale_cancel-mvt_type = <fs_item_drug_sale_cancel>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_drug_sale_cancel-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_drug_sale_cancel-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_drug_sale_cancel-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_drug_sale_cancel> = '00000'. ls_processed_dttsit2_drug_sale_cancel-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_drug_sale_cancel-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_drug_sale_cancel TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_drug_sale_cancel> ) IMPORTING p_description = lv_desc_drug_sale_cancel ).
                               ls_processed_dttsit2_drug_sale_cancel-trans_stat = lv_desc_drug_sale_cancel.
                               ls_processed_dttsit2_drug_sale_cancel-changed_date = sy-datum.
                               ls_processed_dttsit2_drug_sale_cancel-changed_time = sy-uzeit.
                               ls_processed_dttsit2_drug_sale_cancel-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_drug_sale_cancel TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

                WHEN 'DEACTIVATE'.
                  ASSIGN COMPONENT 'DEACTIVATE_SERVICE_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_deactivate_resp>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_deactivate_resp> TO FIELD-SYMBOL(<lv_notif_id_deactivate>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_deactivate_resp> TO FIELD-SYMBOL(<fs_resp_prod_list_deactivate>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_deactivate> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_deactivate>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_deactivate> TO FIELD-SYMBOL(<r_gtin_deactivate>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_deactivate> TO FIELD-SYMBOL(<r_bn_deactivate>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_deactivate> TO FIELD-SYMBOL(<r_rc_deactivate>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_deactivate>).
                             IF <fs_item_deactivate>-prodstat = 'SUCCESS'. CONTINUE. ENDIF.
                             DATA lv_item_gtin_deactivate TYPE string. DATA lv_resp_gtin_deactivate TYPE string.
                             lv_item_gtin_deactivate = <fs_item_deactivate>-gtin. lv_resp_gtin_deactivate = <r_gtin_deactivate>.
                             SHIFT lv_item_gtin_deactivate LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin_deactivate LEFT DELETING LEADING '0'.

                             IF lv_item_gtin_deactivate = lv_resp_gtin_deactivate AND <fs_item_deactivate>-batch = <r_bn_deactivate>.
                               DATA ls_processed_dttsit2_deactivate TYPE zmm_sst_dttsit2.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2_deactivate
                                 WHERE tran_id = @<fs_item_deactivate>-tranid AND item_no = @<fs_item_deactivate>-itemno.

                               ls_processed_dttsit2_deactivate-mandt = sy-mandt.
                               ls_processed_dttsit2_deactivate-tran_id = <fs_item_deactivate>-tranid.
                               ls_processed_dttsit2_deactivate-item_no = <fs_item_deactivate>-itemno.
                               ls_processed_dttsit2_deactivate-zeile = <fs_item_deactivate>-zeile.
                               ls_processed_dttsit2_deactivate-product = <fs_item_deactivate>-product.
                               ls_processed_dttsit2_deactivate-prod_name = <fs_item_deactivate>-prodname.
                               ls_processed_dttsit2_deactivate-prod_qty = <fs_item_deactivate>-prodqty.
                               ls_processed_dttsit2_deactivate-prod_unit = <fs_item_deactivate>-produnit.
                               ls_processed_dttsit2_deactivate-gtin = <fs_item_deactivate>-gtin.
                               ls_processed_dttsit2_deactivate-batch = <fs_item_deactivate>-batch.
                               ls_processed_dttsit2_deactivate-exp_date = <fs_item_deactivate>-expdate.
                               IF <lv_notif_id_deactivate> IS ASSIGNED. ls_processed_dttsit2_deactivate-notif_id = <lv_notif_id_deactivate>. ENDIF.
                               IF <r_rc_deactivate> IS ASSIGNED. ls_processed_dttsit2_deactivate-tr_response = <r_rc_deactivate>. ENDIF.
                               ls_processed_dttsit2_deactivate-mat_doc = <fs_item_deactivate>-matdoc.
                               ls_processed_dttsit2_deactivate-mvt_type = <fs_item_deactivate>-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2_deactivate-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2_deactivate-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2_deactivate-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_deactivate> = '00000'. ls_processed_dttsit2_deactivate-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2_deactivate-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               DATA lv_desc_deactivate TYPE char255.
                               me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_deactivate> ) IMPORTING p_description = lv_desc_deactivate ).
                               ls_processed_dttsit2_deactivate-trans_stat = lv_desc_deactivate.
                               ls_processed_dttsit2_deactivate-changed_date = sy-datum.
                               ls_processed_dttsit2_deactivate-changed_time = sy-uzeit.
                               ls_processed_dttsit2_deactivate-changed_by = sy-uname.

                               APPEND ls_processed_dttsit2_deactivate TO et_update_buffer.
                             ENDIF.
                           ENDLOOP.
                        ENDLOOP.
                      ENDIF.
                    ENDIF.
                  ENDIF.

              ENDCASE.

            CATCH cx_ai_application_fault INTO DATA(lx_app_fault).
               LOOP AT lt_items ASSIGNING <fs_item>.
                 APPEND me->populate_full_error_record( is_item = <fs_item> it_header = lt_header iv_trans_stat = 'API Application Fault' ) TO et_update_buffer.
               ENDLOOP.
            CATCH cx_ai_system_fault INTO DATA(lx_sys).
               LOOP AT lt_items ASSIGNING <fs_item>.
                 APPEND me->populate_full_error_record( is_item = <fs_item> it_header = lt_header iv_trans_stat = 'API System Fault' ) TO et_update_buffer.
               ENDLOOP.
            CATCH cx_root INTO DATA(lx_root).
               LOOP AT lt_items ASSIGNING <fs_item>.
                 APPEND me->populate_full_error_record( is_item = <fs_item> it_header = lt_header iv_trans_stat = 'Generic API Error' ) TO et_update_buffer.
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
    DATA lv_clean_date TYPE string.
    lv_clean_date = p_exp_date_in.
    REPLACE ALL OCCURRENCES OF '-' IN lv_clean_date WITH ''.

    IF lv_clean_date IS NOT INITIAL.
      " Check if it's already in the format YYMMDD
      IF strlen( lv_clean_date ) = 6.
         lv_year  = lv_clean_date+0(2).
         lv_month = lv_clean_date+2(2).
         lv_day   = lv_clean_date+4(2).
         p_exp_date_out = |{ lv_year }{ lv_month }{ lv_day }|.
      ELSE.
         lv_year  = lv_clean_date+0(4).
         lv_month = lv_clean_date+4(2).
         lv_day   = lv_clean_date+6(2).
         p_exp_date_out = |{ lv_year+2(2) }{ lv_month }{ lv_day }|.
      ENDIF.
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
