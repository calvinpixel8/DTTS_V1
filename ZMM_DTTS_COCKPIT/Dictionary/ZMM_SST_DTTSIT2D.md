```abap
@EndUserText.label : 'DTTS Items - Draft Shadow Table'
@AbapCatalog.enhancement.category : #EXTENSIBLE_ANY
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #A
@AbapCatalog.dataMaintenance : #RESTRICTED
define table zmm_sst_dttsit2d {

  key mandt   : mandt not null;
  key doc_year : mjahr not null;
  key mat_doc  : mblnr not null;
  key mvt_type : bwart not null;
  key item_no  : abap.numc(4) not null;
  tran_id      : ztran_id;
  zeile       : mblpo;
  product     : matnr;
  prodname    : maktx;
  @Semantics.quantity.unitOfMeasure : 'zmm_sst_dttsit2d.produnit'
  prodqty     : menge_d;
  produnit    : meins;
  gtin        : z_dgtin;
  batch       : zmm_sst_batch;
  expdate     : zmm_sst_expiry_date;
  notifid     : zmm_sst_notif_id;
  trresponse  : zmm_sst_response;
  srnumber    : zmm_br_serial_no;
  createddate : dats;
  createdtime : tims;
  createdby   : xubname;
  changeddate : dats;
  changedtime : tims;
  changedby   : xubname;
  prodstat    : zmm_sst_prod_stat;
  transstat   : abap.char(1333);
  operation   : abap.char(20);
  item_operation : abap.char(20);
  fiscal_year : gjahr;
  frm_gln     : abap.char(13);
  to_gln      : abap.char(13);
  auth_gln    : abap.char(13);
  "%admin"    : include sych_bdl_draft_admin_inc;

}
```
