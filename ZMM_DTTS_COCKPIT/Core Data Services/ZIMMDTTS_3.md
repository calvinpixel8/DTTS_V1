```abap
@AbapCatalog.sqlViewName: 'ZVIMMDTTSO'
@AbapCatalog.compiler.compareFilter: true
@AbapCatalog.preserveKey: true
@ClientHandling.algorithm: #SESSION_VARIABLE
@EndUserText.label: 'DTTS Items - Union of Edited and Original'
define view ZIMMDTTS_3
  as select from zmm_sst_dttsit2 as curr
{
  key curr.mandt,
  key curr.doc_year as DOC_YEAR,
  key curr.mat_doc,
  key curr.mvt_type,
  key curr.item_no,
      curr.tran_id,
      curr.zeile,
      curr.product,
      curr.prod_name,
      curr.prod_qty,
      curr.prod_unit,
      curr.gtin,
      curr.batch,
      curr.exp_date,
      curr.notif_id,
      curr.tr_response,
      curr.sr_number,
      curr.created_date,
      curr.created_time,
      curr.created_by,
      curr.changed_date,
      curr.changed_time,
      curr.changed_by,
      curr.prod_stat,
      curr.trans_stat,
      curr.operation
}
union all select from zmm_sst_dtts_itm as orig
{
  key orig.mandt,
  key orig.doc_year as DOC_YEAR,
  key orig.mat_doc,
  key orig.mvt_type,
  key orig.item_no,
      orig.tran_id,
      orig.zeile,
      orig.product,
      orig.prod_name,
      orig.prod_qty,
      orig.prod_unit,
      orig.gtin,
      orig.batch,
      orig.exp_date,
      orig.notif_id,
      orig.tr_response,
      orig.sr_number,
      orig.created_date,
      orig.created_time,
      orig.created_by,
      orig.changed_date,
      orig.changed_time,
      orig.changed_by,
      orig.prod_stat,
      orig.trans_stat,
      cast('' as abap.char(20)) as operation
}
```
