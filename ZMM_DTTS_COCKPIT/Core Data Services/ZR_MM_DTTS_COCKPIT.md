```abap
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'DTTS Cockpit Root View'
define root view entity ZR_MM_DTTS_COCKPIT
  as select from zmm_sst_dtts_itm as Item
  association [1..1] to zmm_sst_dtts_hdr as _Header
    on  $projection.mandt   = _Header.mandt
    and $projection.tran_id = _Header.tran_id
{
  key Item.mandt,
  key Item.tran_id,
  key Item.item_no,
      Item.zeile,
      Item.product,
      Item.prod_name,
      @Semantics.quantity.unitOfMeasure: 'prod_unit'
      Item.prod_qty,
      Item.prod_unit,
      Item.gtin,
      Item.batch,
      Item.exp_date,
      Item.notif_id,
      Item.tr_response,
      Item.mat_doc,
      Item.mvt_type,
      Item.sr_number,
      Item.created_date,
      Item.created_time,
      Item.created_by,
      Item.changed_date,
      Item.changed_time,
      Item.changed_by,
      Item.prod_stat,
      Item.trans_stat,
      /* Associations */
      _Header,
      _Header.operation as header_operation,
      _Header.frm_gln   as frm_gln,
      _Header.to_gln    as to_gln
}
```
