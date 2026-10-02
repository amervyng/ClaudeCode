"""
Script to migrate CSV data from the fetchAPI directory to the migrate data directory.

Migrates the latest fetched data from .claude/skills/fetchAPI/data to a target location
and provides migration status and logging.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path


FETCH_DATA_DIR = Path("./.claude/skills/fetchAPI/data")
MIGRATE_DATA_DIR = Path("./.claude/skills/migrate/data")
MIGRATE_LOGS_DIR = Path("./.claude/skills/migrate/logs")


def setup_logging(log_dir: Path) -> logging.Logger:
    """
    Setup logging configuration for migration process.

    Args:
        log_dir: Directory where log file will be stored

    Returns:
        Configured logger instance
    """
    log_file = log_dir / "migrate.log"

    logger = logging.getLogger("migrate")
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers = []

    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def get_latest_fetch_folder() -> Path | None:
    """
    Get the latest folder from the fetchAPI data directory.

    Returns:
        Path to the latest folder or None if no folders exist
    """
    if not FETCH_DATA_DIR.exists():
        return None

    folders = [d for d in FETCH_DATA_DIR.iterdir() if d.is_dir()]

    if not folders:
        return None

    latest_folder = max(folders, key=lambda x: x.name)
    return latest_folder


def migrate_data(source_dir: Path, dest_dir: Path, logger: logging.Logger) -> dict:
    """
    Migrate CSV files from source to destination directory.

    Args:
        source_dir: Source directory containing CSV files
        dest_dir: Destination directory for migrated files
        logger: Logger instance

    Returns:
        Dictionary with migration results
    """
    results = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "files": [],
    }

    if not source_dir.exists():
        logger.error(f"Source directory does not exist: {source_dir}")
        return results

    csv_files = list(source_dir.glob("*.csv"))
    results["total"] = len(csv_files)

    if not csv_files:
        logger.warning(f"No CSV files found in {source_dir}")
        return results

    dest_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Migrating {len(csv_files)} CSV files from {source_dir} to {dest_dir}")

    for csv_file in csv_files:
        try:
            dest_file = dest_dir / csv_file.name
            shutil.copy2(csv_file, dest_file)
            results["successful"] += 1
            results["files"].append({
                "filename": csv_file.name,
                "size": csv_file.stat().st_size,
                "status": "success",
            })
            logger.info(f"✓ Migrated: {csv_file.name} ({csv_file.stat().st_size} bytes)")
        except Exception as e:
            results["failed"] += 1
            results["files"].append({
                "filename": csv_file.name,
                "error": str(e),
                "status": "failed",
            })
            logger.error(f"✗ Failed to migrate {csv_file.name}: {str(e)}")

    return results


def log_summary(results: dict, source_dir: Path, dest_dir: Path, logger: logging.Logger) -> None:
    """
    Log summary of migration operation.

    Args:
        results: Results from migrate_data
        source_dir: Source directory path
        dest_dir: Destination directory path
        logger: Logger instance
    """
    logger.info("=" * 70)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Source: {source_dir}")
    logger.info(f"Destination: {dest_dir}")
    logger.info(f"Total files: {results['total']}")
    logger.info(f"Successfully migrated: {results['successful']}")
    logger.info(f"Failed: {results['failed']}")

    if results["files"]:
        logger.info("\nMigrated files:")
        for file_info in results["files"]:
            if file_info["status"] == "success":
                logger.info(f"  ✓ {file_info['filename']} ({file_info['size']} bytes)")
            else:
                logger.info(f"  ✗ {file_info['filename']}: {file_info['error']}")

    logger.info("=" * 70)


def main():
    """Main function to orchestrate the data migration process."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Setup logging
    MIGRATE_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_dir = MIGRATE_LOGS_DIR / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_dir)

    logger.info("=" * 70)
    logger.info("DATA MIGRATION PROCESS STARTED")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {timestamp}")

    # Get latest fetch folder
    latest_folder = get_latest_fetch_folder()

    if latest_folder is None:
        logger.error("No fetch data found. Please run the fetchAPI script first.")
        print("Error: No fetch data found. Please run the fetchAPI script first.")
        return

    logger.info(f"Latest fetch folder: {latest_folder.name}")

    # Migrate data
    dest_dir = MIGRATE_DATA_DIR / latest_folder.name
    results = migrate_data(latest_folder, dest_dir, logger)

    # Log summary
    log_summary(results, latest_folder, dest_dir, logger)

    print(f"Migration completed!")
    print(f"Migrated {results['successful']} files to: {dest_dir}")
    print(f"Logs saved to: {log_dir / 'migrate.log'}")

    if results["failed"] > 0:
        print(f"Warning: {results['failed']} file(s) failed to migrate")


if __name__ == "__main__":
    main()