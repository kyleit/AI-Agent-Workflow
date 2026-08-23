import pytest

from devteam.application.dto import SendMailRequest
from devteam.domain.errors import DevTeamError, ErrorCode


def test_send_appends_and_assigns_id_ts(team):
    env = team.send.execute(SendMailRequest(to="app", type="task", payload={"title": "x"}))
    assert env.to == "app" and env.id and env.ts
    got = team.poll.execute("app")
    assert len(got) == 1 and got[0].title == "x"


def test_send_unknown_seat(team):
    with pytest.raises(DevTeamError) as e:
        team.send.execute(SendMailRequest(to="ghost", type="task", payload={}))
    assert e.value.code == ErrorCode.UNKNOWN_SEAT


def test_send_before_init(container):
    with pytest.raises(DevTeamError) as e:
        container.send.execute(SendMailRequest(to="app", type="task", payload={}))
    assert e.value.code == ErrorCode.NOT_INITIALIZED
