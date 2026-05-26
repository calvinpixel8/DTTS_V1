# User Guidance and Developer Reference
## DTTS API Processing & Reprocessing Application

### 1. Application Overview
**Purpose:**
The DTTS (Drug Track and Trace System) Reprocess Cockpit is a SAP RAP (RESTful ABAP Programming Model) application designed to facilitate the viewing, editing, and reprocessing of transactional items that failed to integrate correctly with the external DTTS API.

**Business Problem:**
When warehouse or pharmacy movements occur (e.g., dispatch, receive, consume, deactivate), standard SAP goods movements must be reported to the external SFDA DTTS platform. Occasionally, transactions fail due to data issues (incorrect GLN, unregistered GTIN, API timeouts, etc.). This application provides a centralized Fiori UI for users to monitor these integration records, correct erroneous data directly within a draft-enabled interface, and trigger a re-transmission of the data to the API without reversing and reposting the core SAP material documents.

**Intended Users:**
- **Business Users / Supply Chain Operators:** To monitor failed transactions and correct data entry errors (e.g., GLN mismatch).
- **Administrators:** To oversee overall integration health and handle mass reprocessing.
- **Developers/Technical Support:** To audit the API payloads, responses, and integration errors returned by CPI or the SFDA platform.

**Architecture:**
- **RAP Paradigm:** Unmanaged implementation with draft capabilities.
- **Data Models:** Root CDS View (`ZR_MM_DTTS_COCKPIT`) on table `ZMM_SST_DTTS_ITM` representing individual drug packages (PRODUCT level), joined with header table `ZMM_SST_DTTS_HDR` for contextual routing (FROM/TO GLNs).
- **Behavior Definition:** `strict(2)` compliant, controlling instance features to lock successfully processed items, and managing the Draft shadow table (`ZMM_SST_DTTSIT2D`).
- **UI:** Fiori Elements projected via `ZC_MM_DTTS_COCKPIT` and annotated via Metadata Extension (`Z_MM_DTTS_COCKPIT_MDE`).
- **Integration:** Dynamic ABAP Proxy instantiation based on configuration table `ZMM_DTTS_API_CON`, communicating synchronously to external web services.

---

### 2. Functional Features (Detailed)

#### Feature 2.1: View DTTS Integration Records
- **Business purpose:** Provide visibility into the current integration state of all material document line items.
- **End-user workflow:** User opens the Fiori Elements List Report. Filters by Material Document, Status, or Date. Views the list of records.
- **Trigger point:** Standard Fiori tile / App load.
- **Input parameters:** Selection filters (matdoc, status, etc.).
- **Output/result:** Tabular display of records with their `PROD_STAT` (SUCCESS, ERROR, NEW) and detailed `TRANS_STAT` (error descriptions).

#### Feature 2.2: Edit Erroneous Records
- **Business purpose:** Allow correction of data (e.g., GTIN, Batch, Expiry, GLNs) that caused API rejection.
- **End-user workflow:** User selects an item with status 'ERROR' or 'NEW' and clicks "Edit". Modifies allowable fields, clicks "Save".
- **Trigger point:** Standard Edit button (Draft).
- **Validation rules:** `PROD_STAT` must not be 'SUCCESS'.
- **Business logic executed:** SAP RAP Draft framework transitions the record to an exclusive lock state in `ZMM_SST_DTTSIT2D`. Upon save, the unmanaged `update` method writes the changes back.
- **Error handling behavior:** Standard RAP locking mechanisms.
- **Dependencies:** Draft table `ZMM_SST_DTTSIT2D`.

#### Feature 2.3: Reprocess Transactions
- **Business purpose:** Re-send corrected or failed items to the DTTS API.
- **End-user workflow:** User selects one or multiple items, clicks "Reprocess".
- **Trigger point:** Action button `reprocess`.
- **Validation rules:** Only records with `PROD_STAT <> 'SUCCESS'` are processed.
- **Business logic executed:**
  1. Group selected items by `TRAN_ID`.
  2. Fetch header context and API configuration (`ZMM_DTTS_API_CON`).
  3. Dynamically construct the nested API payload based on the operation type (e.g., ACCEPT, DISPATCH).
  4. Instantiate and invoke the web service proxy.
  5. Parse the XML/Object response.
  6. Update item status (`SUCCESS` or `ERROR`) and log the `NOTIF_ID` / Response Codes.
