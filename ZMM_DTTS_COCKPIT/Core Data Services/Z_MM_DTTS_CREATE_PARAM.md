```abap
@EndUserText.label: 'DTTS Create Parameters'
define abstract entity Z_MM_DTTS_CREATE_PARAM
{
  @EndUserText.label: 'From GLN'
  frm_gln      : abap.char(13);
  @EndUserText.label: 'To GLN'
  to_gln       : abap.char(13);
  @EndUserText.label: 'Operation'
  operation    : abap.char(20);
  @EndUserText.label: 'GTIN'
  gtin         : z_dgtin;
// 1. Add the semantics annotation pointing to your unit field
  @Semantics.quantity.unitOfMeasure: 'prod_unit'
  @EndUserText.label: 'Quantity'
  prod_qty   : menge_d;
  
// 2. Add the unit field itself (typically MSEH or standard char 3)
  @EndUserText.label: 'Unit of Measure'
  prod_unit  : abap.unit(3);
  @EndUserText.label: 'Batch'
  batch        : zmm_sst_batch;
  @EndUserText.label: 'Shelf Expiry'
  exp_date     : zmm_sst_expiry_date;
}

```
