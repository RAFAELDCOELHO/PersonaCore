"""CSV logger unit tests: append-only, header-once, survives a restart.

The offline CSV logger (no wandb — zero-budget/offline intent) must survive Kaggle session
restarts: re-opening on the same path appends without re-writing the header.
"""

import csv

from personacore.logging import CSVLogger


def _read_rows(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def test_csv_logger_appends(tmp_path):
    # Two logged rows -> one header line + two data rows.
    path = tmp_path / "log.csv"
    logger = CSVLogger(path, fieldnames=["step", "loss"])
    logger.log(step=1, loss=0.5)
    logger.log(step=2, loss=0.4)
    logger.close()

    rows = _read_rows(path)
    assert rows[0] == ["step", "loss"]
    assert len(rows) == 3  # header + 2 data rows
    assert rows[1] == ["1", "0.5"]
    assert rows[2] == ["2", "0.4"]


def test_csv_logger_survives_restart(tmp_path):
    # Log, close, re-open a NEW logger on the same path, log again:
    # header appears exactly once and both rows persist (Kaggle restart survivability).
    path = tmp_path / "log.csv"

    first = CSVLogger(path, fieldnames=["step", "loss"])
    first.log(step=1, loss=0.5)
    first.close()

    second = CSVLogger(path, fieldnames=["step", "loss"])
    second.log(step=2, loss=0.4)
    second.close()

    rows = _read_rows(path)
    assert rows[0] == ["step", "loss"]
    assert rows.count(["step", "loss"]) == 1  # header written ONCE across the restart
    assert len(rows) == 3
    assert rows[1] == ["1", "0.5"]
    assert rows[2] == ["2", "0.4"]
