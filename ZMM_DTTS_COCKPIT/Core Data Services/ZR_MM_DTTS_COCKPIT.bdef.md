```abap
unmanaged implementation in class zcl_mm_dtts_cockpit_bdef unique;
strict ( 2 );
with draft;

define behavior for ZR_MM_DTTS_COCKPIT alias Item
draft table zmm_sst_dttsit2d
lock master total etag changedtime
etag master changedtime
authorization master ( instance )
{
  create;
  update ( features : instance ); // Only non-success can be updated
  delete;

  field ( readonly ) mandt, tranid, itemno, prodstat, transstat, notifid;

  // Actions
  action ( features : instance ) reprocess result [1] $self;

  // Factory action to create new records with parameters
  factory action createWithPopup parameter Z_MM_DTTS_CREATE_PARAM [1];

  draft action Edit;
  draft action Activate optimized;
  draft action Discard;
  draft action Resume;
  draft determine action Prepare;

  mapping for zmm_sst_dtts_itm
  {
    mandt = mandt;
    tranid = tran_id;
    itemno = item_no;
    zeile = zeile;
    product = product;
    prodname = prod_name;
    prodqty = prod_qty;
    produnit = prod_unit;
    gtin = gtin;
    batch = batch;
    expdate = exp_date;
    notifid = notif_id;
    trresponse = tr_response;
    matdoc = mat_doc;
    mvttype = mvt_type;
    srnumber = sr_number;
    createddate = created_date;
    createdtime = created_time;
    createdby = created_by;
    changeddate = changed_date;
    changedtime = changed_time;
    changedby = changed_by;
    prodstat = prod_stat;
    transstat = trans_stat;
  }
}
```
