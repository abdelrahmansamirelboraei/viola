from viola.reporting.weekly import build_weekly_report
from viola.growth.planner import GrowthPlanner
from viola.memory.store import MemoryStore

def test_checkin_and_reporting_pipeline():
    store = MemoryStore()
    store.append_checkin("test_user_2", 50, "test note")

    report = build_weekly_report("test_user_2", days=7)
    assert report["user_id"] == "test_user_2"
    assert "recommendations" in report

    plan = GrowthPlanner().build_weekly_plan("test_user_2", days=7)
    assert plan.user_id == "test_user_2"
    assert len(plan.daily_micro_habits) >= 1
