from workflow_runtime.domain.models.snapshot_aggregate import SnapshotAggregate


def test_tc301_domain_ring_buffer_trim():
    """TC-301-PY: Assert SnapshotAggregate trims snapshots to exactly 50 when 55 snapshots are added."""
    session_id = "test_session_ring_buffer"
    aggregate = SnapshotAggregate(session_id=session_id, max_snapshots=50)

    for i in range(1, 56):
        snap_id = f"snap_{i}"
        ast_json = f'{{"version": {i}}}'
        state_payload = {"step": i, "data": f"value_{i}"}
        snapshot = aggregate.add_snapshot(
            snapshot_id=snap_id,
            ast_schema_json=ast_json,
            state_payload=state_payload,
            reason="test_trim"
        )
        assert snapshot.snapshot_id == snap_id

    snapshots = aggregate.get_all_snapshots()
    assert len(snapshots) == 50
    assert snapshots[0].snapshot_id == "snap_6"
    assert snapshots[-1].snapshot_id == "snap_55"
    assert aggregate.get_latest().snapshot_id == "snap_55"
    assert aggregate.get_by_id("snap_1") is None
    assert aggregate.get_by_id("snap_6") is not None
