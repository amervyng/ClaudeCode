"""Fetch dimension and fact CSV datasets from remote endpoints.

Downloads a fixed set of CSV files concurrently with ``httpx``, writes each
response body to a timestamped data directory, and records the outcome of every
call in a timestamped log file.

Run with the project virtual environment::

    .venv/Scripts/python.exe .claude/skills/fetchAPI/fetch_api.py
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

import httpx

SKILL_DIR: Final[Path] = Path(__file__).resolve().parent
DATA_ROOT: Final[Path] = SKILL_DIR / "data"
LOG_ROOT: Final[Path] = SKILL_DIR / "logs"
LOG_FILE_NAME: Final[str] = "fetchAPI.log"
TIMESTAMP_FORMAT: Final[str] = "%Y-%m-%d_%H-%M-%S"
REQUEST_TIMEOUT: Final[float] = 30.0

API_URLS: Final[tuple[str, ...]] = (
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/dim_customer.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/dim_store.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/dim_date.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/dim_product.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/fact_sales.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/fact_returns.csv",
)


@dataclass(frozen=True)
class FetchResult:
    """Outcome of a single API call.

    Attributes:
        url: The endpoint that was requested.
        success: Whether the payload was fetched and saved.
        file_path: Destination file, or ``None`` when the call failed.
        status_code: HTTP status code, or ``None`` when no response arrived.
        bytes_written: Number of bytes saved to disk.
        error: Error description, or ``None`` on success.
    """

    url: str
    success: bool
    file_path: Path | None = None
    status_code: int | None = None
    bytes_written: int = 0
    error: str | None = None


def configure_logging(log_dir: Path) -> logging.Logger:
    """Create a logger that writes to ``log_dir/fetchAPI.log`` and stdout.

    Args:
        log_dir: Directory that will hold the log file. Created if missing.

    Returns:
        The configured logger.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("fetchAPI")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(
        log_dir / LOG_FILE_NAME, mode="w", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def file_name_from_url(url: str) -> str:
    """Return the CSV file name encoded in an endpoint URL.

    Args:
        url: Endpoint URL ending in a file name.

    Returns:
        The trailing path segment of the URL.
    """
    return url.rsplit("/", maxsplit=1)[-1]


async def fetch_and_save(
    client: httpx.AsyncClient,
    url: str,
    data_dir: Path,
    logger: logging.Logger,
) -> FetchResult:
    """Fetch one endpoint and write its body into ``data_dir``.

    Args:
        client: Shared async HTTP client.
        url: Endpoint to request.
        data_dir: Directory the CSV file is written to.
        logger: Logger used to record the call outcome.

    Returns:
        A :class:`FetchResult` describing the call.
    """
    file_name = file_name_from_url(url)
    logger.info("CALL    | requesting %s", url)
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.error("FAILURE | %s | HTTP %s %s", url, status, exc.response.reason_phrase)
        return FetchResult(url=url, success=False, status_code=status, error=f"HTTP {status}")
    except httpx.HTTPError as exc:
        logger.error("FAILURE | %s | %s: %s", url, type(exc).__name__, exc)
        return FetchResult(
            url=url, success=False, error=f"{type(exc).__name__}: {exc}"
        )

    destination = data_dir / file_name
    try:
        destination.write_bytes(response.content)
    except OSError as exc:
        logger.error("FAILURE | %s | write error: %s", url, exc)
        return FetchResult(
            url=url,
            success=False,
            status_code=response.status_code,
            error=f"OSError: {exc}",
        )

    logger.info(
        "SUCCESS | %s | HTTP %s | %s bytes -> %s",
        url,
        response.status_code,
        len(response.content),
        destination,
    )
    return FetchResult(
        url=url,
        success=True,
        file_path=destination,
        status_code=response.status_code,
        bytes_written=len(response.content),
    )


async def fetch_all(
    urls: tuple[str, ...], data_dir: Path, logger: logging.Logger
) -> tuple[FetchResult, ...]:
    """Fetch every endpoint concurrently.

    Args:
        urls: Endpoints to request.
        data_dir: Directory the CSV files are written to.
        logger: Logger used to record call outcomes.

    Returns:
        One :class:`FetchResult` per URL, in input order.
    """
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT, follow_redirects=True
    ) as client:
        tasks = [fetch_and_save(client, url, data_dir, logger) for url in urls]
        return tuple(await asyncio.gather(*tasks))


def log_summary(results: tuple[FetchResult, ...], logger: logging.Logger) -> None:
    """Write an aggregate report of all calls to the log.

    Args:
        results: Outcomes of every API call.
        logger: Logger used to record the summary.
    """
    successes = [result for result in results if result.success]
    failures = [result for result in results if not result.success]

    logger.info("-" * 72)
    logger.info(
        "SUMMARY | total=%s successful=%s failed=%s total_bytes=%s",
        len(results),
        len(successes),
        len(failures),
        sum(result.bytes_written for result in successes),
    )
    for result in successes:
        logger.info("SUMMARY | OK     | %s", file_name_from_url(result.url))
    for result in failures:
        logger.warning(
            "SUMMARY | FAILED | %s | %s", file_name_from_url(result.url), result.error
        )


def main() -> int:
    """Run the fetch pipeline.

    Returns:
        ``0`` when every call succeeded, otherwise the number of failures.
    """
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    data_dir = DATA_ROOT / timestamp
    log_dir = LOG_ROOT / timestamp

    logger = configure_logging(log_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Run started at %s", timestamp)
    logger.info("Data directory: %s", data_dir)
    logger.info("Log directory:  %s", log_dir)
    logger.info("Endpoints queued: %s", len(API_URLS))

    results = asyncio.run(fetch_all(API_URLS, data_dir, logger))
    log_summary(results, logger)

    failures = sum(1 for result in results if not result.success)
    logger.info("Run finished with %s failure(s)", failures)
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
