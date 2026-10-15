-- CareFlow: Patient Pathway Analysis
-- Identifies the most frequent transitions between hospital activities.

WITH ordered_events AS (
    SELECT
        case_id,
        activity,
        timestamp,
        LEAD(activity) OVER (
            PARTITION BY case_id
            ORDER BY timestamp
        ) AS next_activity
    FROM
        `careflow-process-mining-511617.careflow.raw_ehr_events`
)
SELECT
    activity AS from_activity,
    next_activity AS to_activity,
    COUNT(*) AS transition_count,
    COUNT(DISTINCT case_id) AS patient_visits
FROM
    ordered_events
WHERE
    next_activity IS NOT NULL
GROUP BY
    from_activity,
    to_activity
ORDER BY
    transition_count DESC
LIMIT 20;