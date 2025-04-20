WITH Consumption_Diff AS (
    SELECT 
        e1.CA_Number,
        e1.Customer_Name,
        e1.Meter_Number,
        e1.Tariff_Plan,	
        e1.Fixed_Charge,
        e1.Power_Factor,
        e2.Billing_Month AS Current_Month,
        e1.Billing_Month AS Previous_Month,
        e2.Kwh_Consumption - e1.Kwh_Consumption AS Kwh_Difference
    FROM Electricity_Bills e1
    JOIN Electricity_Bills2 e2 ON e1.CA_Number = e2.CA_Number
    WHERE e1.CA_Number = 'CA0987654321'  -- Replace with a specific CA Number
)
SELECT 
    CA_Number,
    Customer_Name,
    Meter_Number,
    Tariff_Plan,
    Fixed_Charge,
    Current_Month,
    Previous_Month,
    Kwh_Difference,

    -- Energy Charge Calculation Based on kWh Slabs
    CASE 
        WHEN Kwh_Difference <= 100 THEN Kwh_Difference * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)
        WHEN Kwh_Difference <= 300 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                       ((Kwh_Difference - 100) * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END))
        WHEN Kwh_Difference <= 500 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                       (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                                       ((Kwh_Difference - 300) * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END))
        ELSE (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
             (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
             (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END)) + 
             ((Kwh_Difference - 500) * (CASE WHEN Tariff_Plan = 'Residential' THEN 8.5 ELSE 12 END))
    END AS Energy_Charge,

    -- Fuel Surcharge (Assuming 15% per kWh)
    (Kwh_Difference * 0.15) AS Fuel_Surcharge,

    -- Tax Calculation (10% of total charges)
    (0.10 * (Fixed_Charge + 
             CASE 
                WHEN Kwh_Difference <= 100 THEN Kwh_Difference * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)
                WHEN Kwh_Difference <= 300 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                              ((Kwh_Difference - 100) * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END))
                WHEN Kwh_Difference <= 500 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                              (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                                              ((Kwh_Difference - 300) * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END))
                ELSE (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                     (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                     (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END)) + 
                     ((Kwh_Difference - 500) * (CASE WHEN Tariff_Plan = 'Residential' THEN 8.5 ELSE 12 END))
             END + 
             (Kwh_Difference * 0.15))) AS Tax,

    -- Power Factor Penalty (5% penalty if Power Factor < 0.90)
    CASE 
        WHEN Power_Factor < 0.90 THEN 0.05 * (Fixed_Charge + 
            CASE 
                WHEN Kwh_Difference <= 100 THEN Kwh_Difference * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)
                WHEN Kwh_Difference <= 300 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                              ((Kwh_Difference - 100) * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END))
                WHEN Kwh_Difference <= 500 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                              (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                                              ((Kwh_Difference - 300) * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END))
                ELSE (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                     (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                     (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END)) + 
                     ((Kwh_Difference - 500) * (CASE WHEN Tariff_Plan = 'Residential' THEN 8.5 ELSE 12 END))
            END + 
            (Kwh_Difference * 0.15)) 
        ELSE 0 
    END AS Power_Factor_Penalty,

    -- Total Amount Calculation
    (Fixed_Charge + 
     CASE 
         WHEN Kwh_Difference <= 100 THEN Kwh_Difference * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)
         WHEN Kwh_Difference <= 300 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                         ((Kwh_Difference - 100) * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END))
         ELSE Kwh_Difference * 8 -- Default slab for higher consumption
     END +
     (Kwh_Difference * 0.15) + 
     (0.10 * (Fixed_Charge + Kwh_Difference * 8)) +
     CASE WHEN Power_Factor < 0.90 THEN 0.05 * (Fixed_Charge + Kwh_Difference * 8) ELSE 0 END
    ) AS Total_Amount
FROM Consumption_Diff;
