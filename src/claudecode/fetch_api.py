"""Fetch DBT masterclass CSV datasets concurrently and persist them to disk.

Each run writes the downloaded CSVs into a timestamped directory under
``.claude/skills/fetchAPI/data/`` and a matching log file under
``.claude/skills/fetchAPI/logs/``.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx

BASE_URL = (
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/"
    "refs/heads/main/DBT_Masterclass"
)

API_URLS: tuple[str, ...] = (
    f"{BASE_URL}/dim_customer.csv",
    f"{BASE_URL}/dim_store.csv",
    f"{BASE_URL}/dim_date.csv",
    f"{BASE_URL}/dim_product.csv",
    f"{BASE_URL}/fact_sales.csv",
    f"{BASE_URL}/fact_returns.csv",
)

SKILL_ROOT = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "fetchAPI"
DATA_ROOT = SKILL_ROOT / "data"
LOG_ROOT = SKILL_ROOT / "logs"

TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
REQUEST_TIMEOUT = 30.0


@dataclass(frozen=True)
class FetchResult:
    """Outcome of a single API call."""

    url: str
    ok: bool
    path: Path | None = None
    bytes_written: int = 0
    error: str | None = None


def configure_logging(log_dir: Path) -> logging.Logger:
    """Attach a file and console handler to a run-scoped logger.

    Args:
        log_dir: Directory that will hold ``fetchAPI.log``.

    Returns:
        The configured logger.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("fetchAPI")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_dir / "fetchAPI.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


async def fetch_one(
    client: httpx.AsyncClient,
    url: str,
    data_dir: Path,
    logger: logging.Logger,
) -> FetchResult:
    """Download one CSV and write it into ``data_dir``.

    Args:
        client: Shared async HTTP client.
        url: CSV endpoint to call.
        data_dir: Destination directory for the downloaded file.
        logger: Logger used to record the call outcome.

    Returns:
        A :class:`FetchResult` describing success or failure.
    """
    filename = url.rsplit("/", 1)[-1]
    logger.info("CALL     | %s", url)
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = f"HTTP {exc.response.status_code} {exc.response.reason_phrase}"
        logger.error("FAILED   | %s | %s", url, message)
        return FetchResult(url=url, ok=False, error=message)
    except httpx.HTTPError as exc:
        message = f"{type(exc).__name__}: {exc}"
        logger.error("FAILED   | %s | %s", url, message)
        return FetchResult(url=url, ok=False, error=message)

    destination = data_dir / filename
    payload = response.content
    destination.write_bytes(payload)
    logger.info(
        "SUCCESS  | %s | %s | %d bytes",
        url,
        destination.name,
        len(payload),
    )
    return FetchResult(
        url=url,
        ok=True,
        path=destination,
        bytes_written=len(payload),
    )


async def fetch_all(
    urls: tuple[str, ...],
    data_dir: Path,
    logger: logging.Logger,
) -> list[FetchResult]:
    """Fetch every URL concurrently.

    Args:
        urls: CSV endpoints to call.
        data_dir: Destination directory for the downloaded files.
        logger: Logger used to record call outcomes.

    Returns:
        One :class:`FetchResult` per URL, in the order given.
    """
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT, follow_redirects=True
    ) as client:
        tasks = [fetch_one(client, url, data_dir, logger) for url in urls]
        return list(await asyncio.gather(*tasks))


async def main() -> int:
    """Run one fetch cycle and report the outcome.

    Returns:
        ``0`` if every call succeeded, otherwise the number of failures.
    """
    run_stamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    data_dir = DATA_ROOT / run_stamp
    log_dir = LOG_ROOT / run_stamp
    data_dir.mkdir(parents=True, exist_ok=True)

    logger = configure_logging(log_dir)
    logger.info("Run started  | %d endpoint(s)", len(API_URLS))
    logger.info("Data dir     | %s", data_dir)
    logger.info("Log dir      | %s", log_dir)

    results = await fetch_all(API_URLS, data_dir, logger)

    succeeded = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]

    logger.info(
        "Run finished | %d succeeded, %d failed, %d bytes written",
        len(succeeded),
        len(failed),
        sum(r.bytes_written for r in succeeded),
    )
    for result in failed:
        logger.warning("Unresolved   | %s | %s", result.url, result.error)

    return len(failed)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
