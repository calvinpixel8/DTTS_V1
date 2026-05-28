```abap
@AbapCatalog.sqlViewName: 'ZVIMMDTTFYH'
@AbapCatalog.compiler.compareFilter: true
@AbapCatalog.preserveKey: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Fiscal Year Helper for DTTS Items'
define view ZIMM_DTTS_FY_HELPER
  as select from ZIMMDTTS_3 as itm
{
  key itm.mandt,
  key itm.DOC_YEAR,
  key itm.mat_doc,
  key itm.mvt_type,
  key itm.item_no,
      itm.tran_id,
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
      itm.sr_number,
      itm.created_date,
      itm.created_time,
      itm.created_by,
      itm.changed_date,
      itm.changed_time,
      itm.changed_by,
      itm.prod_stat,
      itm.trans_stat,
      itm.operation,

      case
        when itm.mat_doc is not initial then itm.DOC_YEAR
        else '0000'
      end as fiscal_year
}
```
