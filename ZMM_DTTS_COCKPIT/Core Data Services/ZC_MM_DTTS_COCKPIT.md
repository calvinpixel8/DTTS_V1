```abap
@EndUserText.label: 'DTTS Cockpit Projection View'
@AccessControl.authorizationCheck: #NOT_REQUIRED
@Metadata.allowExtensions: true
@Search.searchable: true
define root view entity ZC_MM_DTTS_COCKPIT
  provider contract transactional_query
  as projection on ZR_MM_DTTS_COCKPIT
{
  key doc_year,
  @Search.defaultSearchElement: true
  key matdoc,
  key mvttype,
  key item_no,
  @Search.defaultSearchElement: true
  tran_id,
  zeile,
  product,
  prodname,
  prodqty,
  produnit,
  @Search.defaultSearchElement: true
  gtin,
  batch,
  expdate,
  notifid,
  trresponse,
  srnumber,
  createddate,
  createdtime,
  createdby,
  changeddate,
  changedtime,
  changedby,
  prodstat,
  transstat,
  operation,
  item_operation,
  fiscal_year,
  frm_gln,
  to_gln,
  auth_gln
}
```
