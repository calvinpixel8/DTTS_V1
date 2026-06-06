```abap
projection;
strict ( 2 );
use draft;

define behavior for ZC_MM_DTTS_COCKPIT alias Item
{
  //use create; " Disabled standard create to enforce popup creation
  use update;
  use delete;

  use action reprocess;
  use action createWithPopup;

  use action Edit;
  use action Activate;
  use action Discard;
  use action Resume;
  use action Prepare;
}
```
