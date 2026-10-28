%pip install pytest

import pandas as pd
import pytest

P = "data/processed/"
CLEAN = P + "clean_log.csv"          # EDIT to your cleaned file
CASE, ACTIVITY, TIME = "case_id", "activity", "timestamp"   # EDIT if different


@pytest.fixture(scope="module")
def log():
    return pd.read_csv(CLEAN, parse_dates=[TIME])


def test_no_missing_core_fields(log):
    assert log[[CASE, ACTIVITY, TIME]].isna().sum().sum() == 0


def test_no_duplicate_events(log):
    assert not log.duplicated(subset=[CASE, ACTIVITY, TIME]).any()


def test_timestamps_increase_within_case(log):
    ordered = log.sort_values([CASE, TIME])
    diffs = ordered.groupby(CASE)[TIME].diff().dropna()
    assert (diffs >= pd.Timedelta(0)).all()


def test_case_durations_match_log(log):
    dur = pd.read_csv(P + "case_durations.csv")
    assert len(dur) == log[CASE].nunique()
    assert (dur["duration_hours"] >= 0).all()


def test_variants_add_up(log):
    var = pd.read_csv(P + "variants.csv")
    assert var["cases"].sum() == log[CASE].nunique()
    assert abs(var["percent"].sum() - 100) < 1


def test_waiting_times_not_negative():
    wait = pd.read_csv(P + "transition_waiting_times.csv")
    assert (wait["mean_min"] >= 0).all()
    assert (wait["count"] > 0).all()
