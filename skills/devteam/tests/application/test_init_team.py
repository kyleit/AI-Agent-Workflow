import json
import os

import pytest

from devteam.domain.errors import DevTeamError, ErrorCode


def test_preview_does_not_write(container, root):
    res = container.init.execute(apply=False)
    assert res.applied is False
    assert not os.path.exists(os.path.join(root, ".agents", "devteam", "seats.json"))
    slugs = [s["slug"] for s in res.roster["seats"]]
    assert "leader" in slugs and "src" in slugs and "app" in slugs


def test_apply_writes_all_artifacts(container, root):
    res = container.init.execute(apply=True)
    assert res.applied is True
    dev = os.path.join(root, ".agents", "devteam")
    assert os.path.exists(os.path.join(dev, "seats.json"))
    assert os.path.exists(os.path.join(dev, "BOARD.md"))
    # relative paths only in files_written (§22)
    for p in res.files_written:
        assert not os.path.isabs(p)
        assert ".." not in p


def test_apply_twice_refuses(container):
    container.init.execute(apply=True)
    with pytest.raises(DevTeamError) as e:
        container.init.execute(apply=True)
    assert e.value.code == ErrorCode.ALREADY_INITIALIZED


def test_seats_json_is_valid_json(team, root):
    data = json.loads(open(os.path.join(root, ".agents", "devteam", "seats.json"), encoding="utf-8").read())
    assert data["version"] == 1 and len(data["seats"]) >= 2