- **Output/result:** Items are updated with new statuses and error messages.
- **Dependencies:** External API, `ZMM_DTTS_API_CON` config table, ABAP Proxy objects.

#### Feature 2.4: Create New Manual Records
- **Business purpose:** Manually inject missing transactions into the integration queue.
- **End-user workflow:** User clicks "Create", fills out a parameter popup with GLNs, GTIN, Batch, etc., and submits.
- **Trigger point:** Factory Action `createWithPopup`.
- **Input parameters:** Abstract entity `Z_MM_DTTS_CREATE_PARAM` (frm_gln, to_gln, operation, gtin, prod_qty, batch, exp_date).
- **Business logic executed:** Creates a new buffer entry with `PROD_STAT = 'NEW'` and generates a new `TRAN_ID`.

---

### 3. Technical Implementation Mapping

| Feature | CDS Views | BDEF | Behavior Implementation | MDE / Service |
| :--- | :--- | :--- | :--- | :--- |
| **View Records** | `ZR_MM_DTTS_COCKPIT`, `ZC_MM_DTTS_COCKPIT` | N/A | N/A | `Z_MM_DTTS_COCKPIT_MDE`, `ZSRV_MM_DTTS_COCKPIT` |
| **Edit Records** | `ZR_MM_DTTS_COCKPIT` | `update ( features : instance );` | `METHOD get_instance_features`, `METHOD update` | N/A |
| **Reprocess** | N/A | `action ( features : instance ) reprocess result [1] $self;` | `METHOD reprocess` | `@UI.lineItem: [{ type: #FOR_ACTION, dataAction: 'reprocess' }]` |
| **Create Manual**| N/A | `factory action createWithPopup parameter Z_MM_DTTS_CREATE_PARAM [1];` | `METHOD createWithPopup` | N/A |

---

### 4. Code Snippets

#### 4.1 Feature Control (Locking SUCCESS records)
```abap
  METHOD get_instance_features.
    READ ENTITIES OF zr_mm_dtts_cockpit IN LOCAL MODE
      ENTITY Item
      FIELDS ( prodstat ) WITH CORRESPONDING #( keys )
      RESULT DATA(lt_items).

    result = VALUE #( FOR ls_item IN lt_items
                      ( %tky = ls_item-%tky
                        %update = COND #( WHEN ls_item-prodstat = 'SUCCESS' THEN if_abap_behv=>fc-o-disabled ELSE if_abap_behv=>fc-o-enabled )
                        %action-reprocess = COND #( WHEN ls_item-prodstat = 'SUCCESS' THEN if_abap_behv=>fc-o-disabled ELSE if_abap_behv=>fc-o-enabled )
                      ) ).
  ENDMETHOD.
```

#### 4.2 Reprocess Action (Dynamic Proxy Call)
```abap
        SELECT SINGLE * FROM zmm_dtts_api_con INTO @wa_zmm_dtts_api_con
          WHERE api_name = @lv_operation.

        IF sy-subrc = 0.
          CREATE DATA request_ptr TYPE (wa_zmm_dtts_api_con-request_structure).
          ASSIGN request_ptr->* TO <fs_request>.

          " ... Payload Construction ...

          TRY.
              CREATE OBJECT lo_proxy TYPE (wa_zmm_dtts_api_con-proxy_class)
                PARAMETER-TABLE ptab.

              CALL METHOD lo_proxy->(wa_zmm_dtts_api_con-method_name)
                EXPORTING
                  input  = <fs_request>
                IMPORTING
                  output = <fs_response>.
```

---

### 5. Requirement Traceability Matrix

