```abap
unmanaged implementation in class zcl_mm_dtts_cockpit_bdef unique;
strict ( 2 );
with draft;

define behavior for ZR_MM_DTTS_COCKPIT alias Item
draft table zmm_sst_dttsit2d
lock master total etag changed_time
etag master changed_time
authorization master ( instance )
{
  create;
  update ( features : instance ); // Only non-success can be updated
  delete;

  field ( readonly ) mandt, tran_id, item_no, prod_stat, trans_stat, notif_id;

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
    tran_id = tran_id;
    item_no = item_no;
    zeile = zeile;
    product = product;
    prod_name = prod_name;
    prod_qty = prod_qty;
    prod_unit = prod_unit;
    gtin = gtin;
    batch = batch;
    exp_date = exp_date;
    notif_id = notif_id;
    tr_response = tr_response;
    mat_doc = mat_doc;
    mvt_type = mvt_type;
    sr_number = sr_number;
    created_date = created_date;
    created_time = created_time;
    created_by = created_by;
    changed_date = changed_date;
    changed_time = changed_time;
    changed_by = changed_by;
    prod_stat = prod_stat;
    trans_stat = trans_stat;
  }
}
```
