import datetime
import io
import math
from dataclasses import asdict
from enum import Enum

import pandas as pd
import streamlit as st

from core.entities.run import RunStatus
from infra.containers import Container

pd.set_option("future.no_silent_downcasting", True)


# Types
class ExportFormat(str, Enum):
    csv = "CSV"
    parquet = "Parquet"
    json = "JSON"

    @classmethod
    def all_formats(cls):
        return [fmt.value for fmt in cls]


# Constants
PAGE_TITLE = "CarScout Dashboard"

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="🚗",
    layout="wide",
)

# Styling
st.markdown(
    """
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    .pagination-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        margin-top: 20px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Utility functions


def _format_column_name(col: str) -> str:
    return " ".join(c.capitalize() for c in col.split("_"))


def _get_base_metrics():
    container = get_container()
    try:
        runs = container.run_repository().list_all(limit=100)

        # fixme: temporary implementation
        return (
            len(runs),
            "N/A",
            "N/A",
            (
                pd.DataFrame([asdict(r) for r in runs])["status"]
                .isin(["success", "completed"])
                .mean()
                * 100
                if runs
                else 0
            ),
        )
    except Exception:
        return 0, 0, 0, 0


def _convert_df(df, file_type: ExportFormat):
    if file_type == ExportFormat.csv:
        return df.to_csv(index=False).encode("utf-8")
    elif file_type == ExportFormat.json:
        return df.to_json(orient="records", date_format="iso").encode("utf-8")
    elif file_type == ExportFormat.parquet:
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        return buffer.getvalue()


def _get_mime_type(file_type: ExportFormat) -> str:
    mapping = {
        ExportFormat.csv: "text/csv",
        ExportFormat.parquet: "application/parquet",
        ExportFormat.json: "application/json",
    }
    return mapping.get(file_type)


# Resources


@st.cache_resource
def get_container():
    return Container.create_and_patch()


# Render functions


def render_runs_view():
    container = get_container()
    repo = container.run_repository()

    st.header("📊 Pipeline Runs")

    # render filters
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_id = st.text_input("🔍 Search by Run ID", placeholder="e.g. 2024...")
    with col2:
        status_filter = st.selectbox(
            "🎯 Filter by Status",
            options=[
                "All",
                RunStatus.SUCCESS.value,
                RunStatus.FAILED.value,
                RunStatus.RUNNING.value,
            ],
        )
    with col3:
        page_size = st.selectbox(
            "📏 Page Size",
            options=[10, 25, 50, 100],
            index=0,
        )

    # pagination state
    if "runs_page" not in st.session_state:
        st.session_state.runs_page = 1

    # reset page if filters change
    filter_hash = f"{search_id}-{status_filter}-{page_size}"
    if (
        "last_filter_hash" not in st.session_state
        or st.session_state.last_filter_hash != filter_hash
    ):
        st.session_state.runs_page = 1
        st.session_state.last_filter_hash = filter_hash

    # fetch data
    status = None if status_filter not in RunStatus.all_statuses() else status_filter
    offset = (st.session_state.runs_page - 1) * page_size

    runs, total_count = repo.search(
        status=status, id_pattern=search_id, offset=offset, limit=page_size
    )
    if not runs:
        st.info("No runs found matching the search criteria.")
        return

    # prepare data to render
    df = pd.DataFrame([asdict(r) for r in runs])
    df.columns = list(map(_format_column_name, df.columns.tolist()))
    col_order = list(df)
    df["Completed At"] = pd.to_datetime(df["Completed At"].fillna(value=datetime.datetime.now()))
    df["Duration"] = df["Completed At"] - df["Started At"]
    col_order.insert(1, "Duration")
    df = df[col_order]

    # render table
    st.write(f"Showing {len(runs)} of {total_count} runs (Page {st.session_state.runs_page})")
    st.dataframe(df, width="stretch", hide_index=True)

    # pagination controls
    total_pages = math.ceil(total_count / page_size)
    if total_pages > 1:
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col2:
            cols = st.columns(5)
            with cols[1]:
                if st.button("⬅️ Previous", disabled=st.session_state.runs_page <= 1):
                    st.session_state.runs_page -= 1
                    st.rerun()
            with cols[2]:
                st.write(f"Page {st.session_state.runs_page} of {total_pages}")
            with cols[3]:
                if st.button("Next ➡️", disabled=st.session_state.runs_page >= total_pages):
                    st.session_state.runs_page += 1
                    st.rerun()

    # export
    st.sidebar.divider()
    st.sidebar.header("📥 Export This View")
    export_format = st.sidebar.radio(
        "Format", ExportFormat.all_formats(), horizontal=True, key="runs_export"
    )

    export_data = _convert_df(df, export_format)
    export_fname = (
        f"runs_query={filter_hash}_page={st.session_state.runs_page}.{export_format.lower()}"
    )
    st.sidebar.download_button(
        label=f"Download {len(df)} records",
        data=export_data,
        file_name=export_fname,
        mime=_get_mime_type(export_format),
        width="stretch",
    )


def render_generic_view(table_name):
    container = get_container()
    st.header(f"📊 {table_name} View")

    if table_name == "Listings":
        entities = container.listing_repository().list_all(limit=1000)
    else:
        entities = container.vehicle_repository().list_all(limit=1000)

    if not entities:
        st.info(f"No data found in {table_name} table.")
        return

    df = pd.DataFrame([asdict(e) for e in entities])

    # Search for listings
    if table_name == "Listings":
        search_query = st.text_input("🔍 Search by title", "")
        if search_query:
            df = df[df["title"].str.contains(search_query, case=False, na=False)]

    st.write(f"Showing {len(df)} records (limited to 1000)")
    st.dataframe(df, width="stretch", hide_index=True)

    # Export
    st.sidebar.divider()
    st.sidebar.header("📥 Export Data")
    export_format = st.sidebar.radio(
        "Format", ["CSV", "JSON", "Parquet"], horizontal=True, key=f"{table_name}_export"
    )

    export_data = _convert_df(df, export_format)
    st.sidebar.download_button(
        label=f"Download as {export_format}",
        data=export_data,
        file_name=f"{table_name.lower()}_export.{export_format.lower()}",
        mime=f"application/{export_format.lower()}" if export_format != "CSV" else "text/csv",
        width="stretch",
    )


# Elements

st.title(f"🚗 {PAGE_TITLE}")
st.markdown("---")

# Metrics Row
r_count, l_count, v_count, s_rate = _get_base_metrics()
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.metric("Recent Runs", r_count)
with m_col2:
    st.metric("Listings Status", "Connected")
with m_col3:
    st.metric("Vehicles Status", "Connected")
with m_col4:
    st.metric("Success Rate (Recent)", f"{s_rate:.1f}%")

st.markdown("---")

# Sidebar
st.sidebar.title("🎮 Navigation")
table_selection = st.sidebar.selectbox("Choose Table", ["Runs", "Listings", "Vehicles"])

# Route View
try:
    if table_selection == "Runs":
        render_runs_view()
    else:
        render_generic_view(table_selection)
except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.info("Check your database connection and migrations.")

st.sidebar.divider()
st.sidebar.caption("CarScout Pipeline v0.1.4")
