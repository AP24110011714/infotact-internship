
-- ============================================================
-- CAREFLOW: CREATE BIGQUERY MART TABLES
-- Source: raw_ehr_events
-- Project: careflow-process-mining-511617
-- Dataset: careflow
-- ============================================================


-- ============================================================
-- 1. TRANSITION TIMES
-- Calculate transitions and average waiting time between
-- consecutive activities for each patient case.
-- ============================================================

CREATE OR REPLACE TABLE
`careflow-process-mining-511617.careflow.transition_times` AS

WITH ordered_events AS (

    SELECT
        case_id,
        activity AS from_activity,
        timestamp AS event_timestamp,

        LEAD(activity) OVER (
            PARTITION BY case_id
            ORDER BY timestamp, activity, resource
        ) AS to_activity,

        LEAD(timestamp) OVER (
            PARTITION BY case_id
            ORDER BY timestamp, activity, resource
        ) AS next_timestamp

    FROM
        `careflow-process-mining-511617.careflow.raw_ehr_events`

)

SELECT
    from_activity,
    to_activity,

    COUNT(*) AS transition_count,

    ROUND(
        AVG(
            TIMESTAMP_DIFF(
                next_timestamp,
                event_timestamp,
                MINUTE
            )
        ),
        2
    ) AS avg_wait_minutes

FROM ordered_events

WHERE
    to_activity IS NOT NULL
    AND next_timestamp >= event_timestamp

GROUP BY
    from_activity,
    to_activity;


-- ============================================================
-- 2. LOOPBACKS
-- Identify activities repeated after an intervening activity.
--
-- Example:
-- Doctor Consultation -> Blood Test -> Doctor Consultation
--
-- Counts repeated activity occurrences for each case.
-- ============================================================

CREATE OR REPLACE TABLE
`careflow-process-mining-511617.careflow.loopbacks` AS

WITH ordered_events AS (

    SELECT
        case_id,
        activity,
        timestamp,

        ROW_NUMBER() OVER (
            PARTITION BY case_id
            ORDER BY timestamp, activity, resource
        ) AS event_number,

        LAG(activity) OVER (
            PARTITION BY case_id
            ORDER BY timestamp, activity, resource
        ) AS previous_activity

    FROM
        `careflow-process-mining-511617.careflow.raw_ehr_events`

),

loopback_events AS (

    SELECT
        curr.case_id,
        curr.previous_activity AS from_activity,
        curr.activity AS to_activity

    FROM ordered_events AS curr

    WHERE
        curr.previous_activity IS NOT NULL

        AND EXISTS (

            SELECT 1

            FROM ordered_events AS prev

            WHERE
                prev.case_id = curr.case_id
                AND prev.activity = curr.activity
                AND prev.event_number < curr.event_number - 1

        )

)

SELECT
    case_id,
    from_activity,
    to_activity,

    COUNT(*) AS loop_count

FROM loopback_events

GROUP BY
    case_id,
    from_activity,
    to_activity;


-- ============================================================
-- 3. KPI SUMMARY
-- Calculate overall patient and process performance metrics.
--
-- Metrics:
-- Total cases
-- Total events
-- Average case duration
-- Average waiting time
-- Loopback rate percentage
-- ============================================================

CREATE OR REPLACE TABLE
`careflow-process-mining-511617.careflow.kpi_summary` AS

WITH case_metrics AS (

    SELECT
        case_id,

        TIMESTAMP_DIFF(
            MAX(timestamp),
            MIN(timestamp),
            MINUTE
        ) AS case_duration_minutes

    FROM
        `careflow-process-mining-511617.careflow.raw_ehr_events`

    GROUP BY
        case_id

),

event_metrics AS (

    SELECT
        COUNT(*) AS total_events,
        COUNT(DISTINCT case_id) AS total_cases

    FROM
        `careflow-process-mining-511617.careflow.raw_ehr_events`

),

wait_metrics AS (

    SELECT
        ROUND(
            AVG(
                TIMESTAMP_DIFF(
                    next_timestamp,
                    event_timestamp,
                    MINUTE
                )
            ),
            2
        ) AS avg_wait_minutes

    FROM (

        SELECT
            timestamp AS event_timestamp,

            LEAD(timestamp) OVER (
                PARTITION BY case_id
                ORDER BY timestamp, activity, resource
            ) AS next_timestamp

        FROM
            `careflow-process-mining-511617.careflow.raw_ehr_events`

    )

    WHERE
        next_timestamp IS NOT NULL

),

loopback_metrics AS (

    SELECT
        COUNT(DISTINCT case_id) AS loopback_cases

    FROM
        `careflow-process-mining-511617.careflow.loopbacks`

)

SELECT
    event_metrics.total_cases,
    event_metrics.total_events,

    ROUND(
        AVG(case_metrics.case_duration_minutes),
        2
    ) AS avg_case_duration_minutes,

    wait_metrics.avg_wait_minutes,

    ROUND(
        SAFE_DIVIDE(
            loopback_metrics.loopback_cases,
            event_metrics.total_cases
        ) * 100,
        2
    ) AS loopback_rate

FROM event_metrics

CROSS JOIN case_metrics
CROSS JOIN wait_metrics
CROSS JOIN loopback_metrics

GROUP BY
    event_metrics.total_cases,
    event_metrics.total_events,
    wait_metrics.avg_wait_minutes,
    loopback_metrics.loopback_cases;


-- ============================================================
-- END OF CAREFLOW MART CREATION
-- ============================================================
