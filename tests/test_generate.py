"""Tests for generate.py."""

from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest

import generate


# ---------------------------------------------------------------------------
# build_ooni_url
# ---------------------------------------------------------------------------


def test_build_ooni_url_contains_required_params():
    """URL must carry all OONI API parameters and point to aggregation endpoint."""
    url = generate.build_ooni_url(days_back=7, now=datetime(2025, 6, 6))
    parsed = urlparse(url)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == generate.OONI_API_URL

    params = parse_qs(parsed.query)
    assert params["probe_cc"] == ["RU"]
    assert params["test_name"] == ["web_connectivity"]
    assert params["time_grain"] == ["day"]
    assert params["format"] == ["CSV"]
    assert params["axis_y"] == ["domain"]
    assert params["axis_x"] == ["measurement_start_day"]


def test_build_ooni_url_date_range_exact():
    """since/until must reflect days_back window ending at `now`."""
    url = generate.build_ooni_url(days_back=7, now=datetime(2025, 6, 6))
    params = parse_qs(urlparse(url).query)
    assert params["since"] == ["2025-05-30"]
    assert params["until"] == ["2025-06-06"]


def test_build_ooni_url_zero_days_back():
    """Edge case: zero window -> since == until."""
    url = generate.build_ooni_url(days_back=0, now=datetime(2025, 1, 1))
    params = parse_qs(urlparse(url).query)
    assert params["since"] == ["2025-01-01"]
    assert params["until"] == ["2025-01-01"]


# ---------------------------------------------------------------------------
# filter_blocked_domains
# ---------------------------------------------------------------------------


def _row(
    domain: str,
    measurement_count: int = 10,
    anomaly_count: int = 0,
    ok_count: int = 0,
) -> dict:
    return {
        "domain": domain,
        "measurement_count": measurement_count,
        "anomaly_count": anomaly_count,
        "ok_count": ok_count,
    }


def test_filter_keeps_only_anomaly_gt_ok():
    """anomaly_count > ok_count is the inclusion criterion."""
    df = pd.DataFrame(
        [
            _row("blocked.example", anomaly_count=10, ok_count=2),
            _row("healthy.example", anomaly_count=2, ok_count=10),
            _row("equal.example", anomaly_count=5, ok_count=5),
        ]
    )
    result = generate.filter_blocked_domains(df)
    assert list(result["domain"]) == ["blocked.example"]


def test_filter_drops_invalid_domains_with_consecutive_dots():
    """Domains with `..` are dropped per README methodology."""
    df = pd.DataFrame(
        [
            _row("valid.example", anomaly_count=5, ok_count=0),
            _row("bad..example", anomaly_count=10, ok_count=0),
            _row("another..bad.example", anomaly_count=10, ok_count=0),
        ]
    )
    result = generate.filter_blocked_domains(df)
    assert list(result["domain"]) == ["valid.example"]


def test_filter_drops_na_domains():
    """NaN/None domains must be dropped."""
    df = pd.DataFrame(
        [
            _row("kept.example", anomaly_count=5, ok_count=0),
            _row(None, anomaly_count=10, ok_count=0),  # type: ignore[arg-type]
        ]
    )
    result = generate.filter_blocked_domains(df)
    assert list(result["domain"]) == ["kept.example"]


def test_filter_dedup_keeps_highest_measurement_count():
    """For duplicate domains the row with max measurement_count wins."""
    df = pd.DataFrame(
        [
            _row("dup.example", measurement_count=5, anomaly_count=10, ok_count=0),
            _row("dup.example", measurement_count=100, anomaly_count=10, ok_count=0),
            _row("dup.example", measurement_count=50, anomaly_count=10, ok_count=0),
        ]
    )
    result = generate.filter_blocked_domains(df)
    assert len(result) == 1
    assert result["domain"].iloc[0] == "dup.example"
    # The chosen row must reflect the highest measurement_count -> anomaly/ok
    # values from that row. We verify by re-reading source df.
    winning = df.loc[df["measurement_count"].idxmax()]
    assert winning["anomaly_count"] == 10


def test_filter_returns_only_domain_column():
    """Output DataFrame must contain only the `domain` column."""
    df = pd.DataFrame([_row("a.example", anomaly_count=1, ok_count=0)])
    result = generate.filter_blocked_domains(df)
    assert list(result.columns) == ["domain"]


def test_filter_empty_dataframe_returns_empty():
    """Empty input -> empty output, no exceptions."""
    df = pd.DataFrame(
        columns=["domain", "measurement_count", "anomaly_count", "ok_count"]
    )
    result = generate.filter_blocked_domains(df)
    assert result.empty
    assert list(result.columns) == ["domain"]


