```abap
@AbapCatalog.sqlViewName: 'ZVIMMDTTSOP'
@AbapCatalog.compiler.compareFilter: true
@AbapCatalog.preserveKey: true
@ClientHandling.algorithm: #SESSION_VARIABLE
@EndUserText.label: 'DTTS Items with Header Operation'

define view ZIMMDTTS_4
  as select from ZIMM_DTTS_FY_HELPER as itm
    left outer join zmm_sst_dtts_hdr as hdr
      on  itm.mandt   = hdr.mandt
      and itm.tran_id = hdr.tran_id
{
  key itm.mandt,
  key itm.tran_id,
  key itm.item_no,

      itm.zeile,
      itm.product,
      itm.prod_name,
      itm.prod_qty,
      itm.prod_unit,
      itm.gtin,
      itm.batch,
      itm.exp_date,
      itm.notif_id,
      itm.tr_response,
      itm.mat_doc,
      itm.mvt_type,
      itm.sr_number,
      itm.created_date,
      itm.created_time,
      itm.created_by,
      itm.changed_date,
      itm.changed_time,
      itm.changed_by,
      itm.prod_stat,
      itm.trans_stat,
      itm.fiscal_year,
      itm.DOC_YEAR,
      itm.operation as item_operation,
      hdr.operation as header_operation,
      hdr.frm_gln as frm_gln,
      hdr.to_gln as to_gln,
      hdr.auth_gln as auth_gln
}
```
