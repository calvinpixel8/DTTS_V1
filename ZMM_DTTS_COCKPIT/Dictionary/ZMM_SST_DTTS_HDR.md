```abap
@EndUserText.label : 'DTTS integration - serial to batch - Header Table'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #A
@AbapCatalog.dataMaintenance : #ALLOWED
define table zmm_sst_dtts_hdr {

  key mandt    : mandt not null;
  key tran_id  : ztran_id not null;
  mat_doc      : mblnr;
  doc_yr       : mjahr;
  gjhr         : gjahr;
  mvt_type     : bwart;
  budat        : budat;
  @EndUserText.label : 'Operation'
  operation    : abap.char(20);
  frm_gln      : zmm_sst_gln_src;
  to_gln       : zmm_sst_gln_des;
  auth_gln     : zmm_sst_gln_auth;
  created_date : dats;
  created_time : tims;
  created_by   : xubname;
  changed_date : dats;
  changed_time : tims;
  changed_by   : xubname;
  @EndUserText.label : 'Status'
  status       : abap.char(10);

}
```
