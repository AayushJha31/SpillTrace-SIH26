from __future__ import annotations

from data.scoring.candidate_cli import print_scoring_docs, print_health_status


def test_candidate_cli_functions_run_without_errors(capsys) -> None:
    print_scoring_docs()
    captured = capsys.readouterr()
    assert "# Candidate scoring model" in captured.out

    print_health_status()
    captured = capsys.readouterr()
    assert "Status:" in captured.out
    assert "healthy" in captured.out