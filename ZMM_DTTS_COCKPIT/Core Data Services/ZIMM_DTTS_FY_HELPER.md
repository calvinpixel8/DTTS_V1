```abap
@AbapCatalog.sqlViewName: 'ZV_DTTS_FYHLP'
@AbapCatalog.compiler.compareFilter: true
@AbapCatalog.preserveKey: true
@ClientHandling.algorithm: #SESSION_VARIABLE
@EndUserText.label: 'DTTS Fiscal Year Helper'

define view ZIMM_DTTS_FY_HELPER
  as select from ZIMMDTTS_3
{
  key mandt,
  key DOC_YEAR,
  key mat_doc,
  key mvt_type,
  key item_no,
      tran_id,
      zeile,
      product,
      prod_name,
      prod_qty,
      prod_unit,
      gtin,
      batch,
      exp_date,
      notif_id,
      tr_response,
      sr_number,
      created_date,
      created_time,
      created_by,
      changed_date,
      changed_time,
      changed_by,
      prod_stat,
      trans_stat,

    cast(
      case substring( created_date, 5, 2 )

        when '01' then
          case substring( created_date, 4, 1 )
            when '1' then concat( substring( created_date, 1, 3 ), '0' )
            when '2' then concat( substring( created_date, 1, 3 ), '1' )
            when '3' then concat( substring( created_date, 1, 3 ), '2' )
            when '4' then concat( substring( created_date, 1, 3 ), '3' )
            when '5' then concat( substring( created_date, 1, 3 ), '4' )
            when '6' then concat( substring( created_date, 1, 3 ), '5' )
            when '7' then concat( substring( created_date, 1, 3 ), '6' )
            when '8' then concat( substring( created_date, 1, 3 ), '7' )
            when '9' then concat( substring( created_date, 1, 3 ), '8' )
            when '0' then
              case substring( created_date, 3, 1 )
                when '1' then concat( substring( created_date, 1, 2 ), '09' )
                when '2' then concat( substring( created_date, 1, 2 ), '19' )
                when '3' then concat( substring( created_date, 1, 2 ), '29' )
                when '4' then concat( substring( created_date, 1, 2 ), '39' )
                when '5' then concat( substring( created_date, 1, 2 ), '49' )
                when '6' then concat( substring( created_date, 1, 2 ), '59' )
                when '7' then concat( substring( created_date, 1, 2 ), '69' )
                when '8' then concat( substring( created_date, 1, 2 ), '79' )
                when '9' then concat( substring( created_date, 1, 2 ), '89' )
                else          concat( substring( created_date, 1, 2 ), '99' )
              end
            else substring( created_date, 1, 4 )
          end

        when '02' then
          case substring( created_date, 4, 1 )
            when '1' then concat( substring( created_date, 1, 3 ), '0' )
            when '2' then concat( substring( created_date, 1, 3 ), '1' )
            when '3' then concat( substring( created_date, 1, 3 ), '2' )
            when '4' then concat( substring( created_date, 1, 3 ), '3' )
            when '5' then concat( substring( created_date, 1, 3 ), '4' )
            when '6' then concat( substring( created_date, 1, 3 ), '5' )
            when '7' then concat( substring( created_date, 1, 3 ), '6' )
            when '8' then concat( substring( created_date, 1, 3 ), '7' )
            when '9' then concat( substring( created_date, 1, 3 ), '8' )
            when '0' then
              case substring( created_date, 3, 1 )
                when '1' then concat( substring( created_date, 1, 2 ), '09' )
                when '2' then concat( substring( created_date, 1, 2 ), '19' )
                when '3' then concat( substring( created_date, 1, 2 ), '29' )
                when '4' then concat( substring( created_date, 1, 2 ), '39' )
                when '5' then concat( substring( created_date, 1, 2 ), '49' )
                when '6' then concat( substring( created_date, 1, 2 ), '59' )
                when '7' then concat( substring( created_date, 1, 2 ), '69' )
                when '8' then concat( substring( created_date, 1, 2 ), '79' )
                when '9' then concat( substring( created_date, 1, 2 ), '89' )
                else          concat( substring( created_date, 1, 2 ), '99' )
              end
            else substring( created_date, 1, 4 )
          end

        when '03' then
          case substring( created_date, 4, 1 )
            when '1' then concat( substring( created_date, 1, 3 ), '0' )
            when '2' then concat( substring( created_date, 1, 3 ), '1' )
            when '3' then concat( substring( created_date, 1, 3 ), '2' )
            when '4' then concat( substring( created_date, 1, 3 ), '3' )
            when '5' then concat( substring( created_date, 1, 3 ), '4' )
            when '6' then concat( substring( created_date, 1, 3 ), '5' )
            when '7' then concat( substring( created_date, 1, 3 ), '6' )
            when '8' then concat( substring( created_date, 1, 3 ), '7' )
            when '9' then concat( substring( created_date, 1, 3 ), '8' )
            when '0' then
              case substring( created_date, 3, 1 )
                when '1' then concat( substring( created_date, 1, 2 ), '09' )
                when '2' then concat( substring( created_date, 1, 2 ), '19' )
                when '3' then concat( substring( created_date, 1, 2 ), '29' )
                when '4' then concat( substring( created_date, 1, 2 ), '39' )
                when '5' then concat( substring( created_date, 1, 2 ), '49' )
                when '6' then concat( substring( created_date, 1, 2 ), '59' )
                when '7' then concat( substring( created_date, 1, 2 ), '69' )
                when '8' then concat( substring( created_date, 1, 2 ), '79' )
                when '9' then concat( substring( created_date, 1, 2 ), '89' )
                else          concat( substring( created_date, 1, 2 ), '99' )
              end
            else substring( created_date, 1, 4 )
          end

        else substring( created_date, 1, 4 )

            end as abap.numc(4)
        ) as fiscal_year,
      operation
}
```
