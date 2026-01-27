"""
Data loading utilities for TravelAssist UI.
Handles dataset upload, extraction, and initialization.
"""

import os
import zipfile
import tarfile
import shutil
from pathlib import Path
import streamlit as st
from pyobvector import ObVecClient
from sqlalchemy import text


def check_data_initialized() -> tuple[bool, int]:
    """
    Check if data is initialized in database.
    
    Returns:
        tuple[bool, int]: (is_initialized, record_count)
    """
    try:
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = os.getenv("DB_PORT", "2881")
        uri = f"{db_host}:{db_port}"
        user = os.getenv("DB_USER", "root")
        db_name = os.getenv("DB_NAME", "test")
        pwd = os.getenv("DB_PASSWORD", "")
        
        client = ObVecClient(uri=uri, user=user, password=pwd, db_name=db_name)
        
        if not client.check_table_exists(table_name="obmms_demo"):
            return False, 0
        
        with client.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as cnt FROM obmms_demo"))
            row = result.fetchone()
            count = row[0] if row else 0
        
        return count > 0, count
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return False, 0


def extract_archive(archive_path: Path, extract_to: Path) -> None:
    """
    Extract compressed archive to target directory.
    
    Args:
        archive_path: Path to the archive file
        extract_to: Target directory for extraction
        
    Raises:
        ValueError: If archive format is not supported
    """
    extract_to.mkdir(parents=True, exist_ok=True)
    
    if archive_path.suffix == '.zip':
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.suffix in ['.tar', '.gz', '.bz2', '.xz'] or '.tar.' in archive_path.name:
        with tarfile.open(archive_path, 'r:*') as tar_ref:
            tar_ref.extractall(extract_to)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path.suffix}")


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
        return None
    
    file_path = upload_dir / uploaded_file.name
    
    # Skip if already exists
    if file_path.exists():
        return file_path
    
    # Write file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    
    return file_path


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
    from obmms.data.attraction_data_preprocessor import create_obmms_table, load_csv
    
    # Clean citydata directory
    if citydata_dir.exists():
        shutil.rmtree(citydata_dir)
    citydata_dir.mkdir(exist_ok=True)
    
    # Extract archive
    with st.spinner("Extracting archive..."):
        extract_archive(archive_path, citydata_dir)
    
    # Find CSV files
    csv_files = list(citydata_dir.rglob("*.csv"))
    if not csv_files:
        st.error("No CSV files found in archive")
        return False
    
    st.info(f"Found {len(csv_files)} CSV file(s)")
    
    # Create table
    try:
        with st.spinner("Creating database table..."):
            create_obmms_table()
        
        # Load data with progress bar
        total = len(csv_files)
        finished = 0
        bar = st.progress(0, text="Loading data...")
        
        for csv_file in csv_files:
            try:
                load_csv(str(csv_file), delete_after_loaded=False)
                finished += 1
                bar.progress(
                    finished / total,
                    text=f"Processing {csv_file.name} ({finished}/{total})"
                )
            except Exception as e:
                st.warning(f"Error processing {csv_file.name}: {str(e)}")
        
        st.toast("Data loaded successfully!", icon="🎉")
        return True
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False
