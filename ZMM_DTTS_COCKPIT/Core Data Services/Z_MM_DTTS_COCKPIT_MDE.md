```abap
@Metadata.layer: #CORE
annotate view ZC_MM_DTTS_COCKPIT with
{
  @UI.createHidden: true
  @UI.facet: [ { id:              'Item',
                 purpose:         #STANDARD,
                 type:            #IDENTIFICATION_REFERENCE,
                 label:           'Item Details',
                 position:        10 } ]

  @UI.selectionField: [ { position: 30 } ]
  @UI.lineItem: [ { position: 10, label: 'Transaction ID' } ]
  tran_id;

  @UI.lineItem: [ { position: 20, label: 'Item No' } ]
  item_no;

  @UI.lineItem: [ { position: 30, label: 'From GLN' } ]
  @UI.identification: [ { position: 30, label: 'From GLN' } ]
  frm_gln;

  @UI.lineItem: [ { position: 40, label: 'To GLN' } ]
  @UI.identification: [ { position: 40, label: 'To GLN' } ]
  to_gln;

  @UI.selectionField: [ { position: 40 } ]
  @UI.lineItem: [ { position: 50, label: 'GTIN' } ]
  @UI.identification: [ { position: 50, label: 'GTIN' } ]
  gtin;

  @UI.lineItem: [ { position: 60, label: 'Quantity' } ]
  @UI.identification: [ { position: 60, label: 'Quantity' } ]
  prodqty;

  @UI.lineItem: [ { position: 70, label: 'Batch' } ]
  @UI.identification: [ { position: 70, label: 'Batch' } ]
  batch;

  @UI.selectionField: [ { position: 50 } ]
  @UI.lineItem: [ { position: 80, label: 'Expiry Date' } ]
  @UI.identification: [ { position: 80, label: 'Expiry Date' } ]
  expdate;

  @UI.selectionField: [ { position: 20 } ]
  @UI.lineItem: [ { position: 90, label: 'Status' } ]
  prodstat;

  @UI.lineItem: [ { position: 100, label: 'Transaction Status' } ]
  transstat;

  @UI.lineItem: [ { position: 110, label: 'Notification ID' } ]
  notifid;

  @UI.selectionField: [ { position: 10 } ]
  @UI.lineItem:       [{ type: #FOR_ACTION, dataAction: 'createWithPopup', label: 'Create', invocationGrouping: #ISOLATED },
                       { type: #FOR_ACTION, dataAction: 'reprocess', label: 'Reprocess' },
                       { position: 120, label: 'Material Document' }]
  matdoc;
  @UI.hidden: true
  doc_year;
  @UI.hidden: true
  fiscal_year;
}
```
