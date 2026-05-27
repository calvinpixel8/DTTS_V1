```abap
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'DTTS Cockpit Root View'
define root view entity ZR_MM_DTTS_COCKPIT
  as select from zmm_sst_dtts_itm as Item
  association [1..1] to zmm_sst_dtts_hdr as _Header
   -- on  $projection.mandt   = _Header.mandt
    on $projection.tran_id = _Header.tran_id
{
 -- key Item.mandt,
  key Item.tran_id ,
  key Item.item_no ,
      Item.zeile,
      Item.product,
      Item.prod_name as prodname,
      @Semantics.quantity.unitOfMeasure: 'produnit'
      Item.prod_qty as prodqty,
      Item.prod_unit as produnit,
      Item.gtin,
      Item.batch,
      Item.exp_date as expdate,
      Item.notif_id as notifid,
      Item.tr_response as trresponse,
      Item.mat_doc as matdoc,
      Item.mvt_type as mvttype,
      Item.sr_number as srnumber,
      Item.created_date as createddate,
      Item.created_time as createdtime,
      Item.created_by as createdby,
      Item.changed_date as changeddate,
      Item.changed_time as changedtime,
      Item.changed_by as changedby,
      Item.prod_stat as prodstat,
      Item.trans_stat as transstat,
      /* Associations */
      _Header,
      _Header.operation as operation,
      _Header.frm_gln   as frm_gln,
      _Header.to_gln    as to_gln
}

```
