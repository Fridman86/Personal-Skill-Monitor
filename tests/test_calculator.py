"""
Tests for src/utils/calculator.py
"""
import pytest
from src.utils.calculator import (
    training_time, format_duration, sp_required,
    sp_per_minute, plan_total_time, get_skill_rank,
)

ATTRS_BALANCED = {
    "intelligence": 20, "memory": 20,
    "perception": 20, "willpower": 20, "charisma": 20,
}
ATTRS_HIGH_INT = {
    "intelligence": 27, "memory": 21,
    "perception": 17, "willpower": 17, "charisma": 17,
}


class TestFormatDuration:
    def test_zero(self):
        assert format_duration(0) == "0s"

    def test_negative(self):
        assert format_duration(-5) == "0s"

    def test_seconds_only(self):
        assert format_duration(45) == "45s"

    def test_minutes(self):
        assert format_duration(90) == "1m 30s"

    def test_hours(self):
        assert format_duration(3661) == "1h 1m 01s"

    def test_days(self):
        result = format_duration(86400 + 3600 + 60 + 1)
        assert "1d" in result
        assert "1h" in result


class TestSpRequired:
    def test_level_0_to_1(self):
        # Rank-1 skill: 250 SP for level 1
        assert sp_required("Drones", 0, 1) == 250

    def test_level_0_to_5(self):
        # Rank-1 skill: 256_000 SP total
        assert sp_required("Drones", 0, 5) == 256_000

    def test_level_4_to_5(self):
        # 256_000 - 45_255 = 210_745
        assert sp_required("Drones", 4, 5) == 210_745

    def test_rank_multiplier(self):
        # Large Hybrid Turret rank=5
        rank5_total = sp_required("Large Hybrid Turret", 0, 5)
        rank1_total = sp_required("Drones", 0, 5)
        assert rank5_total == rank1_total * 5

    def test_same_level_returns_zero(self):
        assert sp_required("Drones", 3, 3) == 0

    def test_from_higher_than_to(self):
        assert sp_required("Drones", 5, 3) == 0


class TestSpPerMinute:
    def test_balanced_attrs(self):
        # 20 + 20/2 = 30
        spm = sp_per_minute(ATTRS_BALANCED, "Drones")
        assert spm == pytest.approx(30.0)

    def test_high_int(self):
        # Science uses INT+MEM: 27 + 21/2 = 37.5
        spm = sp_per_minute(ATTRS_HIGH_INT, "Science")
        assert spm == pytest.approx(37.5)

    def test_unknown_skill_uses_default(self):
        # Unknown skill falls back to intelligence+memory
        spm = sp_per_minute(ATTRS_BALANCED, "NonExistentSkillXYZ")
        assert spm > 0


class TestTrainingTime:
    def test_positive_time(self):
        secs = training_time("Drones", 0, 1, ATTRS_BALANCED)
        assert secs > 0

    def test_higher_rank_takes_longer(self):
        t_rank1 = training_time("Drones", 0, 5, ATTRS_BALANCED)
        t_rank5 = training_time("Large Hybrid Turret", 0, 5, ATTRS_BALANCED)
        assert t_rank5 > t_rank1

    def test_same_level_zero_time(self):
        assert training_time("Drones", 3, 3, ATTRS_BALANCED) == 0.0

    def test_zero_spm_returns_zero(self):
        bad_attrs = {k: 0 for k in ATTRS_BALANCED}
        assert training_time("Drones", 0, 1, bad_attrs) == 0.0


class TestPlanTotalTime:
    def test_empty_plan(self):
        assert plan_total_time([], ATTRS_BALANCED) == 0.0

    def test_single_entry(self):
        plan = [{"name": "Drones", "level": 1}]
        total = plan_total_time(plan, ATTRS_BALANCED)
        expected = training_time("Drones", 0, 1, ATTRS_BALANCED)
        assert total == pytest.approx(expected)

    def test_multi_entry(self):
        plan = [
            {"name": "Drones", "level": 1},
            {"name": "Drones", "level": 2},
        ]
        total = plan_total_time(plan, ATTRS_BALANCED)
        assert total > 0


class TestGetSkillRank:
    def test_known_skill(self):
        assert get_skill_rank("Drones") == 1
        assert get_skill_rank("Large Hybrid Turret") == 5

    def test_unknown_skill_default(self):
        assert get_skill_rank("NonExistentSkillXYZ") == 1