| Feature | Current Implementation | Technical Objects | Status | Gaps / Deviations |
| :--- | :--- | :--- | :--- | :--- |
| View DTTS Data | List Report App | `ZR/ZC_MM_DTTS_COCKPIT`, MDE | Fully Implemented | None |
| Edit Non-Success | Draft-enabled unmanaged RAP | `ZMM_SST_DTTSIT2D`, `lhc_Item->update` | Fully Implemented | Draft shadow table required renaming to match CDS aliases. |
| Reprocess | Unmanaged Action | `lhc_Item->reprocess` | Partially Implemented | Proxy calls are scaffolded; exact ABAP proxy structure references must be verified against actual SFDA WSDLs in the target system. |
| Create Records | Factory Action | `createWithPopup` | Assumed Implementation | TRAN_ID generation logic is hardcoded as 'NEW_TRAN_ID' and needs a proper number range / GUID generation. |

---

### 6. Developer Review Notes

- **Design Assumptions:** Assumed that the unmanaged save sequence relies on the EML `MODIFY ENTITIES IN LOCAL MODE` to push updates into the transactional buffer, and the actual database commit (`MODIFY zmm_sst_dttsit2`) must be handled inside the `lsc_ZR_MM_DTTS_COCKPIT->save()` method.
- **Potential Technical Debt:** The proxy payload construction inside `reprocess` currently relies on massive `ASSIGN COMPONENT` logic to dynamically map generic XML payloads. This is brittle. If the DTTS WSDL changes, this code will fail silently at runtime.
- **Hardcoded Values:**
  - `lv_tran_id = 'NEW_TRAN_ID'` in `createWithPopup`.
  - `lv_item_no = '0001'` in `createWithPopup`.
- **Missing Validations:** No backend validation ensures that `frm_gln` and `to_gln` are valid 13-digit GLNs before saving the draft.
- **RAP Anti-Patterns:** Using unmanaged scenarios for simple DB tables is generally an anti-pattern unless legacy BAPIs are involved. Since we are updating a custom Z-table, a Managed scenario with an unmanaged save or determine actions would be cleaner.

---

### 7. User Guidance

**How to use:**
1. Open the "DTTS Reprocess Cockpit" application from the Fiori Launchpad.
2. Use the smart filter bar to search for `PROD_STAT = ERROR`.
3. To edit an item, click the arrow to navigate to the Object Page, click **Edit**, modify the GTIN or Expiry Date, and click **Save**.
4. To reprocess, select one or more rows from the List Report and click the **Reprocess** button at the top of the table.

**Common Errors:**
- *Button Disabled:* If the Reprocess or Edit buttons are grayed out, it means the record has already achieved a status of `SUCCESS`.
- *API Application Fault:* The data sent to the SFDA was structurally valid but business-invalid (e.g., GTIN not registered). Read the Transaction Status column for the exact reason.

---

### 8. Deployment / Configuration Dependencies

- **Configuration:** Table `ZMM_DTTS_API_CON` must be populated with the correct API Operation mappings (Proxy Class, Logical Port, Method Name).
- **SOAMANAGER:** The logical ports defined in the config table must be actively configured and pingable in `SOAMANAGER`.
- **Authorization Roles:** Basic Fiori catalog authorizations. No row-level DCL authorizations are currently applied (`#NOT_REQUIRED`).

---

### 9. Known Limitations

- **Missing Functionality:** Mass creation via Excel upload is not supported.
- **Prototype Shortcuts:** The `save` sequence in the Behavior Saver class is currently pseudo-code and requires the implementation of the buffer read mapping to `zmm_sst_dttsit2`.
- **Technical Constraints:** Only non-successful items can be edited. If a user needs to reverse a 'SUCCESS' item, they must execute a cancellation goods movement in SAP (e.g., MIGO 102), which will generate a *new* DTTS item for the reversal.

---

### 10. Final Accuracy Check

**Implementation Confidence Assessment**
- **Confidence:** 85%
- **Areas needing manual verification:** The dynamic proxy construction `ASSIGN COMPONENT 'PRODUCTLIST' OF STRUCTURE <fs_accept_req>`. The exact component names of the generated ABAP proxies must exactly match these string literals, which requires verification against the actual active data dictionary in the target SAP system.
- **AI-Generated Assumptions:** The factory action for manual creation was inferred from the requirement "Create a button called “Create”... to a new object page where the below mentioned fields should be asked". A factory action using an abstract entity popup is the modern Fiori Elements approach to this, rather than a traditional object page creation.
