from types import SimpleNamespace

from pyfireca import cli


def test_validate_command_calls_model_aware_validation(monkeypatch, capsys) -> None:
    marker = object()
    calls = []
    monkeypatch.setattr(cli, "load_run_config", lambda path: marker)
    monkeypatch.setattr(cli, "validate_run_config", lambda config: calls.append(config))

    status = cli.main(["validate", "example.yml"])

    assert status == 0
    assert calls == [marker]
    assert "Valid PyFireCA configuration" in capsys.readouterr().out


def test_run_command_reports_output_and_summary(monkeypatch, capsys, tmp_path) -> None:
    marker = object()
    result = SimpleNamespace(
        summary_metrics=lambda: {
            "burned_cell_count": 12,
            "burned_area_m2": 10800.0,
            "last_arrival_s": 345.5,
        }
    )
    artifacts = SimpleNamespace(directory=tmp_path / "run")
    monkeypatch.setattr(cli, "load_run_config", lambda path: marker)
    monkeypatch.setattr(cli, "run_config", lambda config: (result, artifacts))

    status = cli.main(["run", "example.yml"])

    output = capsys.readouterr().out
    assert status == 0
    assert "PyFireCA run complete" in output
    assert "Burned cells: 12" in output
    assert "Burned area: 10800.000 m^2" in output
    assert "Last arrival: 345.500 s" in output


def test_cli_converts_runtime_failure_to_nonzero_status(monkeypatch, capsys) -> None:
    def fail(path):
        raise ValueError("bad config")

    monkeypatch.setattr(cli, "load_run_config", fail)

    status = cli.main(["validate", "broken.yml"])

    assert status == 2
    assert "pyfireca: error: bad config" in capsys.readouterr().err
