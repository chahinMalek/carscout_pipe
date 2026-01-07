import datetime
import io
from enum import Enum

import pandas as pd
import streamlit as st


class ExportFormat(str, Enum):
    """Supported export file formats."""

    CSV = "CSV"
    PARQUET = "Parquet"
    JSON = "JSON"

    @classmethod
    def all_formats(cls) -> list[str]:
        return [fmt.value for fmt in cls]


def render_export_sidebar(df: pd.DataFrame, page_key: str) -> None:
    """
    Render the export sidebar with format selection and download button.

    Args:
        df: The DataFrame to export.
        page_key: Unique key for the export radio button.
    """
    st.sidebar.divider()
    st.sidebar.header("📥 Export This View")

    export_format = st.sidebar.radio(
        "Format",
        ExportFormat.all_formats(),
        horizontal=True,
        key=f"{page_key}_export",
    )

    export_data = _export_data(df, export_format)
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    st.sidebar.download_button(
        label="Download",
        data=export_data,
        file_name=f"{page_key}_{now}.{export_format.lower()}",
        mime=_get_mime_type(export_format),
        use_container_width=True,
    )


def _export_data(df: pd.DataFrame, file_type: ExportFormat) -> bytes:
    if file_type == ExportFormat.CSV:
        return df.to_csv(index=False).encode("utf-8")

    elif file_type == ExportFormat.JSON:
        return df.to_json(orient="records", date_format="iso").encode("utf-8")

    elif file_type == ExportFormat.PARQUET:
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        return buffer.getvalue()

    else:
        raise ValueError(f"Unsupported export format: {file_type}")


def _get_mime_type(file_type: ExportFormat) -> str:
    mapping = {
        ExportFormat.CSV: "text/csv",
        ExportFormat.PARQUET: "application/parquet",
        ExportFormat.JSON: "application/json",
    }
    mime_type = mapping.get(file_type)

    if mime_type is None:
        raise ValueError(f"Unsupported export format: {file_type}")
    return mime_type
