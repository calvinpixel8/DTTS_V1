@EndUserText.label: 'DTTS Cockpit Projection View'
@AccessControl.authorizationCheck: #NOT_REQUIRED
@Metadata.allowExtensions: true
@Search.searchable: true
define root view entity ZC_MM_DTTS_COCKPIT
  provider contract transactional_query
  as projection on ZR_MM_DTTS_COCKPIT
{
  key mandt,
  key tran_id,
  key item_no,
      zeile,
      product,
      prod_name,
      prod_qty,
      prod_unit,
      gtin,
      batch,
      exp_date,
      notif_id,
      tr_response,
      mat_doc,
      mvt_type,
      sr_number,
      created_date,
      created_time,
      created_by,
      changed_date,
      changed_time,
      changed_by,
      prod_stat,
      trans_stat,
      header_operation,
      frm_gln,
      to_gln
}
