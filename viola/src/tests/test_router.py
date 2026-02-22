from viola.router import process_text

def test_router_cbt_mode():
    out = process_text("انا قلقان ومش قادر اركز وحاسس اني دايمًا هفشل", user_id="test_user")
    assert out["mode"] == "cbt"
    assert "analysis" in out
    assert "plan" in out
    assert "memory_summary" in out

def test_router_crisis_mode():
    out = process_text("مش قادر اكمل وحياتي ملهاش لازمه", user_id="test_user")
    assert out["mode"] == "crisis"
    assert "analysis" in out
    assert "response" in out
    assert out["analysis"]["crisis_flag"] is True
