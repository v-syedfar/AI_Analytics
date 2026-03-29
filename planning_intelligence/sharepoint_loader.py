"""
SharePoint Loader
Authenticates to SharePoint via Azure AD app credentials,
downloads current.xlsx and previous.xlsx, and returns
normalized row dicts ready for the analytics pipeline.

Required environment variables:
  SHAREPOINT_TENANT_ID
  SHAREPOINT_CLIENT_ID
  SHAREPOINT_CLIENT_SECRET
  SHAREPOINT_SITE_URL          e.g. https://microsoft.sharepoint.com/teams/COI-ConstructionEngineering

  Option A — by file path:
  SHAREPOINT_CURRENT_FILE      e.g. /Shared Documents/planning/current.xlsx
  SHAREPOINT_PREVIOUS_FILE     e.g. /Shared Documents/planning/previous.xlsx

  Option B — by document GUID (preferred when filenames change monthly):
  SHAREPOINT_CURRENT_GUID      e.g. 64CA35FA-D4F2-4574-B61F-3427AAAF3B51
  SHAREPOINT_PREVIOUS_GUID     e.g. 8C6E67F7-0E0D-4267-B45D-FA5728DC2DA7
"""
import io
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Required columns that must exist in the Excel sheet
REQUIRED_COLUMNS = {"LOCID", "PRDID", "GSCEQUIPCAT"}

# SAP column → canonical name mapping (for standardization)
COLUMN_ALIASES = {
    "LOC ID": "LOCID",
    "PRD ID": "PRDID",
    "MATERIAL ID": "PRDID",
    "EQUIPMENT CATEGORY": "GSCEQUIPCAT",
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def load_current_previous_from_sharepoint() -> tuple:
    """
    Downloads current and previous Excel files from SharePoint.
    Supports two modes:
    - GUID mode: uses SHAREPOINT_CURRENT_GUID / SHAREPOINT_PREVIOUS_GUID
    - Path mode: uses SHAREPOINT_CURRENT_FILE / SHAREPOINT_PREVIOUS_FILE
    Returns (current_rows, previous_rows) as list[dict].
    """
    token = _get_access_token()
    site_url = _require_env("SHAREPOINT_SITE_URL").rstrip("/")

    # Prefer GUID mode — works even when filenames change monthly
    current_guid = os.environ.get("SHAREPOINT_CURRENT_GUID", "").strip()
    previous_guid = os.environ.get("SHAREPOINT_PREVIOUS_GUID", "").strip()

    if current_guid and previous_guid:
        current_bytes = download_by_guid(token, site_url, current_guid)
        previous_bytes = download_by_guid(token, site_url, previous_guid)
    else:
        current_path = _require_env("SHAREPOINT_CURRENT_FILE")
        previous_path = _require_env("SHAREPOINT_PREVIOUS_FILE")
        current_bytes = download_sharepoint_file(token, site_url, current_path)
        previous_bytes = download_sharepoint_file(token, site_url, previous_path)

    current_df = load_excel_from_bytes(current_bytes, label="current")
    previous_df = load_excel_from_bytes(previous_bytes, label="previous")

    current_df = standardize_columns(current_df)
    previous_df = standardize_columns(previous_df)

    validate_required_columns(current_df, label="current")
    validate_required_columns(previous_df, label="previous")

    return current_df.to_dict(orient="records"), previous_df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Step 1: Authenticate
# ---------------------------------------------------------------------------

def _get_access_token() -> str:
    """Obtains an OAuth2 token from Azure AD using client credentials."""
    try:
        import requests
    except ImportError:
        raise SharePointError("requests package not installed. Add to requirements.txt.")

    tenant_id = _require_env("SHAREPOINT_TENANT_ID")
    client_id = _require_env("SHAREPOINT_CLIENT_ID")
    client_secret = _require_env("SHAREPOINT_CLIENT_SECRET")
    site_url = _require_env("SHAREPOINT_SITE_URL")

    # Extract hostname for resource scope
    from urllib.parse import urlparse
    hostname = urlparse(site_url).netloc  # e.g. contoso.sharepoint.com

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": f"https://{hostname}/.default",
    }

    try:
        resp = requests.post(token_url, data=payload, timeout=15)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise SharePointError("No access_token in auth response.")
        logger.info("SharePoint auth token obtained.")
        return token
    except requests.RequestException as e:
        raise SharePointError(f"Authentication failed: {e}")


