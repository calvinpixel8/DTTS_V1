```abap
@AbapCatalog.sqlViewName: 'ZVIMMDTTS_3'
@EndUserText.label: 'DTTS Items - Combined View (Latest State)'
define view ZIMMDTTS_3
  as

/* 1. Always take latest (Table2) */
select from zmm_sst_dttsit2 as t2

{
  key t2.mandt,
  key t2.tran_id,
  key t2.item_no,
      t2.zeile,
      t2.product,
      t2.prod_name,
      t2.prod_qty,
      t2.prod_unit,
      t2.gtin,
      t2.batch,
      t2.exp_date,
      t2.notif_id,
      t2.tr_response,
      t2.mat_doc,
      --fy.fiscal_year,
      t2.mvt_type,
      t2.sr_number,
      t2.created_date,
      t2.created_time,
      t2.created_by,
      t2.changed_date,
      t2.changed_time,
      t2.changed_by,
      t2.prod_stat,
      t2.trans_stat,
      t2.operation
}

union all

/* 2. Take from Table1 ONLY if no record in Table2 */
select from zmm_sst_dtts_itm as t1
  left outer join zmm_sst_dttsit2 as t2
    on  t1.mandt   = t2.mandt
    and t1.tran_id = t2.tran_id
    and t1.item_no = t2.item_no

{
  key t1.mandt,
  key t1.tran_id,
  key t1.item_no,
      t1.zeile,
      t1.product,
      t1.prod_name,
      t1.prod_qty,
      t1.prod_unit,
      t1.gtin,
      t1.batch,
      t1.exp_date,
      t1.notif_id,
      t1.tr_response,
      t1.mat_doc,
      --fy.fiscal_year,
      t1.mvt_type,
      t1.sr_number,
      t1.created_date,
      t1.created_time,
      t1.created_by,
      t1.changed_date,
      t1.changed_time,
      t1.changed_by,
      t1.prod_stat,
      t1.trans_stat,
      '' as operation

}
where t2.mandt is null
```
