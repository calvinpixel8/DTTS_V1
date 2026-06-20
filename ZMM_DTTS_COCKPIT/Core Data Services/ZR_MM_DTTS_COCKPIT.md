```abap
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'DTTS Cockpit Root View'
define root view entity ZR_MM_DTTS_COCKPIT
  as select from ZIMMDTTS_4 as Item
{
  key Item.mandt,
  key Item.DOC_YEAR as doc_year,
  key Item.mat_doc as matdoc,
  key Item.mvt_type as mvttype,
  key Item.item_no as item_no,
      Item.tran_id as tran_id,
      Item.zeile,
      Item.product,
      Item.prod_name as prodname,
      @Semantics.quantity.unitOfMeasure: 'produnit'
      Item.prod_qty as prodqty,
      Item.prod_unit as produnit,
      Item.gtin,
      Item.batch,

      // Fix for Date Parsing / Preview Scroll Error
      cast(
        case
          when length(Item.exp_date) = 8 and dats_is_valid(Item.exp_date) = 1
            then Item.exp_date
          else '00000000'
        end as abap.dats
      ) as expdate,

      Item.notif_id as notifid,
      Item.tr_response as trresponse,
      Item.sr_number as srnumber,
      Item.created_date as createddate,
      Item.created_time as createdtime,
      Item.created_by as createdby,
      Item.changed_date as changeddate,
      Item.changed_time as changedtime,
      Item.changed_by as changedby,
      Item.prod_stat as prodstat,
      Item.trans_stat as transstat,
      Item.header_operation as operation,
      Item.item_operation,
      Item.fiscal_year,
      Item.frm_gln,
      Item.to_gln,
      Item.auth_gln
}
```
