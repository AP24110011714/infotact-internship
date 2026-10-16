-- CareFlow: Patient Transition Time Analysis

WITH ordered_events AS (
    SELECT
        case_id,
        activity AS current_activity,
        timestamp AS current_timestamp,
        LEAD(activity) OVER (
            PARTITION BY case_id
            ORDER BY timestamp
        ) AS next_activity,
        LEAD(timestamp) OVER (
            PARTITION BY case_id
            ORDER BY timestamp
        ) AS next_timestamp
    FROM
        `careflow-process-mining-511617.careflow.raw_ehr_events`
)
SELECT
    current_activity,
    next_activity,
    COUNT(*) AS transition_count,
    ROUND(
        AVG(
            TIMESTAMP_DIFF(
                next_timestamp,
                current_timestamp,
                MINUTE
            )
        ),
        2
    ) AS avg_transition_minutes,
    MAX(
        TIMESTAMP_DIFF(
            next_timestamp,
            current_timestamp,
            MINUTE
        )
    ) AS max_transition_minutes
FROM
    ordered_events
WHERE
    next_activity IS NOT NULL
    AND next_timestamp >= current_timestamp
GROUP BY
    current_activity,
    next_activity
ORDER BY
    avg_transition_minutes DESC;