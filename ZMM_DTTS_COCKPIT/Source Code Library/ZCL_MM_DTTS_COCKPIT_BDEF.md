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
             doc_year TYPE mjahr,
             matdoc TYPE mblnr,
             mvttype TYPE bwart,
             item_no TYPE numc4,
           END OF ty_key.
    TYPES: tt_keys TYPE STANDARD TABLE OF ty_key WITH DEFAULT KEY.
    TYPES: tt_dttsit2 TYPE STANDARD TABLE OF zmm_sst_dttsit2 WITH DEFAULT KEY.
    TYPES: tt_is_item TYPE STRUCTURE FOR READ RESULT zr_mm_dtts_cockpit\\Item.
    TYPES: ty_zmm_sst_dtts_hdr TYPE TABLE OF zmm_sst_dtts_hdr.

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

    METHODS populate_full_error_record IMPORTING is_item TYPE tt_is_item
                                                 iv_trans_stat TYPE string
                                                 it_header TYPE ty_zmm_sst_dtts_hdr
                                       RETURNING VALUE(rs_err) TYPE zmm_sst_dttsit2.

ENDCLASS.

CLASS lhc_Item IMPLEMENTATION.

  METHOD get_instance_features.
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
    DATA lt_keys_to_reprocess TYPE tt_keys.

    LOOP AT entities INTO DATA(ls_entity).
      SELECT SINGLE tran_id FROM zr_mm_dtts_cockpit INTO @DATA(lv_tran_id)
        WHERE doc_year = @ls_entity-doc_year AND mat_doc = @ls_entity-matdoc AND mvt_type = @ls_entity-mvttype AND item_no = @ls_entity-item_no.

      IF sy-subrc = 0.
        SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @DATA(ls_dttsit2)
          WHERE tran_id = @lv_tran_id AND item_no = @ls_entity-item_no.

        IF sy-subrc <> 0.
          SELECT SINGLE * FROM zr_mm_dtts_cockpit INTO @DATA(ls_base)
            WHERE doc_year = @ls_entity-doc_year AND mat_doc = @ls_entity-matdoc AND mvt_type = @ls_entity-mvttype AND item_no = @ls_entity-item_no.

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

            SELECT SINGLE operation, frm_gln, to_gln FROM zmm_sst_dtts_hdr INTO (@ls_dttsit2-operation, @ls_dttsit2-frm_gln, @ls_dttsit2-to_gln)
              WHERE mat_doc = @ls_entity-matdoc AND doc_yr = @ls_entity-doc_year AND mvt_type = @ls_entity-mvttype.

            APPEND ls_dttsit2 TO lcl_buffer=>mt_create.
          ENDIF.
        ENDIF.

        IF ls_entity-%control-gtin = if_abap_behv=>mk-on. ls_dttsit2-gtin = ls_entity-gtin. ENDIF.
        IF ls_entity-%control-prodqty = if_abap_behv=>mk-on. ls_dttsit2-prod_qty = ls_entity-prodqty. ENDIF.
        IF ls_entity-%control-batch = if_abap_behv=>mk-on. ls_dttsit2-batch = ls_entity-batch. ENDIF.
        IF ls_entity-%control-expdate = if_abap_behv=>mk-on. ls_dttsit2-exp_date = ls_entity-expdate. ENDIF.
        IF ls_entity-%control-frm_gln = if_abap_behv=>mk-on. ls_dttsit2-frm_gln = ls_entity-frm_gln. ENDIF.
        IF ls_entity-%control-to_gln = if_abap_behv=>mk-on. ls_dttsit2-to_gln = ls_entity-to_gln. ENDIF.

        ls_dttsit2-changed_date = sy-datum.
        ls_dttsit2-changed_time = sy-uzeit.
        ls_dttsit2-changed_by = sy-uname.

        READ TABLE lcl_buffer=>mt_create ASSIGNING FIELD-SYMBOL(<fs_create>) WITH KEY tran_id = ls_dttsit2-tran_id item_no = ls_dttsit2-item_no.
        IF sy-subrc = 0.
          <fs_create> = ls_dttsit2.
        ELSE.
          APPEND ls_dttsit2 TO lcl_buffer=>mt_update.
        ENDIF.

        APPEND VALUE #( doc_year = ls_entity-doc_year matdoc = ls_entity-matdoc mvttype = ls_entity-mvttype item_no = ls_entity-item_no ) TO lt_keys_to_reprocess.
      ENDIF.
    ENDLOOP.

    IF lt_keys_to_reprocess IS NOT INITIAL.
       DATA lt_processed_updates TYPE tt_dttsit2.
       me->execute_reprocess( EXPORTING it_keys = lt_keys_to_reprocess
                              IMPORTING et_update_buffer = lt_processed_updates ).

       LOOP AT lt_processed_updates INTO DATA(ls_proc).
         READ TABLE lcl_buffer=>mt_update ASSIGNING FIELD-SYMBOL(<fs_buf>) WITH KEY tran_id = ls_proc-tran_id item_no = ls_proc-item_no.
         IF sy-subrc = 0.
            <fs_buf>-zeile = ls_proc-zeile.
            <fs_buf>-product = ls_proc-product.
            <fs_buf>-prod_name = ls_proc-prod_name.
            <fs_buf>-prodqty = ls_proc-prodqty.
            <fs_buf>-prod_unit = ls_proc-prod_unit.
            <fs_buf>-gtin = ls_proc-gtin.
            <fs_buf>-batch = ls_proc-batch.
            <fs_buf>-expdate = ls_proc-expdate.
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
               <fs_create>-prodqty = ls_proc-prodqty.
               <fs_create>-prod_unit = ls_proc-prod_unit.
               <fs_create>-gtin = ls_proc-gtin.
               <fs_create>-batch = ls_proc-batch.
               <fs_create>-expdate = ls_proc-expdate.
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
        WHERE doc_year = @keys-doc_year AND mat_doc = @keys-matdoc AND mvt_type = @keys-mvttype AND item_no = @keys-item_no
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
       APPEND VALUE #( doc_year = ls_key-doc_year matdoc = ls_key-matdoc mvttype = ls_key-mvttype item_no = ls_key-item_no ) TO lt_keys_to_reprocess.
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
            <fs_buf>-prodqty = ls_proc-prodqty.
            <fs_buf>-prod_unit = ls_proc-prod_unit.
            <fs_buf>-gtin = ls_proc-gtin.
            <fs_buf>-batch = ls_proc-batch.
            <fs_buf>-expdate = ls_proc-expdate.
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
     SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @rs_err
       WHERE tran_id = @is_item-%data-tran_id AND item_no = @is_item-%data-item_no.

     rs_err-mandt = sy-mandt.
     rs_err-tran_id = is_item-%data-tran_id.
     rs_err-item_no = is_item-%data-item_no.
     rs_err-zeile = is_item-%data-zeile.
     rs_err-product = is_item-%data-product.
     rs_err-prod_name = is_item-%data-prodname.
     rs_err-prodqty = is_item-%data-prodqty.
     rs_err-prod_unit = is_item-%data-produnit.
     rs_err-gtin = is_item-%data-gtin.
     rs_err-batch = is_item-%data-batch.
     rs_err-expdate = is_item-%data-expdate.
     rs_err-mat_doc = is_item-%data-matdoc.
     rs_err-mvt_type = is_item-%data-mvttype.

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
             doc_year TYPE mjahr,
             matdoc TYPE mblnr,
             mvttype TYPE bwart,
           END OF ty_header_key.
    DATA: lt_header_keys TYPE TABLE OF ty_header_key.

    DATA: lo_table_desc TYPE REF TO cl_abap_tabledescr,
          lo_line_desc TYPE REF TO cl_abap_datadescr,
          dref_line TYPE REF TO data,
          lv_all_success TYPE abap_bool VALUE abap_true,
          lv_item_gtin TYPE string,
          lv_resp_gtin TYPE string,
          ls_processed_dttsit2 TYPE zmm_sst_dttsit2,
          lv_desc TYPE char255.

    DATA: lv_gtin_fmt TYPE string,
          lv_qty_fmt TYPE string,
          lv_batch_fmt TYPE string,
          lv_exp_fmt TYPE string.

    LOOP AT it_keys INTO DATA(ls_key).
      APPEND VALUE #( doc_year = ls_key-doc_year matdoc = ls_key-matdoc mvttype = ls_key-mvttype ) TO lt_header_keys.
    ENDLOOP.
    SORT lt_header_keys BY doc_year matdoc mvttype.
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
                   <lt_resp_products> TYPE ANY TABLE,
                   <fs_req> TYPE any,
                   <fs_resp> TYPE any,
                   <lv_fromgln> TYPE any,
                   <lv_togln> TYPE any,
                   <lv_authgln> TYPE any,
                   <fs_prod_list> TYPE any.

    LOOP AT lt_header_keys INTO DATA(ls_hdr_key).
      CLEAR: lt_header, lt_items.

      LOOP AT it_keys INTO DATA(ls_k) WHERE doc_year = ls_hdr_key-doc_year AND mat_doc = ls_hdr_key-matdoc AND mvt_type = ls_hdr_key-mvttype.
        DATA ls_item_st TYPE tt_is_item.

        SELECT SINGLE tran_id FROM zr_mm_dtts_cockpit INTO @DATA(lv_t)
          WHERE doc_year = @ls_k-doc_year AND mat_doc = @ls_k-matdoc AND mvt_type = @ls_k-mvttype AND item_no = @ls_k-item_no.

        READ TABLE lcl_buffer=>mt_create INTO DATA(ls_buf) WITH KEY tran_id = lv_t item_no = ls_k-item_no.
        IF sy-subrc = 0.
           ls_item_st = CORRESPONDING #( ls_buf MAPPING prodname = prod_name prodqty = prod_qty produnit = prod_unit expdate = exp_date notifid = notif_id trresponse = tr_response srnumber = sr_number createddate = created_date createdtime = created_time createdby = created_by changeddate = changed_date changedtime = changed_time changedby = changed_by prodstat = prod_stat transstat = trans_stat ).
           ls_item_st-%data-doc_year = ls_k-doc_year.
           APPEND ls_item_st TO lt_items.
        ELSE.
           READ TABLE lcl_buffer=>mt_update INTO ls_buf WITH KEY tran_id = lv_t item_no = ls_k-item_no.
           IF sy-subrc = 0.
             ls_item_st = CORRESPONDING #( ls_buf MAPPING prodname = prod_name prodqty = prod_qty produnit = prod_unit expdate = exp_date notifid = notif_id trresponse = tr_response srnumber = sr_number createddate = created_date createdtime = created_time createdby = created_by changeddate = changed_date changedtime = changed_time changedby = changed_by prodstat = prod_stat transstat = trans_stat ).
             ls_item_st-%data-doc_year = ls_k-doc_year.
             APPEND ls_item_st TO lt_items.
           ELSE.
             SELECT SINGLE * FROM zr_mm_dtts_cockpit INTO @DATA(ls_db)
               WHERE doc_year = @ls_k-doc_year AND mat_doc = @ls_k-matdoc AND mvt_type = @ls_k-mvttype AND item_no = @ls_k-item_no.
             IF sy-subrc = 0.
               ls_item_st = CORRESPONDING #( ls_db ).
               APPEND ls_item_st TO lt_items.
             ENDIF.
           ENDIF.
        ENDIF.
      ENDLOOP.

      IF lt_items IS NOT INITIAL.
        SELECT * FROM zmm_sst_dtts_hdr INTO TABLE @lt_header
          WHERE mat_doc = @ls_hdr_key-matdoc AND doc_yr = @ls_hdr_key-doc_year AND mvt_type = @ls_hdr_key-mvttype.

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
              ASSIGN COMPONENT 'ACCEPT_BATCH_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_ACC>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<lv_fromgln_ACC>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL. <lv_fromgln_ACC> = lt_items[ 1 ]-frm_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_fromgln_ACC> = lt_header[ 1 ]-frm_gln. ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<lv_togln_ACC>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_ACC> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_ACC> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'ACCEPT' = 'DRUG_SALE' OR 'ACCEPT' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_ACC> IS INITIAL OR <lv_togln_ACC> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_ACC> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<lv_authgln_ACC>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'ACCEPT' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_ACC> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_ACC> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<lv_doc_ACC>).
                IF sy-subrc = 0. <lv_doc_ACC> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<lv_pat_ACC>).
                IF sy-subrc = 0. <lv_pat_ACC> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<lv_presc_ACC>).
                IF sy-subrc = 0. <lv_presc_ACC> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<lv_pdate_ACC>).
                IF sy-subrc = 0. <lv_pdate_ACC> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<lv_dr_ACC>).
                IF sy-subrc = 0. <lv_dr_ACC> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<lv_exp_ACC>).
                IF sy-subrc = 0. <lv_exp_ACC> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_ACC> TO FIELD-SYMBOL(<fs_prod_list_ACC>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_ACC> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_ACC).
                            IF ls_item_ACC-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_ACC-%data-gtin ) p_quantity_in = CONV #( ls_item_ACC-%data-prodqty ) p_batch_in = CONV #( ls_item_ACC-%data-batch ) p_exp_date_in = CONV #( ls_item_ACC-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_ACC>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_ACC> TO FIELD-SYMBOL(<l_gtin_ACC>).
                            IF sy-subrc = 0. <l_gtin_ACC> = lv_gtin_fmt. ENDIF.



                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_ACC> TO FIELD-SYMBOL(<l_qty_ACC>).
                            IF sy-subrc = 0. <l_qty_ACC> = lv_qty_fmt. ENDIF.

                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_ACC> TO FIELD-SYMBOL(<l_bn_ACC>).
                            IF sy-subrc = 0. <l_bn_ACC> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_ACC> TO FIELD-SYMBOL(<l_xd_ACC>).
                            IF sy-subrc = 0. <l_xd_ACC> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_ACC> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'RETURN'.
              ASSIGN COMPONENT 'RETURN_BATCH_SERVICE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_RET>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_RET> TO FIELD-SYMBOL(<lv_togln_RET>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_RET> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_RET> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'RETURN' = 'DRUG_SALE' OR 'RETURN' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_RET> IS INITIAL OR <lv_togln_RET> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_RET> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_RET> TO FIELD-SYMBOL(<lv_authgln_RET>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'RETURN' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_RET> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_RET> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_RET> TO FIELD-SYMBOL(<lv_doc_RET>).
                IF sy-subrc = 0. <lv_doc_RET> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_RET> TO FIELD-SYMBOL(<lv_pat_RET>).
                IF sy-subrc = 0. <lv_pat_RET> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_RET> TO FIELD-SYMBOL(<lv_presc_RET>).
                IF sy-subrc = 0. <lv_presc_RET> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_RET> TO FIELD-SYMBOL(<lv_pdate_RET>).
                IF sy-subrc = 0. <lv_pdate_RET> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_RET> TO FIELD-SYMBOL(<lv_dr_RET>).
                IF sy-subrc = 0. <lv_dr_RET> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_RET> TO FIELD-SYMBOL(<lv_exp_RET>).
                IF sy-subrc = 0. <lv_exp_RET> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_RET> TO FIELD-SYMBOL(<fs_prod_list_RET>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_RET> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_RET).
                            IF ls_item_RET-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_RET-%data-gtin ) p_quantity_in = CONV #( ls_item_RET-%data-prodqty ) p_batch_in = CONV #( ls_item_RET-%data-batch ) p_exp_date_in = CONV #( ls_item_RET-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_RET>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_RET> TO FIELD-SYMBOL(<l_gtin_RET>).
                            IF sy-subrc = 0. <l_gtin_RET> = lv_gtin_fmt. ENDIF.



                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_RET> TO FIELD-SYMBOL(<l_qty_RET>).
                            IF sy-subrc = 0. <l_qty_RET> = lv_qty_fmt. ENDIF.

                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_RET> TO FIELD-SYMBOL(<l_bn_RET>).
                            IF sy-subrc = 0. <l_bn_RET> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_RET> TO FIELD-SYMBOL(<l_xd_RET>).
                            IF sy-subrc = 0. <l_xd_RET> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_RET> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DISPATCH'.
              ASSIGN COMPONENT 'DISPATCH_BATCH_SERVICE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_DISP>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_DISP> TO FIELD-SYMBOL(<lv_togln_DISP>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_DISP> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_DISP> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'DISPATCH' = 'DRUG_SALE' OR 'DISPATCH' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_DISP> IS INITIAL OR <lv_togln_DISP> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_DISP> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_DISP> TO FIELD-SYMBOL(<lv_authgln_DISP>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'DISPATCH' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_DISP> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_DISP> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_DISP> TO FIELD-SYMBOL(<lv_doc_DISP>).
                IF sy-subrc = 0. <lv_doc_DISP> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_DISP> TO FIELD-SYMBOL(<lv_pat_DISP>).
                IF sy-subrc = 0. <lv_pat_DISP> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_DISP> TO FIELD-SYMBOL(<lv_presc_DISP>).
                IF sy-subrc = 0. <lv_presc_DISP> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_DISP> TO FIELD-SYMBOL(<lv_pdate_DISP>).
                IF sy-subrc = 0. <lv_pdate_DISP> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_DISP> TO FIELD-SYMBOL(<lv_dr_DISP>).
                IF sy-subrc = 0. <lv_dr_DISP> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_DISP> TO FIELD-SYMBOL(<lv_exp_DISP>).
                IF sy-subrc = 0. <lv_exp_DISP> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_DISP> TO FIELD-SYMBOL(<fs_prod_list_DISP>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_DISP> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_DISP).
                            IF ls_item_DISP-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_DISP-%data-gtin ) p_quantity_in = CONV #( ls_item_DISP-%data-prodqty ) p_batch_in = CONV #( ls_item_DISP-%data-batch ) p_exp_date_in = CONV #( ls_item_DISP-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_DISP>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_DISP> TO FIELD-SYMBOL(<l_gtin_DISP>).
                            IF sy-subrc = 0. <l_gtin_DISP> = lv_gtin_fmt. ENDIF.



                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_DISP> TO FIELD-SYMBOL(<l_qty_DISP>).
                            IF sy-subrc = 0. <l_qty_DISP> = lv_qty_fmt. ENDIF.

                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_DISP> TO FIELD-SYMBOL(<l_bn_DISP>).
                            IF sy-subrc = 0. <l_bn_DISP> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_DISP> TO FIELD-SYMBOL(<l_xd_DISP>).
                            IF sy-subrc = 0. <l_xd_DISP> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_DISP> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DISPATCH_CANCEL'.
              ASSIGN COMPONENT 'DISPATCH_CANCEL' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_DISP_CAN>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_DISP_CAN> TO FIELD-SYMBOL(<lv_togln_DISP_CAN>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_DISP_CAN> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_DISP_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'DISPATCH_CANCEL' = 'DRUG_SALE' OR 'DISPATCH_CANCEL' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_DISP_CAN> IS INITIAL OR <lv_togln_DISP_CAN> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_DISP_CAN> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_DISP_CAN> TO FIELD-SYMBOL(<lv_authgln_DISP_CAN>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'DISPATCH_CANCEL' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_DISP_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_DISP_CAN> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_DISP_CAN> TO FIELD-SYMBOL(<lv_doc_DISP_CAN>).
                IF sy-subrc = 0. <lv_doc_DISP_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_DISP_CAN> TO FIELD-SYMBOL(<lv_pat_DISP_CAN>).
                IF sy-subrc = 0. <lv_pat_DISP_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_DISP_CAN> TO FIELD-SYMBOL(<lv_presc_DISP_CAN>).
                IF sy-subrc = 0. <lv_presc_DISP_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_DISP_CAN> TO FIELD-SYMBOL(<lv_pdate_DISP_CAN>).
                IF sy-subrc = 0. <lv_pdate_DISP_CAN> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_DISP_CAN> TO FIELD-SYMBOL(<lv_dr_DISP_CAN>).
                IF sy-subrc = 0. <lv_dr_DISP_CAN> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_DISP_CAN> TO FIELD-SYMBOL(<lv_exp_DISP_CAN>).
                IF sy-subrc = 0. <lv_exp_DISP_CAN> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_DISP_CAN> TO FIELD-SYMBOL(<fs_prod_list_DISP_CAN>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_DISP_CAN> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_DISP_CAN).
                            IF ls_item_DISP_CAN-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_DISP_CAN-%data-gtin ) p_quantity_in = CONV #( ls_item_DISP_CAN-%data-prodqty ) p_batch_in = CONV #( ls_item_DISP_CAN-%data-batch ) p_exp_date_in = CONV #( ls_item_DISP_CAN-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_DISP_CAN>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_DISP_CAN> TO FIELD-SYMBOL(<l_gtin_DISP_CAN>).
                            IF sy-subrc = 0. <l_gtin_DISP_CAN> = lv_gtin_fmt. ENDIF.

                            ASSIGN COMPONENT 'SN' OF STRUCTURE <ls_product_line_DISP_CAN> TO FIELD-SYMBOL(<l_sn_DISP_CAN>).
                            IF sy-subrc = 0. <l_sn_DISP_CAN> = ls_item_DISP_CAN-%data-srnumber. ENDIF.



                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_DISP_CAN> TO FIELD-SYMBOL(<l_bn_DISP_CAN>).
                            IF sy-subrc = 0. <l_bn_DISP_CAN> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_DISP_CAN> TO FIELD-SYMBOL(<l_xd_DISP_CAN>).
                            IF sy-subrc = 0. <l_xd_DISP_CAN> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_DISP_CAN> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'TRANSFER'.
              ASSIGN COMPONENT 'TRANSFER_BATCH_SERVICE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_TRAN>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_TRAN> TO FIELD-SYMBOL(<lv_togln_TRAN>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_TRAN> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_TRAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'TRANSFER' = 'DRUG_SALE' OR 'TRANSFER' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_TRAN> IS INITIAL OR <lv_togln_TRAN> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_TRAN> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_TRAN> TO FIELD-SYMBOL(<lv_authgln_TRAN>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'TRANSFER' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_TRAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_TRAN> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_TRAN> TO FIELD-SYMBOL(<lv_doc_TRAN>).
                IF sy-subrc = 0. <lv_doc_TRAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_TRAN> TO FIELD-SYMBOL(<lv_pat_TRAN>).
                IF sy-subrc = 0. <lv_pat_TRAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_TRAN> TO FIELD-SYMBOL(<lv_presc_TRAN>).
                IF sy-subrc = 0. <lv_presc_TRAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_TRAN> TO FIELD-SYMBOL(<lv_pdate_TRAN>).
                IF sy-subrc = 0. <lv_pdate_TRAN> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_TRAN> TO FIELD-SYMBOL(<lv_dr_TRAN>).
                IF sy-subrc = 0. <lv_dr_TRAN> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_TRAN> TO FIELD-SYMBOL(<lv_exp_TRAN>).
                IF sy-subrc = 0. <lv_exp_TRAN> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_TRAN> TO FIELD-SYMBOL(<fs_prod_list_TRAN>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_TRAN> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_TRAN).
                            IF ls_item_TRAN-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_TRAN-%data-gtin ) p_quantity_in = CONV #( ls_item_TRAN-%data-prodqty ) p_batch_in = CONV #( ls_item_TRAN-%data-batch ) p_exp_date_in = CONV #( ls_item_TRAN-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_TRAN>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_TRAN> TO FIELD-SYMBOL(<l_gtin_TRAN>).
                            IF sy-subrc = 0. <l_gtin_TRAN> = lv_gtin_fmt. ENDIF.



                            ASSIGN COMPONENT 'QUANTITY' OF STRUCTURE <ls_product_line_TRAN> TO FIELD-SYMBOL(<l_qty_TRAN>).
                            IF sy-subrc = 0. <l_qty_TRAN> = lv_qty_fmt. ENDIF.

                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_TRAN> TO FIELD-SYMBOL(<l_bn_TRAN>).
                            IF sy-subrc = 0. <l_bn_TRAN> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_TRAN> TO FIELD-SYMBOL(<l_xd_TRAN>).
                            IF sy-subrc = 0. <l_xd_TRAN> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_TRAN> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'TRANSFER_CANCEL'.
              ASSIGN COMPONENT 'TRANSFER_CANCEL' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_TRAN_CAN>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_TRAN_CAN> TO FIELD-SYMBOL(<lv_togln_TRAN_CAN>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_TRAN_CAN> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_TRAN_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'TRANSFER_CANCEL' = 'DRUG_SALE' OR 'TRANSFER_CANCEL' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_TRAN_CAN> IS INITIAL OR <lv_togln_TRAN_CAN> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_TRAN_CAN> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_TRAN_CAN> TO FIELD-SYMBOL(<lv_authgln_TRAN_CAN>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'TRANSFER_CANCEL' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_TRAN_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_TRAN_CAN> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_TRAN_CAN> TO FIELD-SYMBOL(<lv_doc_TRAN_CAN>).
                IF sy-subrc = 0. <lv_doc_TRAN_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_TRAN_CAN> TO FIELD-SYMBOL(<lv_pat_TRAN_CAN>).
                IF sy-subrc = 0. <lv_pat_TRAN_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_TRAN_CAN> TO FIELD-SYMBOL(<lv_presc_TRAN_CAN>).
                IF sy-subrc = 0. <lv_presc_TRAN_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_TRAN_CAN> TO FIELD-SYMBOL(<lv_pdate_TRAN_CAN>).
                IF sy-subrc = 0. <lv_pdate_TRAN_CAN> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_TRAN_CAN> TO FIELD-SYMBOL(<lv_dr_TRAN_CAN>).
                IF sy-subrc = 0. <lv_dr_TRAN_CAN> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_TRAN_CAN> TO FIELD-SYMBOL(<lv_exp_TRAN_CAN>).
                IF sy-subrc = 0. <lv_exp_TRAN_CAN> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_TRAN_CAN> TO FIELD-SYMBOL(<fs_prod_list_TRAN_CAN>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_TRAN_CAN> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_TRAN_CAN).
                            IF ls_item_TRAN_CAN-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_TRAN_CAN-%data-gtin ) p_quantity_in = CONV #( ls_item_TRAN_CAN-%data-prodqty ) p_batch_in = CONV #( ls_item_TRAN_CAN-%data-batch ) p_exp_date_in = CONV #( ls_item_TRAN_CAN-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_TRAN_CAN>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_TRAN_CAN> TO FIELD-SYMBOL(<l_gtin_TRAN_CAN>).
                            IF sy-subrc = 0. <l_gtin_TRAN_CAN> = lv_gtin_fmt. ENDIF.

                            ASSIGN COMPONENT 'SN' OF STRUCTURE <ls_product_line_TRAN_CAN> TO FIELD-SYMBOL(<l_sn_TRAN_CAN>).
                            IF sy-subrc = 0. <l_sn_TRAN_CAN> = ls_item_TRAN_CAN-%data-srnumber. ENDIF.



                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_TRAN_CAN> TO FIELD-SYMBOL(<l_bn_TRAN_CAN>).
                            IF sy-subrc = 0. <l_bn_TRAN_CAN> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_TRAN_CAN> TO FIELD-SYMBOL(<l_xd_TRAN_CAN>).
                            IF sy-subrc = 0. <l_xd_TRAN_CAN> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_TRAN_CAN> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'CONSUME'.
              ASSIGN COMPONENT 'CONSUME_SERVICE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_CONS>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_CONS> TO FIELD-SYMBOL(<lv_togln_CONS>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_CONS> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_CONS> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'CONSUME' = 'DRUG_SALE' OR 'CONSUME' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_CONS> IS INITIAL OR <lv_togln_CONS> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_CONS> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_CONS> TO FIELD-SYMBOL(<lv_authgln_CONS>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'CONSUME' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_CONS> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_CONS> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_CONS> TO FIELD-SYMBOL(<lv_doc_CONS>).
                IF sy-subrc = 0. <lv_doc_CONS> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_CONS> TO FIELD-SYMBOL(<lv_pat_CONS>).
                IF sy-subrc = 0. <lv_pat_CONS> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_CONS> TO FIELD-SYMBOL(<lv_presc_CONS>).
                IF sy-subrc = 0. <lv_presc_CONS> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_CONS> TO FIELD-SYMBOL(<lv_pdate_CONS>).
                IF sy-subrc = 0. <lv_pdate_CONS> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_CONS> TO FIELD-SYMBOL(<lv_dr_CONS>).
                IF sy-subrc = 0. <lv_dr_CONS> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_CONS> TO FIELD-SYMBOL(<lv_exp_CONS>).
                IF sy-subrc = 0. <lv_exp_CONS> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_CONS> TO FIELD-SYMBOL(<fs_prod_list_CONS>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_CONS> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_CONS).
                            IF ls_item_CONS-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_CONS-%data-gtin ) p_quantity_in = CONV #( ls_item_CONS-%data-prodqty ) p_batch_in = CONV #( ls_item_CONS-%data-batch ) p_exp_date_in = CONV #( ls_item_CONS-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_CONS>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_CONS> TO FIELD-SYMBOL(<l_gtin_CONS>).
                            IF sy-subrc = 0. <l_gtin_CONS> = lv_gtin_fmt. ENDIF.

                            ASSIGN COMPONENT 'SN' OF STRUCTURE <ls_product_line_CONS> TO FIELD-SYMBOL(<l_sn_CONS>).
                            IF sy-subrc = 0. <l_sn_CONS> = ls_item_CONS-%data-srnumber. ENDIF.



                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_CONS> TO FIELD-SYMBOL(<l_bn_CONS>).
                            IF sy-subrc = 0. <l_bn_CONS> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_CONS> TO FIELD-SYMBOL(<l_xd_CONS>).
                            IF sy-subrc = 0. <l_xd_CONS> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_CONS> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'CONSUME_CANCEL'.
              ASSIGN COMPONENT 'CONSUME_CANCEL' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_CONS_CAN>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_CONS_CAN> TO FIELD-SYMBOL(<lv_togln_CONS_CAN>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_CONS_CAN> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_CONS_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'CONSUME_CANCEL' = 'DRUG_SALE' OR 'CONSUME_CANCEL' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_CONS_CAN> IS INITIAL OR <lv_togln_CONS_CAN> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_CONS_CAN> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_CONS_CAN> TO FIELD-SYMBOL(<lv_authgln_CONS_CAN>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'CONSUME_CANCEL' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_CONS_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_CONS_CAN> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_CONS_CAN> TO FIELD-SYMBOL(<lv_doc_CONS_CAN>).
                IF sy-subrc = 0. <lv_doc_CONS_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_CONS_CAN> TO FIELD-SYMBOL(<lv_pat_CONS_CAN>).
                IF sy-subrc = 0. <lv_pat_CONS_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_CONS_CAN> TO FIELD-SYMBOL(<lv_presc_CONS_CAN>).
                IF sy-subrc = 0. <lv_presc_CONS_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_CONS_CAN> TO FIELD-SYMBOL(<lv_pdate_CONS_CAN>).
                IF sy-subrc = 0. <lv_pdate_CONS_CAN> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_CONS_CAN> TO FIELD-SYMBOL(<lv_dr_CONS_CAN>).
                IF sy-subrc = 0. <lv_dr_CONS_CAN> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_CONS_CAN> TO FIELD-SYMBOL(<lv_exp_CONS_CAN>).
                IF sy-subrc = 0. <lv_exp_CONS_CAN> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_CONS_CAN> TO FIELD-SYMBOL(<fs_prod_list_CONS_CAN>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_CONS_CAN> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_CONS_CAN).
                            IF ls_item_CONS_CAN-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_CONS_CAN-%data-gtin ) p_quantity_in = CONV #( ls_item_CONS_CAN-%data-prodqty ) p_batch_in = CONV #( ls_item_CONS_CAN-%data-batch ) p_exp_date_in = CONV #( ls_item_CONS_CAN-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_CONS_CAN>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_CONS_CAN> TO FIELD-SYMBOL(<l_gtin_CONS_CAN>).
                            IF sy-subrc = 0. <l_gtin_CONS_CAN> = lv_gtin_fmt. ENDIF.

                            ASSIGN COMPONENT 'SN' OF STRUCTURE <ls_product_line_CONS_CAN> TO FIELD-SYMBOL(<l_sn_CONS_CAN>).
                            IF sy-subrc = 0. <l_sn_CONS_CAN> = ls_item_CONS_CAN-%data-srnumber. ENDIF.



                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_CONS_CAN> TO FIELD-SYMBOL(<l_bn_CONS_CAN>).
                            IF sy-subrc = 0. <l_bn_CONS_CAN> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_CONS_CAN> TO FIELD-SYMBOL(<l_xd_CONS_CAN>).
                            IF sy-subrc = 0. <l_xd_CONS_CAN> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_CONS_CAN> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DRUG_SALE'.
              ASSIGN COMPONENT 'PHARMACY_SALE' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_SALE>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_SALE> TO FIELD-SYMBOL(<lv_togln_SALE>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_SALE> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_SALE> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'DRUG_SALE' = 'DRUG_SALE' OR 'DRUG_SALE' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_SALE> IS INITIAL OR <lv_togln_SALE> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_SALE> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_SALE> TO FIELD-SYMBOL(<lv_authgln_SALE>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'DRUG_SALE' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_SALE> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_SALE> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_SALE> TO FIELD-SYMBOL(<lv_doc_SALE>).
                IF sy-subrc = 0. <lv_doc_SALE> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_SALE> TO FIELD-SYMBOL(<lv_pat_SALE>).
                IF sy-subrc = 0. <lv_pat_SALE> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_SALE> TO FIELD-SYMBOL(<lv_presc_SALE>).
                IF sy-subrc = 0. <lv_presc_SALE> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_SALE> TO FIELD-SYMBOL(<lv_pdate_SALE>).
                IF sy-subrc = 0. <lv_pdate_SALE> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_SALE> TO FIELD-SYMBOL(<lv_dr_SALE>).
                IF sy-subrc = 0. <lv_dr_SALE> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_SALE> TO FIELD-SYMBOL(<lv_exp_SALE>).
                IF sy-subrc = 0. <lv_exp_SALE> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_SALE> TO FIELD-SYMBOL(<fs_prod_list_SALE>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_SALE> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_SALE).
                            IF ls_item_SALE-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_SALE-%data-gtin ) p_quantity_in = CONV #( ls_item_SALE-%data-prodqty ) p_batch_in = CONV #( ls_item_SALE-%data-batch ) p_exp_date_in = CONV #( ls_item_SALE-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_SALE>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_SALE> TO FIELD-SYMBOL(<l_gtin_SALE>).
                            IF sy-subrc = 0. <l_gtin_SALE> = lv_gtin_fmt. ENDIF.

                            ASSIGN COMPONENT 'SN' OF STRUCTURE <ls_product_line_SALE> TO FIELD-SYMBOL(<l_sn_SALE>).
                            IF sy-subrc = 0. <l_sn_SALE> = ls_item_SALE-%data-srnumber. ENDIF.



                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_SALE> TO FIELD-SYMBOL(<l_bn_SALE>).
                            IF sy-subrc = 0. <l_bn_SALE> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_SALE> TO FIELD-SYMBOL(<l_xd_SALE>).
                            IF sy-subrc = 0. <l_xd_SALE> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_SALE> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DRUG_SALE_CANCEL'.
              ASSIGN COMPONENT 'PHARMACY_SALE_CANCEL' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_SALE_CAN>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_SALE_CAN> TO FIELD-SYMBOL(<lv_togln_SALE_CAN>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_SALE_CAN> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_SALE_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'DRUG_SALE_CANCEL' = 'DRUG_SALE' OR 'DRUG_SALE_CANCEL' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_SALE_CAN> IS INITIAL OR <lv_togln_SALE_CAN> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_SALE_CAN> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_SALE_CAN> TO FIELD-SYMBOL(<lv_authgln_SALE_CAN>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'DRUG_SALE_CANCEL' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_SALE_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_SALE_CAN> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_SALE_CAN> TO FIELD-SYMBOL(<lv_doc_SALE_CAN>).
                IF sy-subrc = 0. <lv_doc_SALE_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_SALE_CAN> TO FIELD-SYMBOL(<lv_pat_SALE_CAN>).
                IF sy-subrc = 0. <lv_pat_SALE_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_SALE_CAN> TO FIELD-SYMBOL(<lv_presc_SALE_CAN>).
                IF sy-subrc = 0. <lv_presc_SALE_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_SALE_CAN> TO FIELD-SYMBOL(<lv_pdate_SALE_CAN>).
                IF sy-subrc = 0. <lv_pdate_SALE_CAN> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_SALE_CAN> TO FIELD-SYMBOL(<lv_dr_SALE_CAN>).
                IF sy-subrc = 0. <lv_dr_SALE_CAN> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_SALE_CAN> TO FIELD-SYMBOL(<lv_exp_SALE_CAN>).
                IF sy-subrc = 0. <lv_exp_SALE_CAN> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_SALE_CAN> TO FIELD-SYMBOL(<fs_prod_list_SALE_CAN>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_SALE_CAN> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_SALE_CAN).
                            IF ls_item_SALE_CAN-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_SALE_CAN-%data-gtin ) p_quantity_in = CONV #( ls_item_SALE_CAN-%data-prodqty ) p_batch_in = CONV #( ls_item_SALE_CAN-%data-batch ) p_exp_date_in = CONV #( ls_item_SALE_CAN-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_SALE_CAN>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_SALE_CAN> TO FIELD-SYMBOL(<l_gtin_SALE_CAN>).
                            IF sy-subrc = 0. <l_gtin_SALE_CAN> = lv_gtin_fmt. ENDIF.

                            ASSIGN COMPONENT 'SN' OF STRUCTURE <ls_product_line_SALE_CAN> TO FIELD-SYMBOL(<l_sn_SALE_CAN>).
                            IF sy-subrc = 0. <l_sn_SALE_CAN> = ls_item_SALE_CAN-%data-srnumber. ENDIF.



                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_SALE_CAN> TO FIELD-SYMBOL(<l_bn_SALE_CAN>).
                            IF sy-subrc = 0. <l_bn_SALE_CAN> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_SALE_CAN> TO FIELD-SYMBOL(<l_xd_SALE_CAN>).
                            IF sy-subrc = 0. <l_xd_SALE_CAN> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_SALE_CAN> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DEACTIVATE'.
              ASSIGN COMPONENT 'DEACTIVATION_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_DEAC>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_DEAC> TO FIELD-SYMBOL(<lv_togln_DEAC>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_DEAC> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_DEAC> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'DEACTIVATE' = 'DRUG_SALE' OR 'DEACTIVATE' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_DEAC> IS INITIAL OR <lv_togln_DEAC> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_DEAC> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_DEAC> TO FIELD-SYMBOL(<lv_authgln_DEAC>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'DEACTIVATE' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_DEAC> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_DEAC> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_DEAC> TO FIELD-SYMBOL(<lv_doc_DEAC>).
                IF sy-subrc = 0. <lv_doc_DEAC> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_DEAC> TO FIELD-SYMBOL(<lv_pat_DEAC>).
                IF sy-subrc = 0. <lv_pat_DEAC> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_DEAC> TO FIELD-SYMBOL(<lv_presc_DEAC>).
                IF sy-subrc = 0. <lv_presc_DEAC> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_DEAC> TO FIELD-SYMBOL(<lv_pdate_DEAC>).
                IF sy-subrc = 0. <lv_pdate_DEAC> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_DEAC> TO FIELD-SYMBOL(<lv_dr_DEAC>).
                IF sy-subrc = 0. <lv_dr_DEAC> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_DEAC> TO FIELD-SYMBOL(<lv_exp_DEAC>).
                IF sy-subrc = 0. <lv_exp_DEAC> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_DEAC> TO FIELD-SYMBOL(<fs_prod_list_DEAC>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_DEAC> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_DEAC).
                            IF ls_item_DEAC-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_DEAC-%data-gtin ) p_quantity_in = CONV #( ls_item_DEAC-%data-prodqty ) p_batch_in = CONV #( ls_item_DEAC-%data-batch ) p_exp_date_in = CONV #( ls_item_DEAC-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_DEAC>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_DEAC> TO FIELD-SYMBOL(<l_gtin_DEAC>).
                            IF sy-subrc = 0. <l_gtin_DEAC> = lv_gtin_fmt. ENDIF.

                            ASSIGN COMPONENT 'SN' OF STRUCTURE <ls_product_line_DEAC> TO FIELD-SYMBOL(<l_sn_DEAC>).
                            IF sy-subrc = 0. <l_sn_DEAC> = ls_item_DEAC-%data-srnumber. ENDIF.



                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_DEAC> TO FIELD-SYMBOL(<l_bn_DEAC>).
                            IF sy-subrc = 0. <l_bn_DEAC> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_DEAC> TO FIELD-SYMBOL(<l_xd_DEAC>).
                            IF sy-subrc = 0. <l_xd_DEAC> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_DEAC> INTO TABLE <lt_products>.
                          ENDLOOP.
                        CATCH cx_root.
                      ENDTRY.
                   ENDIF.
                ENDIF.
              ENDIF.

            WHEN 'DEACTIVATE_CANCEL'.
              ASSIGN COMPONENT 'DEACTIVATION_CANCEL' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_req_DEAC_CAN>).
              IF sy-subrc = 0.
                " --- GLN Assignments ---


                ASSIGN COMPONENT 'TOGLN' OF STRUCTURE <fs_req_DEAC_CAN> TO FIELD-SYMBOL(<lv_togln_DEAC_CAN>).
                IF sy-subrc = 0.
                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL. <lv_togln_DEAC_CAN> = lt_items[ 1 ]-to_gln.
                   ELSEIF lt_header IS NOT INITIAL. <lv_togln_DEAC_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   " Specific override for DRUG_SALE logic in proxy
                   IF 'DEACTIVATE_CANCEL' = 'DRUG_SALE' OR 'DEACTIVATE_CANCEL' = 'DRUG_SALE_CANCEL'.
                     IF <lv_togln_DEAC_CAN> IS INITIAL OR <lv_togln_DEAC_CAN> = lt_header[ 1 ]-frm_gln.
                       <lv_togln_DEAC_CAN> = '0000000000000'.
                     ENDIF.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_req_DEAC_CAN> TO FIELD-SYMBOL(<lv_authgln_DEAC_CAN>).
                IF sy-subrc = 0.
                   " For DISPATCH, TRANSFER, RETURN, CONSUME, DRUG_SALE, authgln is typically frm_gln.
                   IF 'DEACTIVATE_CANCEL' = 'ACCEPT'.
                     IF lt_header IS NOT INITIAL. <lv_authgln_DEAC_CAN> = lt_header[ 1 ]-to_gln. ENDIF.
                   ELSE.
                     IF lt_header IS NOT INITIAL. <lv_authgln_DEAC_CAN> = lt_header[ 1 ]-frm_gln. ENDIF.
                   ENDIF.
                ENDIF.

                " --- Special Constants for certain operations ---
                ASSIGN COMPONENT 'DOCTORID' OF STRUCTURE <fs_req_DEAC_CAN> TO FIELD-SYMBOL(<lv_doc_DEAC_CAN>).
                IF sy-subrc = 0. <lv_doc_DEAC_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PATIENTNATIONALID' OF STRUCTURE <fs_req_DEAC_CAN> TO FIELD-SYMBOL(<lv_pat_DEAC_CAN>).
                IF sy-subrc = 0. <lv_pat_DEAC_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONID' OF STRUCTURE <fs_req_DEAC_CAN> TO FIELD-SYMBOL(<lv_presc_DEAC_CAN>).
                IF sy-subrc = 0. <lv_presc_DEAC_CAN> = 'NA'. ENDIF.

                ASSIGN COMPONENT 'PRESCRIPTIONDATE' OF STRUCTURE <fs_req_DEAC_CAN> TO FIELD-SYMBOL(<lv_pdate_DEAC_CAN>).
                IF sy-subrc = 0. <lv_pdate_DEAC_CAN> = |{ sy-datum(4) }-{ sy-datum+4(2) }-{ sy-datum+6(2) }|. ENDIF.

                ASSIGN COMPONENT 'DR' OF STRUCTURE <fs_req_DEAC_CAN> TO FIELD-SYMBOL(<lv_dr_DEAC_CAN>).
                IF sy-subrc = 0. <lv_dr_DEAC_CAN> = '30'. ENDIF. " Default GRUND if missing in mseg

                ASSIGN COMPONENT 'EXPLANATION' OF STRUCTURE <fs_req_DEAC_CAN> TO FIELD-SYMBOL(<lv_exp_DEAC_CAN>).
                IF sy-subrc = 0. <lv_exp_DEAC_CAN> = 'Damaged Product'. ENDIF.

                " --- Product List Mapping ---
                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_req_DEAC_CAN> TO FIELD-SYMBOL(<fs_prod_list_DEAC_CAN>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list_DEAC_CAN> TO <lt_products>.
                   IF sy-subrc = 0.
                      TRY.
                          lo_table_desc ?= cl_abap_typedescr=>describe_by_data( <lt_products> ).
                          lo_line_desc = lo_table_desc->get_table_line_type( ).

                          LOOP AT lt_items INTO DATA(ls_item_DEAC_CAN).
                            IF ls_item_DEAC_CAN-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                            me->format_data( EXPORTING p_gtin_in = CONV #( ls_item_DEAC_CAN-%data-gtin ) p_quantity_in = CONV #( ls_item_DEAC_CAN-%data-prodqty ) p_batch_in = CONV #( ls_item_DEAC_CAN-%data-batch ) p_exp_date_in = CONV #( ls_item_DEAC_CAN-%data-expdate )
                                             IMPORTING p_gtin_out = lv_gtin_fmt p_quantity_out = lv_qty_fmt p_batch_out = lv_batch_fmt p_exp_date_out = lv_exp_fmt ).

                            CREATE DATA dref_line TYPE HANDLE lo_line_desc.
                            ASSIGN dref_line->* TO FIELD-SYMBOL(<ls_product_line_DEAC_CAN>).

                            ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_product_line_DEAC_CAN> TO FIELD-SYMBOL(<l_gtin_DEAC_CAN>).
                            IF sy-subrc = 0. <l_gtin_DEAC_CAN> = lv_gtin_fmt. ENDIF.

                            ASSIGN COMPONENT 'SN' OF STRUCTURE <ls_product_line_DEAC_CAN> TO FIELD-SYMBOL(<l_sn_DEAC_CAN>).
                            IF sy-subrc = 0. <l_sn_DEAC_CAN> = ls_item_DEAC_CAN-%data-srnumber. ENDIF.



                            ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_product_line_DEAC_CAN> TO FIELD-SYMBOL(<l_bn_DEAC_CAN>).
                            IF sy-subrc = 0. <l_bn_DEAC_CAN> = lv_batch_fmt. ENDIF.

                            ASSIGN COMPONENT 'XD' OF STRUCTURE <ls_product_line_DEAC_CAN> TO FIELD-SYMBOL(<l_xd_DEAC_CAN>).
                            IF sy-subrc = 0. <l_xd_DEAC_CAN> = lv_exp_fmt. ENDIF.

                            INSERT <ls_product_line_DEAC_CAN> INTO TABLE <lt_products>.
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

              lv_all_success = abap_true.

              CASE lv_operation.

                WHEN 'ACCEPT'.
                  ASSIGN COMPONENT 'ACCEPT_BATCH_SERVICE_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_ACC>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_ACC> TO FIELD-SYMBOL(<lv_notif_id_ACC>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_ACC> TO FIELD-SYMBOL(<fs_resp_prod_list_ACC>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_ACC> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_ACC>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_ACC> TO FIELD-SYMBOL(<r_gtin_ACC>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_ACC> TO FIELD-SYMBOL(<r_bn_ACC>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_ACC> TO FIELD-SYMBOL(<r_rc_ACC>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_ACC>).
                             IF <fs_item_ACC>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_ACC>-%data-gtin. lv_resp_gtin = <r_gtin_ACC>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_ACC>-%data-batch = <r_bn_ACC>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_ACC>-%data-tran_id AND item_no = @<fs_item_ACC>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_ACC>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_ACC>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_ACC>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_ACC>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_ACC>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_ACC>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_ACC>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_ACC>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_ACC>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_ACC>-%data-expdate.
                               IF <lv_notif_id_ACC> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_ACC>. ENDIF.
                               IF <r_rc_ACC> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_ACC>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_ACC>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_ACC>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_ACC> IS ASSIGNED AND <r_rc_ACC> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_ACC> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_ACC> ) IMPORTING p_description = lv_desc ). ENDIF.
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
                  ASSIGN COMPONENT 'RETURN_BATCH_SERVICE_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_RET>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_RET> TO FIELD-SYMBOL(<lv_notif_id_RET>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_RET> TO FIELD-SYMBOL(<fs_resp_prod_list_RET>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_RET> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_RET>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_RET> TO FIELD-SYMBOL(<r_gtin_RET>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_RET> TO FIELD-SYMBOL(<r_bn_RET>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_RET> TO FIELD-SYMBOL(<r_rc_RET>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_RET>).
                             IF <fs_item_RET>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_RET>-%data-gtin. lv_resp_gtin = <r_gtin_RET>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_RET>-%data-batch = <r_bn_RET>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_RET>-%data-tran_id AND item_no = @<fs_item_RET>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_RET>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_RET>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_RET>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_RET>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_RET>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_RET>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_RET>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_RET>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_RET>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_RET>-%data-expdate.
                               IF <lv_notif_id_RET> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_RET>. ENDIF.
                               IF <r_rc_RET> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_RET>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_RET>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_RET>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_RET> IS ASSIGNED AND <r_rc_RET> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_RET> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_RET> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'DISPATCH'.
                  ASSIGN COMPONENT 'DISPATCH_BATCH_SERVICE_RESPONS' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_DISP>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_DISP> TO FIELD-SYMBOL(<lv_notif_id_DISP>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_DISP> TO FIELD-SYMBOL(<fs_resp_prod_list_DISP>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_DISP> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_DISP>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_DISP> TO FIELD-SYMBOL(<r_gtin_DISP>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_DISP> TO FIELD-SYMBOL(<r_bn_DISP>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_DISP> TO FIELD-SYMBOL(<r_rc_DISP>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_DISP>).
                             IF <fs_item_DISP>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_DISP>-%data-gtin. lv_resp_gtin = <r_gtin_DISP>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_DISP>-%data-batch = <r_bn_DISP>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_DISP>-%data-tran_id AND item_no = @<fs_item_DISP>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_DISP>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_DISP>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_DISP>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_DISP>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_DISP>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_DISP>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_DISP>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_DISP>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_DISP>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_DISP>-%data-expdate.
                               IF <lv_notif_id_DISP> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_DISP>. ENDIF.
                               IF <r_rc_DISP> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_DISP>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_DISP>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_DISP>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_DISP> IS ASSIGNED AND <r_rc_DISP> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_DISP> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_DISP> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'DISPATCH_CANCEL'.
                  ASSIGN COMPONENT 'DISPATCH_CANCEL_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_DISP_CAN>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_DISP_CAN> TO FIELD-SYMBOL(<lv_notif_id_DISP_CAN>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_DISP_CAN> TO FIELD-SYMBOL(<fs_resp_prod_list_DISP_CAN>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_DISP_CAN> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_DISP_CAN>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_DISP_CAN> TO FIELD-SYMBOL(<r_gtin_DISP_CAN>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_DISP_CAN> TO FIELD-SYMBOL(<r_bn_DISP_CAN>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_DISP_CAN> TO FIELD-SYMBOL(<r_rc_DISP_CAN>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_DISP_CAN>).
                             IF <fs_item_DISP_CAN>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_DISP_CAN>-%data-gtin. lv_resp_gtin = <r_gtin_DISP_CAN>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_DISP_CAN>-%data-batch = <r_bn_DISP_CAN>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_DISP_CAN>-%data-tran_id AND item_no = @<fs_item_DISP_CAN>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_DISP_CAN>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_DISP_CAN>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_DISP_CAN>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_DISP_CAN>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_DISP_CAN>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_DISP_CAN>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_DISP_CAN>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_DISP_CAN>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_DISP_CAN>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_DISP_CAN>-%data-expdate.
                               IF <lv_notif_id_DISP_CAN> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_DISP_CAN>. ENDIF.
                               IF <r_rc_DISP_CAN> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_DISP_CAN>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_DISP_CAN>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_DISP_CAN>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_DISP_CAN> IS ASSIGNED AND <r_rc_DISP_CAN> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_DISP_CAN> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_DISP_CAN> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'TRANSFER'.
                  ASSIGN COMPONENT 'TRANSFER_BATCH_SERVICE_RESPONS' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_TRAN>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_TRAN> TO FIELD-SYMBOL(<lv_notif_id_TRAN>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_TRAN> TO FIELD-SYMBOL(<fs_resp_prod_list_TRAN>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_TRAN> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_TRAN>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_TRAN> TO FIELD-SYMBOL(<r_gtin_TRAN>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_TRAN> TO FIELD-SYMBOL(<r_bn_TRAN>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_TRAN> TO FIELD-SYMBOL(<r_rc_TRAN>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_TRAN>).
                             IF <fs_item_TRAN>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_TRAN>-%data-gtin. lv_resp_gtin = <r_gtin_TRAN>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_TRAN>-%data-batch = <r_bn_TRAN>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_TRAN>-%data-tran_id AND item_no = @<fs_item_TRAN>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_TRAN>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_TRAN>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_TRAN>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_TRAN>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_TRAN>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_TRAN>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_TRAN>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_TRAN>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_TRAN>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_TRAN>-%data-expdate.
                               IF <lv_notif_id_TRAN> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_TRAN>. ENDIF.
                               IF <r_rc_TRAN> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_TRAN>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_TRAN>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_TRAN>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_TRAN> IS ASSIGNED AND <r_rc_TRAN> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_TRAN> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_TRAN> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'TRANSFER_CANCEL'.
                  ASSIGN COMPONENT 'TRANSFER_CANCEL_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_TRAN_CAN>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_TRAN_CAN> TO FIELD-SYMBOL(<lv_notif_id_TRAN_CAN>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_TRAN_CAN> TO FIELD-SYMBOL(<fs_resp_prod_list_TRAN_CAN>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_TRAN_CAN> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_TRAN_CAN>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_TRAN_CAN> TO FIELD-SYMBOL(<r_gtin_TRAN_CAN>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_TRAN_CAN> TO FIELD-SYMBOL(<r_bn_TRAN_CAN>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_TRAN_CAN> TO FIELD-SYMBOL(<r_rc_TRAN_CAN>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_TRAN_CAN>).
                             IF <fs_item_TRAN_CAN>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_TRAN_CAN>-%data-gtin. lv_resp_gtin = <r_gtin_TRAN_CAN>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_TRAN_CAN>-%data-batch = <r_bn_TRAN_CAN>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_TRAN_CAN>-%data-tran_id AND item_no = @<fs_item_TRAN_CAN>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_TRAN_CAN>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_TRAN_CAN>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_TRAN_CAN>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_TRAN_CAN>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_TRAN_CAN>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_TRAN_CAN>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_TRAN_CAN>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_TRAN_CAN>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_TRAN_CAN>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_TRAN_CAN>-%data-expdate.
                               IF <lv_notif_id_TRAN_CAN> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_TRAN_CAN>. ENDIF.
                               IF <r_rc_TRAN_CAN> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_TRAN_CAN>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_TRAN_CAN>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_TRAN_CAN>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_TRAN_CAN> IS ASSIGNED AND <r_rc_TRAN_CAN> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_TRAN_CAN> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_TRAN_CAN> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'CONSUME'.
                  ASSIGN COMPONENT 'CONSUME_SERVICE_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_CONS>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_CONS> TO FIELD-SYMBOL(<lv_notif_id_CONS>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_CONS> TO FIELD-SYMBOL(<fs_resp_prod_list_CONS>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_CONS> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_CONS>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_CONS> TO FIELD-SYMBOL(<r_gtin_CONS>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_CONS> TO FIELD-SYMBOL(<r_bn_CONS>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_CONS> TO FIELD-SYMBOL(<r_rc_CONS>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_CONS>).
                             IF <fs_item_CONS>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_CONS>-%data-gtin. lv_resp_gtin = <r_gtin_CONS>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_CONS>-%data-batch = <r_bn_CONS>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_CONS>-%data-tran_id AND item_no = @<fs_item_CONS>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_CONS>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_CONS>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_CONS>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_CONS>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_CONS>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_CONS>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_CONS>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_CONS>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_CONS>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_CONS>-%data-expdate.
                               IF <lv_notif_id_CONS> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_CONS>. ENDIF.
                               IF <r_rc_CONS> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_CONS>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_CONS>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_CONS>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_CONS> IS ASSIGNED AND <r_rc_CONS> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_CONS> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_CONS> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'CONSUME_CANCEL'.
                  ASSIGN COMPONENT 'CONSUME_CANCEL_SERVICE_RESPONS' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_CONS_CAN>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_CONS_CAN> TO FIELD-SYMBOL(<lv_notif_id_CONS_CAN>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_CONS_CAN> TO FIELD-SYMBOL(<fs_resp_prod_list_CONS_CAN>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_CONS_CAN> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_CONS_CAN>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_CONS_CAN> TO FIELD-SYMBOL(<r_gtin_CONS_CAN>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_CONS_CAN> TO FIELD-SYMBOL(<r_bn_CONS_CAN>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_CONS_CAN> TO FIELD-SYMBOL(<r_rc_CONS_CAN>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_CONS_CAN>).
                             IF <fs_item_CONS_CAN>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_CONS_CAN>-%data-gtin. lv_resp_gtin = <r_gtin_CONS_CAN>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_CONS_CAN>-%data-batch = <r_bn_CONS_CAN>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_CONS_CAN>-%data-tran_id AND item_no = @<fs_item_CONS_CAN>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_CONS_CAN>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_CONS_CAN>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_CONS_CAN>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_CONS_CAN>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_CONS_CAN>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_CONS_CAN>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_CONS_CAN>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_CONS_CAN>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_CONS_CAN>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_CONS_CAN>-%data-expdate.
                               IF <lv_notif_id_CONS_CAN> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_CONS_CAN>. ENDIF.
                               IF <r_rc_CONS_CAN> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_CONS_CAN>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_CONS_CAN>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_CONS_CAN>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_CONS_CAN> IS ASSIGNED AND <r_rc_CONS_CAN> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_CONS_CAN> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_CONS_CAN> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'DRUG_SALE'.
                  ASSIGN COMPONENT 'PHARMACY_SALE_SERVICE_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_SALE>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_SALE> TO FIELD-SYMBOL(<lv_notif_id_SALE>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_SALE> TO FIELD-SYMBOL(<fs_resp_prod_list_SALE>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_SALE> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_SALE>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_SALE> TO FIELD-SYMBOL(<r_gtin_SALE>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_SALE> TO FIELD-SYMBOL(<r_bn_SALE>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_SALE> TO FIELD-SYMBOL(<r_rc_SALE>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_SALE>).
                             IF <fs_item_SALE>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_SALE>-%data-gtin. lv_resp_gtin = <r_gtin_SALE>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_SALE>-%data-batch = <r_bn_SALE>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_SALE>-%data-tran_id AND item_no = @<fs_item_SALE>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_SALE>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_SALE>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_SALE>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_SALE>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_SALE>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_SALE>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_SALE>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_SALE>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_SALE>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_SALE>-%data-expdate.
                               IF <lv_notif_id_SALE> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_SALE>. ENDIF.
                               IF <r_rc_SALE> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_SALE>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_SALE>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_SALE>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_SALE> IS ASSIGNED AND <r_rc_SALE> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_SALE> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_SALE> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'DRUG_SALE_CANCEL'.
                  ASSIGN COMPONENT 'PHARMACY_SALE_CANCEL_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_SALE_CAN>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_SALE_CAN> TO FIELD-SYMBOL(<lv_notif_id_SALE_CAN>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_SALE_CAN> TO FIELD-SYMBOL(<fs_resp_prod_list_SALE_CAN>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_SALE_CAN> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_SALE_CAN>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_SALE_CAN> TO FIELD-SYMBOL(<r_gtin_SALE_CAN>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_SALE_CAN> TO FIELD-SYMBOL(<r_bn_SALE_CAN>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_SALE_CAN> TO FIELD-SYMBOL(<r_rc_SALE_CAN>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_SALE_CAN>).
                             IF <fs_item_SALE_CAN>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_SALE_CAN>-%data-gtin. lv_resp_gtin = <r_gtin_SALE_CAN>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_SALE_CAN>-%data-batch = <r_bn_SALE_CAN>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_SALE_CAN>-%data-tran_id AND item_no = @<fs_item_SALE_CAN>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_SALE_CAN>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_SALE_CAN>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_SALE_CAN>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_SALE_CAN>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_SALE_CAN>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_SALE_CAN>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_SALE_CAN>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_SALE_CAN>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_SALE_CAN>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_SALE_CAN>-%data-expdate.
                               IF <lv_notif_id_SALE_CAN> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_SALE_CAN>. ENDIF.
                               IF <r_rc_SALE_CAN> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_SALE_CAN>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_SALE_CAN>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_SALE_CAN>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_SALE_CAN> IS ASSIGNED AND <r_rc_SALE_CAN> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_SALE_CAN> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_SALE_CAN> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'DEACTIVATE'.
                  ASSIGN COMPONENT 'DEACTIVATION_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_DEAC>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_DEAC> TO FIELD-SYMBOL(<lv_notif_id_DEAC>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_DEAC> TO FIELD-SYMBOL(<fs_resp_prod_list_DEAC>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_DEAC> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_DEAC>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_DEAC> TO FIELD-SYMBOL(<r_gtin_DEAC>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_DEAC> TO FIELD-SYMBOL(<r_bn_DEAC>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_DEAC> TO FIELD-SYMBOL(<r_rc_DEAC>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_DEAC>).
                             IF <fs_item_DEAC>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_DEAC>-%data-gtin. lv_resp_gtin = <r_gtin_DEAC>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_DEAC>-%data-batch = <r_bn_DEAC>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_DEAC>-%data-tran_id AND item_no = @<fs_item_DEAC>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_DEAC>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_DEAC>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_DEAC>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_DEAC>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_DEAC>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_DEAC>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_DEAC>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_DEAC>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_DEAC>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_DEAC>-%data-expdate.
                               IF <lv_notif_id_DEAC> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_DEAC>. ENDIF.
                               IF <r_rc_DEAC> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_DEAC>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_DEAC>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_DEAC>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_DEAC> IS ASSIGNED AND <r_rc_DEAC> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_DEAC> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_DEAC> ) IMPORTING p_description = lv_desc ). ENDIF.
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

                WHEN 'DEACTIVATE_CANCEL'.
                  ASSIGN COMPONENT 'DEACTIVATION_CANCEL_RESPONSE' OF STRUCTURE <fs_response> TO FIELD-SYMBOL(<fs_resp_DEAC_CAN>).
                  IF sy-subrc = 0.
                    ASSIGN COMPONENT 'NOTIFICATIONID' OF STRUCTURE <fs_resp_DEAC_CAN> TO FIELD-SYMBOL(<lv_notif_id_DEAC_CAN>).
                    ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_resp_DEAC_CAN> TO FIELD-SYMBOL(<fs_resp_prod_list_DEAC_CAN>).
                    IF sy-subrc = 0.
                      ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_resp_prod_list_DEAC_CAN> TO <lt_resp_products>.
                      IF sy-subrc = 0.
                        LOOP AT <lt_resp_products> ASSIGNING FIELD-SYMBOL(<ls_resp_prod_DEAC_CAN>).
                           ASSIGN COMPONENT 'GTIN' OF STRUCTURE <ls_resp_prod_DEAC_CAN> TO FIELD-SYMBOL(<r_gtin_DEAC_CAN>).
                           ASSIGN COMPONENT 'BN' OF STRUCTURE <ls_resp_prod_DEAC_CAN> TO FIELD-SYMBOL(<r_bn_DEAC_CAN>).
                           ASSIGN COMPONENT 'RC' OF STRUCTURE <ls_resp_prod_DEAC_CAN> TO FIELD-SYMBOL(<r_rc_DEAC_CAN>).

                           LOOP AT lt_items ASSIGNING FIELD-SYMBOL(<fs_item_DEAC_CAN>).
                             IF <fs_item_DEAC_CAN>-%data-prodstat = 'SUCCESS'. CONTINUE. ENDIF.

                             lv_item_gtin = <fs_item_DEAC_CAN>-%data-gtin. lv_resp_gtin = <r_gtin_DEAC_CAN>.
                             SHIFT lv_item_gtin LEFT DELETING LEADING '0'.
                             SHIFT lv_resp_gtin LEFT DELETING LEADING '0'.

                             IF lv_item_gtin = lv_resp_gtin AND <fs_item_DEAC_CAN>-%data-batch = <r_bn_DEAC_CAN>.
                               SELECT SINGLE * FROM zmm_sst_dtts_itm INTO CORRESPONDING FIELDS OF @ls_processed_dttsit2
                                 WHERE tran_id = @<fs_item_DEAC_CAN>-%data-tran_id AND item_no = @<fs_item_DEAC_CAN>-%data-item_no.

                               ls_processed_dttsit2-mandt = sy-mandt.
                               ls_processed_dttsit2-tran_id = <fs_item_DEAC_CAN>-%data-tran_id.
                               ls_processed_dttsit2-item_no = <fs_item_DEAC_CAN>-%data-item_no.
                               ls_processed_dttsit2-zeile = <fs_item_DEAC_CAN>-%data-zeile.
                               ls_processed_dttsit2-product = <fs_item_DEAC_CAN>-%data-product.
                               ls_processed_dttsit2-prod_name = <fs_item_DEAC_CAN>-prod_name.
                               ls_processed_dttsit2-prodqty = <fs_item_DEAC_CAN>-%data-prodqty.
                               ls_processed_dttsit2-prod_unit = <fs_item_DEAC_CAN>-prod_unit.
                               ls_processed_dttsit2-gtin = <fs_item_DEAC_CAN>-%data-gtin.
                               ls_processed_dttsit2-batch = <fs_item_DEAC_CAN>-%data-batch.
                               ls_processed_dttsit2-expdate = <fs_item_DEAC_CAN>-%data-expdate.
                               IF <lv_notif_id_DEAC_CAN> IS ASSIGNED. ls_processed_dttsit2-notif_id = <lv_notif_id_DEAC_CAN>. ENDIF.
                               IF <r_rc_DEAC_CAN> IS ASSIGNED. ls_processed_dttsit2-tr_response = <r_rc_DEAC_CAN>. ENDIF.
                               ls_processed_dttsit2-mat_doc = <fs_item_DEAC_CAN>-%data-matdoc.
                               ls_processed_dttsit2-mvt_type = <fs_item_DEAC_CAN>-%data-mvttype.
                               IF lt_header IS NOT INITIAL.
                                 ls_processed_dttsit2-operation = lt_header[ 1 ]-operation.
                                 ls_processed_dttsit2-frm_gln = lt_header[ 1 ]-frm_gln.
                                 ls_processed_dttsit2-to_gln = lt_header[ 1 ]-to_gln.
                               ENDIF.
                               IF <r_rc_DEAC_CAN> IS ASSIGNED AND <r_rc_DEAC_CAN> = '00000'. ls_processed_dttsit2-prod_stat = 'SUCCESS'.
                               ELSE. ls_processed_dttsit2-prod_stat = 'ERROR'. lv_all_success = abap_false. ENDIF.

                               IF <r_rc_DEAC_CAN> IS ASSIGNED. me->get_error_description( EXPORTING p_error_code = CONV #( <r_rc_DEAC_CAN> ) IMPORTING p_description = lv_desc ). ENDIF.
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
                WHEN OTHERS.
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
    DATA: lt_create TYPE TABLE FOR CREATE zr_mm_dtts_cockpit.

    LOOP AT keys INTO DATA(ls_key).
      DATA(ls_param) = ls_key-%param.

      DATA lv_doc_year TYPE mjahr.
      DATA lv_matdoc TYPE mblnr.
      DATA lv_mvttype TYPE bwart.
      DATA lv_item_no TYPE numc4.

      lv_doc_year = sy-datum(4).
      GET TIME STAMP FIELD DATA(lv_ts).
      lv_mat_doc = CONV mblnr( lv_ts ).
      lv_mvt_type = '101'.

      CALL FUNCTION 'QF05_RANDOM_INTEGER'
        EXPORTING ran_int_max = 9999 ran_int_min = 1
        IMPORTING ran_int = DATA(lv_ran).
      lv_item_no = CONV numc4( lv_ran ).

      APPEND VALUE #( %cid = ls_key-%cid
                      doc_year = lv_doc_year
                      matdoc = lv_mat_doc
                      mvttype = lv_mvt_type
                      item_no = lv_item_no
                      tran_id = CONV ztran_id( lv_ts )
                      gtin = ls_param-gtin
                      prodqty = ls_param-prodqty
                      batch = ls_param-batch
                      expdate = ls_param-expdate
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
