"""
Azure Blob Storage Loader
Downloads current.xlsx and previous.xlsx from Azure Blob Storage
and returns normalized row dicts ready for the analytics pipeline.

Required environment variables:
  BLOB_CONNECTION_STRING   Azure Storage connection string
  BLOB_CONTAINER_NAME      Container name (default: planning-data)
  BLOB_CURRENT_FILE        Blob name for current file (default: current.xlsx)
  BLOB_PREVIOUS_FILE       Blob name for previous file (default: previous.xlsx)
"""
import io
import os
import logging

logger = logging.getLogger(__name__)

# Required columns that must exist in the Excel sheet
REQUIRED_COLUMNS = {"LOCID", "PRDID", "GSCEQUIPCAT"}

# SAP column → canonical name mapping
COLUMN_ALIASES = {
    "LOC ID": "LOCID",
    "PRD ID": "PRDID",
    "MATERIAL ID": "PRDID",
    "EQUIPMENT CATEGORY": "GSCEQUIPCAT",
}

# Defaults — override via env vars
DEFAULT_CONTAINER = "planning-data"
DEFAULT_CURRENT_BLOB = "current.xlsx"
DEFAULT_PREVIOUS_BLOB = "previous.xlsx"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def load_current_previous_from_blob() -> tuple:
    """
    Downloads current.xlsx and previous.xlsx from Azure Blob Storage.
    Returns (current_rows, previous_rows) as list[dict].
    Raises BlobLoaderError on any failure.
    """
    connection_string = _require_env("BLOB_CONNECTION_STRING")
    container = os.environ.get("BLOB_CONTAINER_NAME", DEFAULT_CONTAINER).strip()
    current_blob = os.environ.get("BLOB_CURRENT_FILE", DEFAULT_CURRENT_BLOB).strip()
    previous_blob = os.environ.get("BLOB_PREVIOUS_FILE", DEFAULT_PREVIOUS_BLOB).strip()

    current_bytes = download_blob(connection_string, container, current_blob)
    previous_bytes = download_blob(connection_string, container, previous_blob)

    current_df = load_excel_from_bytes(current_bytes, label="current")
    previous_df = load_excel_from_bytes(previous_bytes, label="previous")

    current_df = standardize_columns(current_df)
    previous_df = standardize_columns(previous_df)

    validate_required_columns(current_df, label="current")
    validate_required_columns(previous_df, label="previous")

    return current_df.to_dict(orient="records"), previous_df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Download from Blob
# ---------------------------------------------------------------------------

def download_blob(connection_string: str, container: str, blob_name: str) -> bytes:
    """Downloads a blob and returns its content as bytes."""
    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        raise BlobLoaderError("azure-storage-blob not installed. Add to requirements.txt.")

    try:
        client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = client.get_blob_client(container=container, blob=blob_name)
        data = blob_client.download_blob().readall()
        logger.info(f"Downloaded blob {container}/{blob_name} ({len(data)} bytes)")
        return data
    except Exception as e:
        msg = str(e)
        if "BlobNotFound" in msg or "404" in msg:
            raise BlobLoaderError(f"Blob not found: {container}/{blob_name}")
        if "AuthenticationFailed" in msg or "403" in msg:
            raise BlobLoaderError(f"Authentication failed for blob: {container}/{blob_name}")
        raise BlobLoaderError(f"Failed to download blob {container}/{blob_name}: {e}")


# ---------------------------------------------------------------------------
# Load Excel from bytes
# ---------------------------------------------------------------------------

def load_excel_from_bytes(content: bytes, label: str = "file"):
    """Loads Excel bytes into a pandas DataFrame."""
    try:
        import pandas as pd
    except ImportError:
        raise BlobLoaderError("pandas not installed. Add to requirements.txt.")

    if not content:
        raise BlobLoaderError(f"Empty file content for {label}.")

    try:
        df = pd.read_excel(io.BytesIO(content), dtype=str)
        df = df.fillna("")
        if df.empty:
            raise BlobLoaderError(f"Excel sheet is empty: {label}")
        logger.info(f"Loaded {label}: {len(df)} rows, {len(df.columns)} columns")
        return df
    except BlobLoaderError:
        raise
    except Exception as e:
        raise BlobLoaderError(f"Failed to parse Excel ({label}): {e}")


# ---------------------------------------------------------------------------
# Standardize + validate columns
# ---------------------------------------------------------------------------

def standardize_columns(df):
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df.rename(columns=COLUMN_ALIASES)


def validate_required_columns(df, label: str = "file"):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise BlobLoaderError(
            f"Missing required columns in {label}: {sorted(missing)}. "
            f"Found: {sorted(df.columns.tolist())}"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise BlobLoaderError(f"Missing required environment variable: {name}")
    return val


class BlobLoaderError(Exception):
    """Raised for any Blob Storage ingestion failure."""
    pass
