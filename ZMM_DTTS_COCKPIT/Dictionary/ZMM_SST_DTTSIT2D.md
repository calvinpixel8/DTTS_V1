```abap
@EndUserText.label : 'DTTS Items - Draft Shadow Table'
@AbapCatalog.enhancement.category : #EXTENSIBLE_ANY
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #A
@AbapCatalog.dataMaintenance : #RESTRICTED
define table zmm_sst_dttsit2d {

  key mandt   : mandt not null;
  key tran_id : ztran_id not null;
  key item_no : abap.numc(4) not null;
  zeile       : mblpo;
  product     : matnr;
  prod_name   : maktx;
  @Semantics.quantity.unitOfMeasure : 'zmm_sst_dttsit2d.prod_unit'
  prod_qty    : menge_d;
  prod_unit   : meins;
  gtin        : z_dgtin;
  batch       : zmm_sst_batch;
  exp_date    : zmm_sst_expiry_date;
  notif_id    : zmm_sst_notif_id;
  tr_response : zmm_sst_response;
  mat_doc     : mblnr;
  mvt_type    : bwart;
  sr_number   : zmm_br_serial_no;
  created_date : dats;
  created_time : tims;
  created_by   : xubname;
  changed_date : dats;
  changed_time : tims;
  changed_by   : xubname;
  prod_stat    : zmm_sst_prod_stat;
  trans_stat   : abap.char(1333);
  header_operation : abap.char(20);
  frm_gln      : abap.char(13);
  to_gln       : abap.char(13);
  "%admin"     : include sych_bdl_draft_admin_inc;

}
```
