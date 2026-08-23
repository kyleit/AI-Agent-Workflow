from workflow_runtime.__main__ import main


def test_cli_cleanup_dry_run(tmp_path, monkeypatch, capsys):
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path)

    exit_code = main(["cleanup", "--dry-run"])

    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Docs cleanup finished" in captured.out
