```abap

@EndUserText.label: 'DTTS Cockpit Projection View'
@AccessControl.authorizationCheck: #NOT_REQUIRED
@Metadata.allowExtensions: true
@Search.searchable: true
define root view entity ZC_MM_DTTS_COCKPIT
  provider contract transactional_query
  as projection on ZR_MM_DTTS_COCKPIT
{
  --key mandt,
  key tran_id,
  key item_no,
      zeile,
      product,
  @Search.defaultSearchElement: true
  @Search.fuzzinessThreshold: 0.8
      prodname,
      prodqty,
      produnit,
      gtin,
      batch,
      expdate,
      notifid,
      trresponse,
      matdoc,
      mvttype,
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
      frm_gln,
      to_gln
}

```
