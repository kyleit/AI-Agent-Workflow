from devteam.domain.handoff.seat_state import SeatState


def test_render_contains_all_headings_and_next_step():
    st = SeatState(slug="ipc", updated="T", session_id="S1", next_step_now="do the thing")
    text = st.render()
    assert "# Seat ipc — Living State" in text
    assert "## BƯỚC TIẾP THEO NGAY" in text
    assert "do the thing" in text
    # every heading present
    for _attr, heading in SeatState.headings():
        assert f"## {heading}" in text
