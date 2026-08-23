from devteam.application.dto import SendMailRequest


def test_enter_returns_charter_and_git(team):
    res = team.enter.execute("app", session_id="S1")
    assert "Charter — Seat app" in res.charter
    assert isinstance(res.new_mail, list)


def test_enter_preview_does_not_consume(team):
    team.send.execute(SendMailRequest(to="app", type="msg", payload={"body": "x"}))
    res = team.enter.execute("app")
    assert len(res.new_mail) == 1
    # still deliverable on a real poll
    assert len(team.poll.execute("app")) == 1


def test_enter_resumes_next_step(team):
    team.leave.execute("app", {"next_step_now": "resume here"}, session_id="S1")
    res = team.enter.execute("app", session_id="S2")
    assert res.next_step_now == "resume here"
