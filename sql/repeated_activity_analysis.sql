-- CareFlow: Repeated Activity Analysis
-- Identifies consecutive repetitions of the same hospital activity.

WITH ordered_events AS (
    SELECT
        case_id,
        activity,
        timestamp,
        LAG(activity) OVER (
            PARTITION BY case_id
            ORDER BY timestamp
        ) AS previous_activity
    FROM
        `careflow-process-mining-511617.careflow.raw_ehr_events`
),
repeated_activities AS (
    SELECT
        case_id,
        activity,
        COUNT(*) AS repeat_count
    FROM
        ordered_events
    WHERE
        activity = previous_activity
    GROUP BY
        case_id,
        activity
)
SELECT
    activity,
    COUNT(DISTINCT case_id) AS affected_patient_visits,
    SUM(repeat_count) AS repeated_event_count
FROM
    repeated_activities
GROUP BY
    activity
ORDER BY
    repeated_event_count DESC;