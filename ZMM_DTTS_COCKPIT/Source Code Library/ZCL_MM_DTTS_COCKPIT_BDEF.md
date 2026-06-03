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
types tt_is_item TYPE STRUCTURE FOR READ RESULT zr_mm_dtts_cockpit\\Item .
types ty_zmm_sst_dtts_hdr type table of zmm_sst_dtts_hdr.
    METHODS populate_full_error_record IMPORTING is_item type tt_is_item
                                                 iv_trans_stat TYPE string
                                                 it_header TYPE ty_zmm_sst_dtts_hdr
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
        item_no   = ls_entity-item_no
        tran_id   = ls_entity-tran_id
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
        WHERE doc_year = @ls_entity-doc_year AND matdoc = @ls_entity-matdoc AND mvttype = @ls_entity-mvttype AND item_no = @ls_entity-item_no.

      IF sy-subrc = 0.
        SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @DATA(ls_dttsit2)
          WHERE tran_id = @lv_tran_id AND item_no = @ls_entity-item_no.

        IF sy-subrc <> 0.
          " If not in buffer table, read full base from CDS to initialize
          SELECT SINGLE * FROM zr_mm_dtts_cockpit INTO @DATA(ls_base)
            WHERE doc_year = @ls_entity-doc_year AND matdoc = @ls_entity-matdoc AND mvttype = @ls_entity-mvttype AND item_no = @ls_entity-item_no.

          IF sy-subrc = 0.
            ls_dttsit2-mandt = sy-mandt.
            ls_dttsit2-tran_id = ls_base-tran_id.
            ls_dttsit2-item_no = ls_base-item_no.
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
              WHERE mat_doc = @ls_entity-matdoc AND doc_yr = @ls_entity-doc_year AND mvt_type = @ls_entity-mvttype.

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

        APPEND VALUE #( docyear = ls_entity-doc_year matdoc = ls_entity-matdoc mvttype = ls_entity-mvttype itemno = ls_entity-item_no ) TO lt_keys_to_reprocess.
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
        WHERE doc_year = @keys-doc_year
          AND matdoc = @keys-matdoc
          AND mvttype = @keys-mvttype
          AND item_no = @keys-item_no
        INTO CORRESPONDING FIELDS OF TABLE @lt_read_data.

      IF sy-subrc = 0.
        LOOP AT lt_read_data INTO DATA(ls_read_data).
          INSERT VALUE #( %tky = VALUE #( doc_year = ls_read_data-doc_year matdoc = ls_read_data-matdoc mvttype = ls_read_data-mvttype item_no = ls_read_data-item_no )
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
       APPEND VALUE #( docyear = ls_key-doc_year matdoc = ls_key-matdoc mvttype = ls_key-mvttype itemno = ls_key-item_no ) TO lt_keys_to_reprocess.
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
       WHERE tran_id = @is_item-tran_id AND item_no = @is_item-item_no.

     rs_err-mandt = sy-mandt.
     rs_err-tran_id = is_item-tran_id.
     rs_err-item_no = is_item-item_no.
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
          WHERE doc_year = @ls_k-docyear AND matdoc = @ls_k-matdoc AND mvttype = @ls_k-mvttype AND item_no = @ls_k-itemno.

        READ TABLE lcl_buffer=>mt_create INTO DATA(ls_buf) WITH KEY tran_id = lv_t item_no = ls_k-itemno.
        IF sy-subrc = 0.
           ls_item_st = CORRESPONDING #( ls_buf MAPPING matdoc = mat_doc mvttype = mvt_type item_no = item_no tran_id = tran_id
           prodname = prod_name prodqty = prod_qty produnit = prod_unit expdate = exp_date notifid = notif_id trresponse = tr_response
           srnumber = sr_number createddate = created_date createdtime = created_time createdby = created_by changeddate = changed_date
           changedtime = changed_time changedby = changed_by prodstat = prod_stat transstat = trans_stat ).
           ls_item_st-doc_year = ls_k-docyear. " Force mapped key
           APPEND ls_item_st TO lt_items.
        ELSE.
           READ TABLE lcl_buffer=>mt_update INTO ls_buf WITH KEY tran_id = lv_t item_no = ls_k-itemno.
           IF sy-subrc = 0.
             ls_item_st = CORRESPONDING #( ls_buf MAPPING matdoc = mat_doc mvttype = mvt_type item_no = item_no tran_id = tran_id
             prodname = prod_name prodqty = prod_qty produnit = prod_unit expdate = exp_date notifid = notif_id trresponse = tr_response
             srnumber = sr_number createddate = created_date createdtime = created_time createdby = created_by changeddate = changed_date
             changedtime = changed_time changedby = changed_by prodstat = prod_stat transstat = trans_stat ).
             ls_item_st-doc_year = ls_k-docyear.
             APPEND ls_item_st TO lt_items.
           ELSE.
             SELECT SINGLE * FROM zr_mm_dtts_cockpit INTO @DATA(ls_db)
               WHERE doc_year = @ls_k-docyear AND matdoc = @ls_k-matdoc AND mvttype = @ls_k-mvttype AND item_no = @ls_k-itemno.
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
                                 WHERE tran_id = @<fs_item>-tran_id AND item_no = @<fs_item>-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item>-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item>-item_no.

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
          data lv_ran type qfranint .
      CALL FUNCTION 'QF05_RANDOM_INTEGER'
        EXPORTING ran_int_max = 9999 ran_int_min = 1
        IMPORTING ran_int = lv_ran .
      lv_item_no = CONV numc4( lv_ran ).

      APPEND VALUE #( %cid = ls_key-%cid
                      doc_year = lv_doc_year
                      matdoc = lv_mat_doc
                      mvttype = lv_mvt_type
                      item_no = lv_item_no
                      tran_id = CONV ztran_id( lv_ts )
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
      CREATE FIELDS ( doc_year matdoc mvttype item_no tran_id gtin prodqty batch expdate prodstat createddate createdtime createdby )
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
*    IF p_exp_date_in IS NOT INITIAL.
*      lv_year  = p_exp_date_in+0(4).
*      lv_month = p_exp_date_in+4(2).
*      lv_day   = p_exp_date_in+6(2).
*      p_exp_date_out = |{ lv_year }-{ lv_month }-{ lv_day }|.
*    ENDIF.

 DATA lv_clean_date TYPE string.

lv_clean_date = p_exp_date_in.
" Remove any existing hyphens just in case it comes in as YYYY-MM-DD
REPLACE ALL OCCURRENCES OF '-' IN lv_clean_date WITH ''.

IF lv_clean_date IS NOT INITIAL.

  IF strlen( lv_clean_date ) = 6.
    " Handles YYMMDD (e.g., 270430) -> Assume 20xx for the century
    lv_year  = |20{ lv_clean_date+0(2) }|.
    lv_month = lv_clean_date+2(2).
    lv_day   = lv_clean_date+4(2).

  ELSEIF strlen( lv_clean_date ) = 8.
    " Handles YYYYMMDD (e.g., 20270430)
    lv_year  = lv_clean_date+0(4).
    lv_month = lv_clean_date+4(2).
    lv_day   = lv_clean_date+6(2).

  ENDIF.

  " Format the final output to YYYY-MM-DD
  IF lv_year IS NOT INITIAL.
    p_exp_date_out = |{ lv_year }-{ lv_month }-{ lv_day }|.
  ENDIF.
endIF.
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
