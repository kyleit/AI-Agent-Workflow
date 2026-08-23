from devteam.application.dto import SendMailRequest


def test_poll_advances_exactly_once(team):
    for i in range(3):
        team.send.execute(SendMailRequest(to="app", type="msg", payload={"body": str(i)}))
    first = team.poll.execute("app")
    assert [e.body for e in first] == ["0", "1", "2"]
    second = team.poll.execute("app")
    assert second == []


def test_poll_no_advance_is_preview(team):
    team.send.execute(SendMailRequest(to="app", type="msg", payload={"body": "keep"}))
    preview = team.poll.execute("app", advance=False)
    assert len(preview) == 1
    # still unread
    assert len(team.poll.execute("app")) == 1


def test_incremental_delivery(team):
    team.send.execute(SendMailRequest(to="app", type="msg", payload={"body": "a"}))
    assert len(team.poll.execute("app")) == 1
    team.send.execute(SendMailRequest(to="app", type="msg", payload={"body": "b"}))
    got = team.poll.execute("app")
    assert [e.body for e in got] == ["b"]