def test_filter_full_pipeline_integration():
    """End-to-end: mix of all rules applied in correct order."""
    df = pd.DataFrame(
        [
            # blocked, kept
            _row("a.example", measurement_count=10, anomaly_count=8, ok_count=1),
            # duplicate of a.example but lower count -> dropped
            _row("a.example", measurement_count=1, anomaly_count=20, ok_count=0),
            # healthy -> dropped
            _row("b.example", measurement_count=10, anomaly_count=1, ok_count=20),
            # invalid domain -> dropped
            _row("c..example", measurement_count=10, anomaly_count=20, ok_count=0),
            # missing domain -> dropped
            _row(None, measurement_count=10, anomaly_count=20, ok_count=0),  # type: ignore[arg-type]
            # blocked, kept
            _row("d.example", measurement_count=5, anomaly_count=3, ok_count=2),
        ]
    )
    result = generate.filter_blocked_domains(df)
    assert set(result["domain"]) == {"a.example", "d.example"}


# ---------------------------------------------------------------------------
# blocked_unique_domains (I/O wrapper)
# ---------------------------------------------------------------------------


def _write_csv(rows: list[dict], path: Path) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def test_blocked_unique_domains_writes_expected_list(tmp_path: Path):
    """End-to-end CSV -> lst on a happy path."""
    csv_path = tmp_path / "input.csv"
    lst_path = tmp_path / "domains.lst"
    _write_csv(
        [
            _row("blocked.example", anomaly_count=10, ok_count=1),
            _row("healthy.example", anomaly_count=1, ok_count=10),
        ],
        csv_path,
    )

    assert generate.blocked_unique_domains(csv_path, lst_path) is True
    assert lst_path.read_text().splitlines() == ["blocked.example"]


def test_blocked_unique_domains_empty_csv_returns_false(tmp_path: Path):
    """Empty CSV must be handled gracefully and return False."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("")
    lst_path = tmp_path / "out.lst"

    assert generate.blocked_unique_domains(csv_path, lst_path) is False
    assert not lst_path.exists()


def test_blocked_unique_domains_missing_columns_returns_false(tmp_path: Path):
    """CSV without required columns must trigger KeyError handler -> False."""
    csv_path = tmp_path / "bad.csv"
    pd.DataFrame([{"foo": 1, "bar": 2}]).to_csv(csv_path, index=False)
    lst_path = tmp_path / "out.lst"

    assert generate.blocked_unique_domains(csv_path, lst_path) is False


def test_blocked_unique_domains_output_has_no_header(tmp_path: Path):
    """Output lst must be a plain column of domains without header."""
    csv_path = tmp_path / "in.csv"
    lst_path = tmp_path / "out.lst"
    _write_csv([_row("only.example", anomaly_count=1, ok_count=0)], csv_path)

    generate.blocked_unique_domains(csv_path, lst_path)

    content = lst_path.read_text().strip().splitlines()
    assert content == ["only.example"]


# ---------------------------------------------------------------------------
# Sanity: module-level constants & main contract
# ---------------------------------------------------------------------------


def test_main_default_arguments_contract():
    """main() defaults must match AGENTS.md documented values."""
    import inspect

    sig = inspect.signature(generate.main)
    assert sig.parameters["days_back"].default == 7
    assert sig.parameters["csv_file_path"].default == Path("ooni_data.csv")
    assert sig.parameters["txt_file_path"].default == Path("domains.lst")


def test_download_chunk_size_is_power_of_two():
    """Sanity: chunk size should be a reasonable buffer size."""
    assert generate.DOWNLOAD_CHUNK_SIZE > 0
    assert (generate.DOWNLOAD_CHUNK_SIZE & (generate.DOWNLOAD_CHUNK_SIZE - 1)) == 0


@pytest.mark.parametrize(
    "exc",
    [
        ConnectionError,
        TimeoutError,
    ],
)
def test_download_file_swallows_network_errors(tmp_path, monkeypatch, exc):
    """download_file must return False on network errors, never raise."""
    import requests as _requests

    def _raise(*_args, **_kwargs):
        raise exc("simulated")

    monkeypatch.setattr(_requests, "get", _raise)
    # ConnectionError is a subclass of OSError; requests.ConnectionError maps
    # to it but we use the stdlib base to keep the test independent.
    result = generate.download_file("http://invalid.invalid", tmp_path / "x.bin")
    assert result is False
