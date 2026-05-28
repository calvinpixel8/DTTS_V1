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
             tranid TYPE ztran_id,
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
        tran_id   = ls_entity-tranid
        item_no   = ls_entity-itemno
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
        mat_doc   = ls_entity-matdoc
        mvt_type  = ls_entity-mvttype
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
      " Read base data
      SELECT SINGLE * FROM zmm_sst_dttsit2 INTO @DATA(ls_dttsit2)
        WHERE tran_id = @ls_entity-tranid AND item_no = @ls_entity-itemno.
      IF sy-subrc = 0.
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

        APPEND ls_dttsit2 TO lcl_buffer=>mt_update.
        APPEND VALUE #( tranid = ls_entity-tranid itemno = ls_entity-itemno ) TO lt_keys_to_reprocess.
      ENDIF.
    ENDLOOP.

    " Execute API Reprocessing for modified keys safely without EML MODIFY loop
    IF lt_keys_to_reprocess IS NOT INITIAL.
       DATA lt_processed_updates TYPE tt_dttsit2.
       me->execute_reprocess( EXPORTING it_keys = lt_keys_to_reprocess
                              IMPORTING et_update_buffer = lt_processed_updates ).

       " Merge the reprocessed results into the global update buffer
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
    ENDIF.
  ENDMETHOD.

  METHOD delete.
  ENDMETHOD.

  METHOD read.
    " Unmanaged read implementation to satisfy OData V4 retrieval of active entities.
    DATA: lt_read_data TYPE TABLE OF zr_mm_dtts_cockpit.

    IF keys IS NOT INITIAL.
      SELECT * FROM zr_mm_dtts_cockpit
        FOR ALL ENTRIES IN @keys
        WHERE tranid = @keys-tranid
          AND itemno = @keys-itemno
        INTO CORRESPONDING FIELDS OF TABLE @lt_read_data.

      IF sy-subrc = 0.
        " Map DB results to the expected RESULT structure
        LOOP AT lt_read_data INTO DATA(ls_read_data).
          INSERT VALUE #( %tky = VALUE #( tranid = ls_read_data-tranid itemno = ls_read_data-itemno )
                          %data = CORRESPONDING #( ls_read_data ) ) INTO TABLE result.
        ENDLOOP.
      ENDIF.
    ENDIF.
  ENDMETHOD.

  METHOD lock.
    " Implementation for pessimistic locking on active instances
    " For unmanaged draft, typically handled implicitly if purely shadow-driven, or explicitly via ENQUEUE.
  ENDMETHOD.

  METHOD reprocess.
     " Triggered manually via UI Button
     DATA lt_keys_to_reprocess TYPE tt_keys.
     LOOP AT keys INTO DATA(ls_key).
       APPEND VALUE #( tranid = ls_key-tranid itemno = ls_key-itemno ) TO lt_keys_to_reprocess.
     ENDLOOP.

     DATA lt_processed_updates TYPE tt_dttsit2.

     me->execute_reprocess( EXPORTING it_keys = lt_keys_to_reprocess
                            IMPORTING et_update_buffer = lt_processed_updates ).

     " Apply API updates safely into global buffer for the saver
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

     " Return result mapping
     READ ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
       ENTITY Item
       ALL FIELDS WITH CORRESPONDING #( keys )
       RESULT DATA(lt_updated_items).

     result = VALUE #( FOR ls_updated IN lt_updated_items
                       ( %tky = ls_updated-%tky
                         %param = ls_updated ) ).
  ENDMETHOD.

  METHOD execute_reprocess.
    " 1. Group by TRANID
    DATA: lt_tran_ids TYPE TABLE OF ty_key.

    LOOP AT it_keys INTO DATA(ls_key).
      APPEND VALUE #( tranid = ls_key-tranid ) TO lt_tran_ids.
    ENDLOOP.
    SORT lt_tran_ids BY tranid.
    DELETE ADJACENT DUPLICATES FROM lt_tran_ids COMPARING tranid.

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

    " Process Each TRAN_ID Group
    LOOP AT lt_tran_ids INTO DATA(ls_tran_id).
      CLEAR: lt_header, lt_items.

      SELECT * FROM zmm_sst_dtts_hdr INTO TABLE @lt_header
        WHERE tran_id = @ls_tran_id-tranid.

      " Read from the local transactional buffer to get newly edited data (not stale DB data)
      READ ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
        ENTITY Item
        ALL FIELDS WITH VALUE #( FOR key IN it_keys WHERE ( tranid = ls_tran_id-tranid )
                                 ( tranid = key-tranid itemno = key-itemno ) )
        RESULT lt_items.

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
          " Build request based on operation using Local Buffer Data
          " -------------------------------------------------------------
          CASE lv_operation.
            WHEN 'ACCEPT'.
              ASSIGN COMPONENT 'ACCEPT_BATCH_SERVICE_REQUEST' OF STRUCTURE <fs_request> TO FIELD-SYMBOL(<fs_accept_req>).
              IF sy-subrc = 0.
                ASSIGN COMPONENT 'FROMGLN' OF STRUCTURE <fs_accept_req> TO FIELD-SYMBOL(<lv_fromgln>).
                ASSIGN COMPONENT 'AUTHGLN' OF STRUCTURE <fs_accept_req> TO FIELD-SYMBOL(<lv_authgln>).
                IF sy-subrc = 0.
                   " Read from updated buffer if available, fallback to header DB
                   IF lt_items[ 1 ]-frm_gln IS NOT INITIAL.
                     <lv_fromgln> = lt_items[ 1 ]-frm_gln.
                   ELSE.
                     <lv_fromgln> = lt_header[ 1 ]-frm_gln.
                   ENDIF.

                   IF lt_items[ 1 ]-to_gln IS NOT INITIAL.
                     <lv_authgln> = lt_items[ 1 ]-to_gln.
                   ELSE.
                     <lv_authgln> = lt_header[ 1 ]-to_gln.
                   ENDIF.
                ENDIF.

                ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_accept_req> TO FIELD-SYMBOL(<fs_prod_list>).
                IF sy-subrc = 0.
                   ASSIGN COMPONENT 'PRODUCT' OF STRUCTURE <fs_prod_list> TO <lt_products>.
                   IF sy-subrc = 0.

                      " Use RTTS to dynamically create the line type for the generic table field symbol
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

                            " Create dynamic reference based on table line type
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
                          " Catch dynamic casting errors gracefully
                      ENDTRY.
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
              " Parse response, prepare updates directly for global buffer
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

                               DATA ls_processed_dttsit2 TYPE zmm_sst_dttsit2.
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
               " Application fault mapping
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
               " System fault mapping
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
               " Generic fault mapping
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
     " Unmanaged Save: persist global buffer to physical database tables

     " Insert new records
     IF lcl_buffer=>mt_create IS NOT INITIAL.
       INSERT zmm_sst_dttsit2 FROM TABLE lcl_buffer=>mt_create.
     ENDIF.

     " Update modified/reprocessed records
     IF lcl_buffer=>mt_update IS NOT INITIAL.
       MODIFY zmm_sst_dttsit2 FROM TABLE lcl_buffer=>mt_update.
     ENDIF.
  ENDMETHOD.

  METHOD cleanup.
     " Clear global memory buffers
     CLEAR lcl_buffer=>mt_create.
     CLEAR lcl_buffer=>mt_update.
  ENDMETHOD.

  METHOD cleanup_finalize.
  ENDMETHOD.

ENDCLASS.
```
