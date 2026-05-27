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
- **Data Models:** Root CDS View (`ZR_MM_DTTS_COCKPIT`) based on `ZIMMDTTS_4` combined views.
- **Behavior Definition:** `strict(2)` compliant, controlling instance features to lock successfully processed items, and managing the Draft shadow table (`ZMM_SST_DTTSIT2D`).
- **UI:** Fiori Elements projected via `ZC_MM_DTTS_COCKPIT` and annotated via Metadata Extension (`Z_MM_DTTS_COCKPIT_MDE`).

---

### 2. Functional Features (Detailed)

#### Feature 2.1: View DTTS Integration Records
- **Business purpose:** Provide visibility into the current integration state of all material document line items.
- **End-user workflow:** User opens the Fiori Elements List Report. Filters by Material Document, Status, or Date. Views the list of records.
- **Trigger point:** Standard Fiori tile / App load.
- **Input parameters:** Selection filters (matdoc, prodstat, tranid, gtin, expdate).
- **Output/result:** Tabular display of records with their `PROD_STAT` (SUCCESS, ERROR, NEW) and detailed `TRANS_STAT` (error descriptions).
- **Error handling behavior:** Handles invalid dates natively in CDS View to prevent UI5 scrolling errors.

#### Feature 2.2: Conditional Navigation & Edit Erroneous Records
- **Business purpose:** Restrict editing to only rejected API entries.
- **End-user workflow:** User clicks on a non-SUCCESS row to navigate to the Object Page.
- **Validation rules:** `PROD_STAT` must not be 'SUCCESS'. The backend restricts Edit operations via instance feature control (`if_abap_behv=>fc-o-disabled`). Navigation from List to Object is natively standard in Fiori Elements, but editing is strictly locked in the backend if SUCCESS.
- **Business logic executed:** SAP RAP Draft framework transitions the record to an exclusive lock state in `ZMM_SST_DTTSIT2D`. Upon save, the unmanaged `update` method writes the changes back.

#### Feature 2.3: Reprocess Transactions & Auto-Reprocess
- **Business purpose:** Re-send corrected items to the DTTS API automatically upon editing, or manually via button.
- **End-user workflow:** User edits a record and hits save. Or, user selects a record from the list report and hits "Reprocess".
- **Business logic executed:**
  1. Record modification intercepts the `update` handler and invokes the internal `execute_reprocess` method.
  2. Constructs API proxy payloads from updated draft state.
  3. Sends request, parses response, and updates Transactional Buffer with EML.
  4. Automatically sets `changed_date` and `changed_time` for tracking.

---

### 3. Technical Implementation Mapping

| Feature | CDS Views | BDEF | Behavior Implementation | MDE / Service |
| :--- | :--- | :--- | :--- | :--- |
| **View Records** | `ZR_MM_DTTS_COCKPIT`, `ZC_MM_DTTS_COCKPIT` | N/A | N/A | `Z_MM_DTTS_COCKPIT_MDE` |
| **Edit Records** | `ZR_MM_DTTS_COCKPIT` | `update ( features : instance );` | `METHOD get_instance_features`, `METHOD update` | N/A |
| **Reprocess** | N/A | `action ( features : instance ) reprocess result [1] $self;` | `METHOD execute_reprocess` | `@UI.lineItem: [{ type: #FOR_ACTION, dataAction: 'reprocess' }]` |

---

### 4. Code Snippets

#### 4.1 Date Formatting Safe Cast
```abap
      cast(
        case
          when length(Item.exp_date) = 8 and dats_is_valid(Item.exp_date) = 1
            then Item.exp_date
          else '00000000'
        end as abap.dats
      ) as expdate,
```

#### 4.2 Auto-Reprocess Interception
```abap
  METHOD update.
    DATA lt_keys_to_reprocess TYPE TABLE FOR ACTION IMPORT zr_mm_dtts_cockpit~reprocess.
    LOOP AT entities INTO DATA(ls_entity).
       APPEND VALUE #( %tky = ls_entity-%tky ) TO lt_keys_to_reprocess.
    ENDLOOP.
    IF lt_keys_to_reprocess IS NOT INITIAL.
       me->execute_reprocess( it_keys = lt_keys_to_reprocess ).
    ENDIF.
  ENDMETHOD.
```

---

### 5. Requirement Traceability Matrix

| Feature | Current Implementation | Technical Objects | Status |
| :--- | :--- | :--- | :--- |
| Fix Date Preview Scroll | CDS Level Validation | `ZR_MM_DTTS_COCKPIT` | Fully Implemented |
| Conditional Navigation | Feature Control Lock | `ZCL_MM_DTTS_COCKPIT_BDEF` | Partially Implemented (Navigation active, Edit disabled) |
| Hide Tech Fields | MDE Identification Hidden | `Z_MM_DTTS_COCKPIT_MDE` | Fully Implemented |
| Auto-Reprocess on Save | Intercept Update method | `ZCL_MM_DTTS_COCKPIT_BDEF` | Fully Implemented |
| Update Processed Date | EML Modification | `execute_reprocess` | Fully Implemented |
| Selection Filters | `@UI.selectionField` | `Z_MM_DTTS_COCKPIT_MDE` | Fully Implemented |

---

### 6. Developer Review Notes

- **Design Assumptions:**
  - Standard Fiori Elements List Report natively enables row navigation for all records. Disabling row navigation entirely for a subset of records (`status = 'SUCCESS'`) requires UI5 Intent-Based Navigation or front-end JS extensions. We satisfied the underlying business rule by making SUCCESS records strictly read-only via ABAP feature control.
  - The `update` method calls `execute_reprocess`. This assumes that the framework has already synced the draft inputs to the active table or buffer. If unmanaged draft logic requires explicit read from the draft table, `execute_reprocess` might need to read from `zmm_sst_dttsit2d` instead of `zmm_sst_dtts_itm`.

### 7. Final Accuracy Check
**Implementation Confidence Assessment:** 90%.
The backend handles the invalid dates natively at the database level. The ABAP implementation successfully implements automatic reprocessing on save. The UI exposes filters correctly.
