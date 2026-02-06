"""
Data loading utilities for TravelAssist.

Handles dataset upload, extraction, initialization, and attraction data
preprocessing (CSV load, embedding generation, geocoding).
"""

import os
import random
import re
import shutil
from pathlib import Path
from typing import List, Optional

import pandas as pd
import streamlit as st
from pyobvector import ST_GeomFromText
from sqlalchemy import text
from tqdm import tqdm

from ..common import geocode, parse_season_str
from ..common.compress import extract_archive
from ..common.config import get_config
from ..common.constants import CITYDATA_DIR, UPLOADED_DIR, ERROR_DIR
from ..common.database import create_db_client, create_table
from ..common.logger import setup_logger
from ..llm.embedding import embedding

logger = setup_logger(__name__)


def check_data_initialized() -> tuple[bool, int]:
    """
    Check if data is initialized in database.

    Returns:
        tuple[bool, int]: (is_initialized, record_count)
    """
    logger.debug("Checking if data is initialized in database")
    try:
        client = create_db_client()
        table_name = get_config().default_table_name

        if not client.check_table_exists(table_name=table_name):
            logger.info("Table %s does not exist, data not initialized", table_name)
            return False, 0

        with client.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) as cnt FROM `{table_name}`")
            )
            row = result.fetchone()
            count = row[0] if row else 0

        logger.info("Data check complete: table=%s, record_count=%d", table_name, count)
        return count > 0, count
    except Exception as e:
        logger.exception("Database connection error when checking data: %s", e)
        st.error(f"Database connection error: {str(e)}")
        return False, 0


def save_uploaded_file(uploaded_file, upload_dir: Path) -> Path:
    """
    Save uploaded file to disk.

    Args:
        uploaded_file: Streamlit UploadedFile object
        upload_dir: Directory to save the file

    Returns:
        Path: Path to the saved file, or None if uploaded_file is None
    """
    if uploaded_file is None:
        logger.debug("No uploaded file provided, skipping save")
        return None

    file_path = upload_dir / uploaded_file.name

    # Skip if already exists
    if file_path.exists():
        logger.info("File already exists, skipping save: %s", file_path)
        return file_path

    # Write file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    logger.info("Saved uploaded file to %s", file_path)
    return file_path


def load_csv(
    csv_path: str,
    table_name: Optional[str] = None,
) -> None:
    """
    Load attraction data from a CSV file into the database.

    Expected CSV columns:
    - 名字: Attraction name
    - 地址: Address text (contains geocodable address)
    - 介绍: Introduction/description
    - 图片链接: Image URL
    - 建议季节: Recommended seasons
    - 门票: Ticket information

    After loading, the CSV file is moved to UPLOADED_DIR.

    Args:
        csv_path: Path to the CSV file.
        table_name: Target table name.
    """
    if table_name is None:
        table_name = get_config().default_table_name
    client = create_db_client()
    df = pd.read_csv(csv_path)

    # Pattern to extract address from formatted text
    address_pattern = r"地址:\n(.*?)\n"
    
    failed = False

    for _, record in tqdm(df.iterrows(), total=df.shape[0], desc=f"Loading {csv_path}"):
        # Skip records with missing required fields
        if pd.isna(record["介绍"]) or pd.isna(record["图片链接"]):
            continue

        # Parse season string
        season_str = "四季皆宜" if pd.isna(record["建议季节"]) else record["建议季节"]

        # Extract address
        address_match = re.search(address_pattern, str(record["地址"]), re.DOTALL)
        if not address_match:
            continue

        address_str = address_match.group(1)

        # Geocode the address
        try:
            lat_long = geocode(address_str)
        except Exception as e:
            logger.warning("Geocoding failed for %s: %s", address_str, e)
            failed = True
            break

        # Prepare record data
        data = {
            "attraction_name": record["名字"],
            "address_text": record["地址"],
            "address": ST_GeomFromText(lat_long, 4326),
            "intro": record["介绍"],
            "intro_vec": embedding([record["介绍"]])[0],
            "img_url": record["图片链接"],
            "score": random.randint(95, 100),
            "season": parse_season_str(season_str),
            "ticket": None if pd.isna(record["门票"]) else record["门票"],
        }

        try:
            client.upsert(table_name=table_name, data=data)
        except Exception as e:
            logger.warning("Failed to insert into database: %s", e)
            failed = True
            break

    if failed == False:
        # Move CSV to UPLOADED_DIR after loading
        UPLOADED_DIR.mkdir(parents=True, exist_ok=True)
        dest_path = UPLOADED_DIR / Path(csv_path).name
        shutil.move(csv_path, dest_path)
        logger.info("Moved %s to %s", csv_path, dest_path)
    else:
        # Move CSV to ERROR_DIR after loading
        ERROR_DIR.mkdir(parents=True, exist_ok=True)
        dest_path = ERROR_DIR / Path(csv_path).name
        shutil.move(csv_path, dest_path)
        logger.info("Moved %s to %s", csv_path, dest_path)

    