# ---------------------------------------------------------------------------
# Step 2: Download file by GUID
# ---------------------------------------------------------------------------

def download_by_guid(token: str, site_url: str, item_id: str) -> bytes:
    """
    Downloads a file from SharePoint using its document GUID/item ID.
    Works regardless of filename — ideal for monthly-renamed files.
    """
    try:
        import requests
    except ImportError:
        raise SharePointError("requests package not installed.")

    from urllib.parse import urlparse
    parsed = urlparse(site_url)
    hostname = parsed.netloc
    site_path = parsed.path.rstrip("/")

    graph_url = (
        f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
        f":/drive/items/{item_id}/content"
    )
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(graph_url, headers=headers, timeout=30)
        if resp.status_code == 404:
            raise SharePointError(f"Document not found with ID: {item_id}")
        resp.raise_for_status()
        logger.info(f"Downloaded document {item_id} ({len(resp.content)} bytes)")
        return resp.content
    except requests.RequestException as e:
        raise SharePointError(f"Failed to download document {item_id}: {e}")


# ---------------------------------------------------------------------------
# Step 3: Download file by path
# ---------------------------------------------------------------------------

def download_sharepoint_file(token: str, site_url: str, file_path: str) -> bytes:
    """
    Downloads a file from SharePoint using the Graph API.
    file_path: server-relative path e.g. /Shared Documents/planning/current.xlsx
    """
    try:
        import requests
    except ImportError:
        raise SharePointError("requests package not installed.")

    from urllib.parse import urlparse, quote
    parsed = urlparse(site_url)
    hostname = parsed.netloc
    site_path = parsed.path.rstrip("/")

    # Build Graph API URL
    encoded_path = quote(file_path)
    graph_url = (
        f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
        f":/drive/root:{encoded_path}:/content"
    )

    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(graph_url, headers=headers, timeout=30)
        if resp.status_code == 404:
            raise SharePointError(f"File not found: {file_path}")
        resp.raise_for_status()
        logger.info(f"Downloaded {file_path} ({len(resp.content)} bytes)")
        return resp.content
    except requests.RequestException as e:
        raise SharePointError(f"Failed to download {file_path}: {e}")


# ---------------------------------------------------------------------------
# Step 3: Load Excel
# ---------------------------------------------------------------------------

def load_excel_from_bytes(content: bytes, label: str = "file"):
    """Loads Excel bytes into a pandas DataFrame."""
    try:
        import pandas as pd
    except ImportError:
        raise SharePointError("pandas not installed. Add to requirements.txt.")

    if not content:
        raise SharePointError(f"Empty file content for {label}.")

    try:
        df = pd.read_excel(io.BytesIO(content), dtype=str)
        df = df.fillna("")
        if df.empty:
            raise SharePointError(f"Excel sheet is empty: {label}")
        logger.info(f"Loaded {label}: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        raise SharePointError(f"Failed to parse Excel ({label}): {e}")


# ---------------------------------------------------------------------------
# Step 4: Standardize columns
# ---------------------------------------------------------------------------

def standardize_columns(df):
    """
    Normalizes column names:
    - strips whitespace
    - uppercases
    - applies known aliases
    """
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns=COLUMN_ALIASES)
    return df


# ---------------------------------------------------------------------------
# Step 5: Validate required columns
# ---------------------------------------------------------------------------

def validate_required_columns(df, label: str = "file"):
    """Raises SharePointError if any required column is missing."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise SharePointError(
            f"Missing required columns in {label}: {sorted(missing)}. "
            f"Found: {sorted(df.columns.tolist())}"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise SharePointError(f"Missing required environment variable: {name}")
    return val


class SharePointError(Exception):
    """Raised for any SharePoint ingestion failure."""
    pass
