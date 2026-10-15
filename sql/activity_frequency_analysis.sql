-- CareFlow: Hospital Activity Frequency Analysis

SELECT
    activity,
    COUNT(*) AS total_events,
    COUNT(DISTINCT case_id) AS patient_visits
FROM
    `careflow-process-mining-511617.careflow.raw_ehr_events`
GROUP BY
    activity
ORDER BY
    total_events DESC;