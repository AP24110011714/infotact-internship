# Member 1 — Data Collection & Data Cleaning

## Overview

The first objective of the project was to collect a suitable clinical dataset and prepare it for analysis by cleaning and validating the raw data. For this project, the dataset used was a patient-level clinical dataset containing sepsis-related health indicators. The original file was stored as an Excel file and later converted into a cleaned CSV dataset for downstream analysis and reporting.

The dataset included key patient information such as Patient_ID, Admission_Date, Temperature_C, BP_Systolic, BP_Diastolic, Heart_Rate, WBC_Count, Lactate_mmol_L, Sepsis_Flag, Ward, and Doctor_On_Duty. These fields are essential for exploring clinical conditions, identifying patterns in patient outcomes, and understanding clinical characteristics across different departments and hospital units. Although the project is focused on clinical pathway and process mining, the available dataset was structured as a patient-level clinical record rather than a traditional event-log format. Therefore, the data cleaning process focused on standardizing patient observations and validating clinical values rather than event sequencing.

## Data Collection

During the data collection phase, the raw dataset was reviewed to understand the structure, variables, and data quality issues. The main variables were identified and mapped to a consistent format. This included recognizing the patient identifier, date field, clinical measurements, binary sepsis indicator, and categorical variables such as ward and doctor on duty. The dataset was then standardized by converting column names to a consistent lowercase format, removing unnecessary inconsistencies, and ensuring that all columns were interpretable for analysis.

## Data Cleaning Process

The cleaning process involved several important steps. First, duplicate records were checked and eliminated based on the patient identifier to avoid repeated patient entries. Second, date values were parsed into a proper datetime format so that admission dates could be used consistently and accurately. Third, missing values were identified and handled appropriately; rows with missing patient IDs or invalid admission dates were removed because they could not be reliably used in downstream analysis. Fourth, numerical clinical values such as temperature, blood pressure, heart rate, WBC count, and lactate were converted to numeric data types and checked against realistic clinical ranges. Values that were clearly invalid or suspicious, such as negative lactate or WBC values, were excluded to improve dataset reliability. Finally, categorical variables such as ward and doctor names were normalized for consistency, and the sepsis flag was standardized into a clean Yes/No format.

A major challenge in the cleaning stage was dealing with inconsistent and invalid medical values. The raw dataset contained values outside expected clinical ranges, which could be caused by transcription errors, missing values, or measurement inaccuracies. Such values were reviewed carefully and removed or corrected where necessary to preserve the integrity of the analytical dataset. Another issue was inconsistent formatting in textual fields, including case variations and spacing differences. These were standardized to improve consistency across the dataset.

## Data Validation

After cleaning, the dataset was validated by checking the total number of rows, unique patient IDs, date range, and missing values. The dataset was also screened to confirm that the clinical values were within acceptable boundaries and that duplicates had been removed. A cleaned CSV file was then created and saved in the repository as the processed dataset. This cleaned dataset can now be used for further analysis, including patient comparison, clinical pattern exploration, and preparation for future process mining or analytical modeling tasks.

The deliverable for this phase includes the cleaned dataset file and the data-cleaning documentation. The cleaned dataset is ready for analysis and can serve as the base for subsequent tasks such as exploratory analysis, clinical profiling, and identifying patterns in patient status and treatment workflow. The data cleaning stage was therefore essential to ensure that the final dataset is reliable, valid, and suitable for evidence-based analysis.

## Conclusion

In conclusion, Member 1 focused on collecting a suitable clinical dataset and preparing it for analysis through systematic cleaning and validation. The process included identifying relevant clinical variables, standardizing column names, handling missing or invalid values, removing duplicates, validating numeric ranges, and producing a clean dataset for further analysis. This stage ensured data quality and made the dataset suitable for the next phase of the internship project. The successful completion of this member contributed to the overall objective of building a robust clinical analytics and process mining workflow.

This phase produced a cleaned and validated clinical dataset that can be used for further exploratory analysis, patient comparison, and process-based understanding of care pathways. The final cleaned dataset is now available in the repository and serves as a solid foundation for subsequent analytical tasks within the project.