def load_directory(
    directory_path: str,
    table_name: Optional[str] = None,
) -> None:
    """
    Load all CSV files from a directory into the database.

    Args:
        directory_path: Path to directory containing CSV files.
        table_name: Target table name.
    """
    if table_name is None:
        table_name = get_config().default_table_name
    for root, _, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(".csv"):
                file_path = os.path.join(root, filename)
                logger.info("Processing %s", file_path)
                load_csv(csv_path=file_path, table_name=table_name)


def load_dataset_from_archive(archive_path: Path, citydata_dir: Path) -> bool:
    """
    Load dataset from archive file.

    Steps:
    1. Clean citydata directory
    2. Extract archive directly to citydata
    3. Load data with progress tracking

    Args:
        archive_path: Path to the archive file
        citydata_dir: Directory for citydata

    Returns:
        bool: True if successful, False otherwise
    """

    logger.info("Loading dataset from archive: %s -> %s", archive_path, citydata_dir)

    # Clean citydata directory
    if citydata_dir.exists():
        logger.info("citydata directory: %s already exists", citydata_dir)
    else:
        logger.info("Creating citydata directory: %s", citydata_dir)
        citydata_dir.mkdir(exist_ok=True)
    
    # Extract archive
    with st.spinner("Extracting archive..."):
        if not extract_archive(str(archive_path), str(citydata_dir)):
            logger.error("Failed to extract archive: %s", archive_path)
            st.error("Failed to extract archive")
            return False
    logger.info("Archive extracted successfully")

    # Find CSV files
    csv_files = list(citydata_dir.rglob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files found in archive: %s", archive_path)
        st.error("No CSV files found in archive")
        return False

    logger.info("Found %d CSV file(s) in archive", len(csv_files))
    st.info(f"Found {len(csv_files)} CSV file(s)")

    # Create table
    try:
        with st.spinner("Creating database table..."):
            create_table()
        logger.info("Database table created successfully")

        # Load data with progress bar
        total = len(csv_files)
        finished = 0
        bar = st.progress(0, text="Loading data...")

        for csv_file in csv_files:
            try:
                load_csv(str(csv_file))
                finished += 1
                logger.debug("Loaded CSV %s (%d/%d)", csv_file.name, finished, total)
                bar.progress(
                    finished / total,
                    text=f"Processing {csv_file.name} ({finished}/{total})"
                )
            except Exception as e:
                logger.warning("Error processing %s: %s", csv_file.name, e)
                st.warning(f"Error processing {csv_file.name}: {str(e)}")

        logger.info("Data loaded successfully, total %d CSV file(s) processed", total)
        st.toast("Data loaded successfully!", icon="🎉")
        return True

    except Exception as e:
        logger.exception("Error during dataset load: %s", e)
        st.error(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    # Run as module so relative imports work: uv run python -m src.data.data_loader
    create_table()
    load_directory(str(CITYDATA_DIR))
