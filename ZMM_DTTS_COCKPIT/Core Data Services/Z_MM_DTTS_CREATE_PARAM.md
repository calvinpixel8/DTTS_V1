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
  @EndUserText.label: 'Quantity'
  prod_qty     : menge_d;
  @EndUserText.label: 'Batch'
  batch        : zmm_sst_batch;
  @EndUserText.label: 'Shelf Expiry'
  exp_date     : zmm_sst_expiry_date;
}
