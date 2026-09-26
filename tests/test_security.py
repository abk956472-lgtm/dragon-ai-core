from dragon_core.security import SecurityController
import policies.security_policy as sp


def test_security_controller():
    sec = SecurityController()
    assert sec.is_allowed("file_read") is True

    # Kill switch test
    sec.set_kill_switch(True)
    assert sec.is_kill_switch_active() is True
    assert sec.is_allowed("file_read") is False

    # Restore kill switch
    sec.set_kill_switch(False)
    assert sec.is_allowed("file_read") is True


def test_security_policy():
    rules = sp.get_security_rules()
    assert len(rules) > 0
    risk = sp.evaluate_security_risk("delete", "file_delete")
    assert risk["risk_level"] == "high"
