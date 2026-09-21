# DAX Measures

These reconstruct the measures implied by the field list and visuals in the
screenshots (`Total`, `Latest Month Wait List`, `PY Latest Month Wait List`,
`Median Wait List`, `Avg/Med Wait`, `Calculation Method`). Exact original DAX
wasn't visible in the screenshots — these are working equivalents you can
paste in and adjust.

Create all of these in the `All_Data` table unless noted otherwise.

## Core totals

```dax
Total = SUM('All_Data'[Total])
```

```dax
Latest Month Wait List =
CALCULATE(
    [Total],
    FILTER(
        ALL('All_Data'[Archive_Date]),
        'All_Data'[Archive_Date] = MAX('All_Data'[Archive_Date])
    )
)
```

```dax
PY Latest Month Wait List =
CALCULATE(
    [Latest Month Wait List],
    DATEADD('All_Data'[Archive_Date], -1, YEAR)
)
```

> `DATEADD` needs a proper Date table marked as a date table for best results.
> If you don't have one yet, add a `Calendar` table (`CALENDAR(MIN('All_Data'[Archive_Date]), MAX('All_Data'[Archive_Date]))`),
> mark it as the date table, and relate it to `All_Data[Archive_Date]`.

## Weighted average / median wait (drives the "Avg/Med Wait" card)

Relies on `Time_Bands_Midpoint` from `Data_Model.md`.

```dax
Avg Wait (Months) =
DIVIDE(
    SUMX(
        'All_Data',
        'All_Data'[Total] * RELATED('Time_Bands_Midpoint'[Midpoint_Months])
    ),
    [Total]
)
```

Weighted median is harder in DAX since there's no native weighted-median
function — this expands each band's midpoint by its patient count and finds
the 50th-percentile crossing point:

```dax
Median Wait List =
VAR BandTotals =
    ADDCOLUMNS(
        SUMMARIZE('All_Data', 'Time_Bands_Midpoint'[Midpoint_Months]),
        "@BandTotal", CALCULATE([Total])
    )
VAR SortedBands =
    ADDCOLUMNS(
        BandTotals,
        "@CumulativeTotal",
        VAR CurrentMidpoint = [Midpoint_Months]
        RETURN
            SUMX(
                FILTER(BandTotals, [Midpoint_Months] <= CurrentMidpoint),
                [@BandTotal]
            )
    )
VAR HalfTotal = DIVIDE([Total], 2)
RETURN
    MINX(
        FILTER(SortedBands, [@CumulativeTotal] >= HalfTotal),
        [Midpoint_Months]
    )
```

## Calculation Method switch (the disconnected `Calc Method` slicer)

```dax
Calculation Method = SELECTEDVALUE('Calc Method'[Method], "Average")
```

```dax
Avg/Med Wait =
SWITCH(
    [Calculation Method],
    "Average", [Avg Wait (Months)],
    "Median", [Median Wait List],
    [Avg Wait (Months)]
)
```

This single measure is what both the **54.38 Avg/Med Wait** card and the
**"Avg/Med Wait List by Time_Bands and Age_Profile"** bar chart use — the
slicer on `Calc Method[Method]` toggles every visual referencing this measure
at once, which is the whole point of the disconnected table pattern.

## Supporting measures used in the visuals

```dax
Sum of Total by Year =
SUM('All_Data'[Total])
```
(used directly on the year-over-year line chart, with `Archive_Date` on the
axis set to Year granularity and `Case_Type` as legend/small multiple)

```dax
Total Inpatient = CALCULATE([Total], 'All_Data'[Case_Type] IN {"Inpatient", "Day Case"})
Total Outpatient = CALCULATE([Total], 'All_Data'[Case_Type] = "Outpatient")
```
(feeds the donut "Avg/Med Wait List by Case_Type")
