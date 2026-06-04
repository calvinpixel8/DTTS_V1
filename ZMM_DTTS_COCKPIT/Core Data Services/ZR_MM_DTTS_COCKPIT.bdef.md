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

  field ( readonly ) mandt, doc_year, matdoc, mvttype, item_no, prodstat, transstat, notifid, tran_id;

  // Actions
  action ( features : instance ) reprocess result [1] $self;

  // Factory action to create new records with parameters
  factory action createWithPopup parameter Z_MM_DTTS_CREATE_PARAM [1];

  draft action Edit;
  draft action Activate optimized;
  draft action Discard;
  draft action Resume;
  draft determine action Prepare;

}
```
