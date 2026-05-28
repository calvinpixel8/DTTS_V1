```abap
@EndUserText.label : 'DTTS integration - serial to batch - Item Table'
@AbapCatalog.enhancement.category : #EXTENSIBLE_ANY
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #A
@AbapCatalog.dataMaintenance : #ALLOWED
define table zmm_sst_dtts_itm {

  key mandt    : mandt not null;
  key doc_year : mjahr not null;
  key mat_doc  : mblnr not null;
  key mvt_type : bwart not null;
  @EndUserText.label : 'Item Number'
  key item_no  : abap.numc(4) not null;
  tran_id      : ztran_id;
  zeile        : mblpo;
  product      : matnr;
  prod_name    : maktx;
  @Semantics.quantity.unitOfMeasure : 'zmm_sst_dtts_itm.prod_unit'
  prod_qty     : menge_d;
  prod_unit    : meins;
  gtin         : z_dgtin;
  batch        : zmm_sst_batch;
  exp_date     : zmm_sst_expiry_date;
  notif_id     : zmm_sst_notif_id;
  tr_response  : zmm_sst_response;
  sr_number    : zmm_br_serial_no;
  created_date : dats;
  created_time : tims;
  created_by   : xubname;
  changed_date : dats;
  changed_time : tims;
  changed_by   : xubname;
  prod_stat    : zmm_sst_prod_stat;
  @EndUserText.label : 'Transaction Status'
  trans_stat   : abap.char(1333);

}
```
