```abap
@Metadata.layer: #CORE
annotate view ZC_MM_DTTS_COCKPIT with
{
  @UI.facet: [ { id:              'Item',
                 purpose:         #STANDARD,
                 type:            #IDENTIFICATION_REFERENCE,
                 label:           'Item Details',
                 position:        10 } ]
  @UI.lineItem: [ { position: 10, label: 'Transaction ID' } ]
  @UI.identification: [ { position: 10, label: 'Transaction ID' } ]
  tran_id;
  @UI.lineItem: [ { position: 20, label: 'Item No' } ]
  @UI.identification: [ { position: 20, label: 'Item No' } ]
  item_no;
  @UI.lineItem: [ { position: 30, label: 'From GLN' } ]
  @UI.identification: [ { position: 30, label: 'From GLN' } ]
  frm_gln;
  @UI.lineItem: [ { position: 40, label: 'To GLN' } ]
  @UI.identification: [ { position: 40, label: 'To GLN' } ]
  to_gln;
  @UI.lineItem: [ { position: 50, label: 'GTIN' } ]
  @UI.identification: [ { position: 50, label: 'GTIN' } ]
  gtin;
  @UI.lineItem: [ { position: 60, label: 'Quantity' } ]
  @UI.identification: [ { position: 60, label: 'Quantity' } ]
  prod_qty;
  @UI.lineItem: [ { position: 70, label: 'Batch' } ]
  @UI.identification: [ { position: 70, label: 'Batch' } ]
  batch;
  @UI.lineItem: [ { position: 80, label: 'Expiry Date' } ]
  @UI.identification: [ { position: 80, label: 'Expiry Date' } ]
  exp_date;
  @UI.lineItem: [ { position: 90, label: 'Status' } ]
  @UI.identification: [ { position: 90, label: 'Status' } ]
  prod_stat;
  @UI.lineItem: [ { position: 100, label: 'Transaction Status' } ]
  @UI.identification: [ { position: 100, label: 'Transaction Status' } ]
  trans_stat;
  @UI.lineItem: [ { position: 110, label: 'Notification ID' } ]
  @UI.identification: [ { position: 110, label: 'Notification ID' } ]
  notif_id;
  @UI.lineItem:       [{ type: #FOR_ACTION, dataAction: 'reprocess', label: 'Reprocess' }]
  @UI.identification: [{ type: #FOR_ACTION, dataAction: 'reprocess', label: 'Reprocess' }]
  mat_doc; " Placeholder for action buttons
}
```
