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


# Resources


@st.cache_resource
def get_container():
    return Container.create_and_patch()


# Types


class ExportFormat(str, Enum):
    CSV = "CSV"
    PARQUET = "Parquet"
    JSON = "JSON"

    @classmethod
    def all_formats(cls):
        return [fmt.value for fmt in cls]


class TableSelection(str, Enum):
    RUNS = "runs"
    LISTINGS = "listings"
    VEHICLES = "vehicles"

    @classmethod
    def all_selections(cls, capitalize: bool = True):
        result = [ts.value for ts in cls]
        if capitalize:
            result = [s.capitalize() for s in result]
        return result


# Constants
PAGE_TITLE = "CarScout Dashboard"
APP_VERSION = get_container().config.app_version()

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


def _convert_df(df, file_type: ExportFormat):
    if file_type == ExportFormat.CSV:
        return df.to_csv(index=False).encode("utf-8")
    elif file_type == ExportFormat.JSON:
        return df.to_json(orient="records", date_format="iso").encode("utf-8")
    elif file_type == ExportFormat.PARQUET:
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        return buffer.getvalue()


def _get_mime_type(file_type: ExportFormat) -> str:
    mapping = {
        ExportFormat.CSV: "text/csv",
        ExportFormat.PARQUET: "application/parquet",
        ExportFormat.JSON: "application/json",
    }
    return mapping.get(file_type)


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
            options=["All"] + RunStatus.all_statuses(),
        )
    with col3:
        page_size = st.selectbox(
            "📏 Page Size",
            options=[10, 25, 50, 100],
            index=0,
            key="runs_page_size",
        )

    # pagination state
    if "runs_page" not in st.session_state:
        st.session_state.runs_page = 1

    # reset page if filters change
    filter_hash = f"runs-{search_id}-{status_filter}-{page_size}"
    if (
        "last_runs_filter_hash" not in st.session_state
        or st.session_state.last_runs_filter_hash != filter_hash
    ):
        st.session_state.runs_page = 1
        st.session_state.last_runs_filter_hash = filter_hash

    # fetch data
    status = None if status_filter == "All" else status_filter
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
                if st.button(
                    "⬅️ Previous", key="runs_prev", disabled=st.session_state.runs_page <= 1
                ):
                    st.session_state.runs_page -= 1
                    st.rerun()
            with cols[2]:
                st.write(f"Page {st.session_state.runs_page} of {total_pages}")
            with cols[3]:
                if st.button(
                    "Next ➡️", key="runs_next", disabled=st.session_state.runs_page >= total_pages
                ):
                    st.session_state.runs_page += 1
                    st.rerun()

    # export
    st.sidebar.divider()
    st.sidebar.header("📥 Export This View")
    export_format = st.sidebar.radio(
        "Format", ExportFormat.all_formats(), horizontal=True, key="runs_export"
    )

    export_data = _convert_df(df, export_format)
    st.sidebar.download_button(
        label=f"Download {len(df)} records",
        data=export_data,
        file_name=f"runs_page_{st.session_state.runs_page}.{export_format.lower()}",
        mime=_get_mime_type(export_format),
        width="stretch",
    )


def render_listings_view():
    container = get_container()
    repo = container.listing_repository()

    st.header("📊 Scraped Listings")

    # render filters
    with st.expander("🔍 Filter Listings", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            search_id = st.text_input("Listing ID", placeholder="Search ID...")
            search_title = st.text_input("Title", placeholder="Search title...")
        with col2:
            c1, c2 = st.columns(2)
            with c1:
                min_price = st.number_input("Min Price", min_value=0, step=1000, value=None)
            with c2:
                max_price = st.number_input("Max Price", min_value=0, step=1000, value=None)
        with col3:
            run_ids = ["All"] + repo.get_unique_run_ids()
            selected_run_id = st.selectbox("Run ID", run_ids)

            date_range = st.date_input("Visited At Range", value=[])
            min_date = None
            max_date = None
            if isinstance(date_range, list | tuple):
                if len(date_range) == 2:
                    min_date = datetime.datetime.combine(date_range[0], datetime.time.min)
                    max_date = datetime.datetime.combine(date_range[1], datetime.time.max)
                elif len(date_range) == 1:
                    min_date = datetime.datetime.combine(date_range[0], datetime.time.min)

    # pagination state
    if "listings_page" not in st.session_state:
        st.session_state.listings_page = 1

    page_size = st.sidebar.selectbox(
        "📏 Listings Page Size", options=[10, 25, 50, 100], index=0, key="list_page_size"
    )

    # reset page if filters change
    run_id_val = None if selected_run_id == "All" else selected_run_id
    filter_hash = f"list-{search_id}-{search_title}-{min_price}-{max_price}-{run_id_val}-{min_date}-{max_date}-{page_size}"
    if (
        "last_listing_filter_hash" not in st.session_state
        or st.session_state.last_listing_filter_hash != filter_hash
    ):
        st.session_state.listings_page = 1
        st.session_state.last_listing_filter_hash = filter_hash

    # fetch data
    offset = (st.session_state.listings_page - 1) * page_size
    listings, total_count = repo.search(
        listing_id=search_id,
        title=search_title,
        min_price=min_price,
        max_price=max_price,
        min_date=min_date,
        max_date=max_date,
        run_id=run_id_val,
        offset=offset,
        limit=page_size,
    )

    if not listings:
        st.info("No listings found matching the search criteria.")
        return

    # prepare data to render
    df = pd.DataFrame([asdict(listing) for listing in listings])
    df.columns = list(map(_format_column_name, df.columns.tolist()))

    # render table
    st.write(
        f"Showing {len(listings)} of {total_count} listings (Page {st.session_state.listings_page})"
    )
    st.dataframe(df, width="stretch", hide_index=True)

    # pagination controls
    total_pages = math.ceil(total_count / page_size)
    if total_pages > 1:
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col2:
            cols = st.columns(5)
            with cols[1]:
                if st.button(
                    "⬅️ Previous", key="list_prev", disabled=st.session_state.listings_page <= 1
                ):
                    st.session_state.listings_page -= 1
                    st.rerun()
            with cols[2]:
                st.write(f"Page {st.session_state.listings_page} of {total_pages}")
            with cols[3]:
                if st.button(
                    "Next ➡️",
                    key="list_next",
                    disabled=st.session_state.listings_page >= total_pages,
                ):
                    st.session_state.listings_page += 1
                    st.rerun()

    # export
    st.sidebar.divider()
    st.sidebar.header("📥 Export This View")
    export_format = st.sidebar.radio(
        "Format", ExportFormat.all_formats(), horizontal=True, key="listings_export"
    )

    export_data = _convert_df(df, export_format)
    st.sidebar.download_button(
        label=f"Download {len(df)} records",
        data=export_data,
        file_name=f"listings_page_{st.session_state.listings_page}.{export_format.lower()}",
        mime=_get_mime_type(export_format),
        width="stretch",
    )


def render_vehicles_view():
    container = get_container()
    repo = container.vehicle_repository()

    st.header("📊 Vehicles Data")

    # render filters
    with st.expander("🔍 Filter Vehicles", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            search_id = st.text_input("Listing ID", placeholder="Search ID...", key="v_search_id")
            search_title = st.text_input(
                "Title", placeholder="Search title...", key="v_search_title"
            )
        with col2:
            c1, c2 = st.columns(2)
            with c1:
                min_price = st.number_input(
                    "Min Price", min_value=0, step=1000, value=None, key="v_min_price"
                )
            with c2:
                max_price = st.number_input(
                    "Max Price", min_value=0, step=1000, value=None, key="v_max_price"
                )
        with col3:
            # Brand dropdown
            brands = ["All"] + repo.get_unique_brands()
            selected_brand = st.selectbox("Brand", brands, key="v_brand")

            # Date range
            date_range = st.date_input("Last Visited Range", value=[], key="v_date_range")
            min_date = None
            max_date = None
            if isinstance(date_range, list | tuple):
                if len(date_range) == 2:
                    min_date = datetime.datetime.combine(date_range[0], datetime.time.min)
                    max_date = datetime.datetime.combine(date_range[1], datetime.time.max)
                elif len(date_range) == 1:
                    min_date = datetime.datetime.combine(date_range[0], datetime.time.min)

    # pagination state
    if "vehicles_page" not in st.session_state:
        st.session_state.vehicles_page = 1

    # Page size in sidebar
    page_size = st.sidebar.selectbox(
        "📏 Vehicles Page Size", options=[10, 25, 50, 100], index=0, key="v_page_size"
    )

    # reset page if filters change
    brand_val = None if selected_brand == "All" else selected_brand
    filter_hash = f"veh-{search_id}-{search_title}-{min_price}-{max_price}-{brand_val}-{min_date}-{max_date}-{page_size}"
    if (
        "last_vehicle_filter_hash" not in st.session_state
        or st.session_state.last_vehicle_filter_hash != filter_hash
    ):
        st.session_state.vehicles_page = 1
        st.session_state.last_vehicle_filter_hash = filter_hash

    # fetch data
    offset = (st.session_state.vehicles_page - 1) * page_size
    vehicles, total_count = repo.search(
        listing_id=search_id,
        title=search_title,
        min_price=min_price,
        max_price=max_price,
        min_date=min_date,
        max_date=max_date,
        brand=brand_val,
        offset=offset,
        limit=page_size,
    )

    if not vehicles:
        st.info("No vehicles found matching the search criteria.")
        return

    # prepare data to render
    df = pd.DataFrame([asdict(v) for v in vehicles])
    df.columns = list(map(_format_column_name, df.columns.tolist()))

    # render table
    st.write(
        f"Showing {len(vehicles)} of {total_count} vehicles (Page {st.session_state.vehicles_page})"
    )
    st.dataframe(df, width="stretch", hide_index=True)

    # pagination controls
    total_pages = math.ceil(total_count / page_size)
    if total_pages > 1:
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col2:
            cols = st.columns(5)
            with cols[1]:
                if st.button(
                    "⬅️ Previous", key="v_prev", disabled=st.session_state.vehicles_page <= 1
                ):
                    st.session_state.vehicles_page -= 1
                    st.rerun()
            with cols[2]:
                st.write(f"Page {st.session_state.vehicles_page} of {total_pages}")
            with cols[3]:
                if st.button(
                    "Next ➡️", key="v_next", disabled=st.session_state.vehicles_page >= total_pages
                ):
                    st.session_state.vehicles_page += 1
                    st.rerun()

    # export
    st.sidebar.divider()
    st.sidebar.header("📥 Export This View")
    export_format = st.sidebar.radio(
        "Format", ExportFormat.all_formats(), horizontal=True, key="vehicles_export"
    )

    export_data = _convert_df(df, export_format)
    st.sidebar.download_button(
        label=f"Download {len(df)} records",
        data=export_data,
        file_name=f"vehicles_page_{st.session_state.vehicles_page}.{export_format.lower()}",
        mime=_get_mime_type(export_format),
        width="stretch",
    )


# Elements

st.title(f"🚗 {PAGE_TITLE}")
st.markdown("---")

# sidebar
st.sidebar.title("🎮 Navigation")
table_selection = st.sidebar.selectbox(
    "Choose Table", TableSelection.all_selections(capitalize=True)
)

# view router
try:
    if table_selection.lower() == TableSelection.RUNS:
        render_runs_view()
    elif table_selection.lower() == TableSelection.LISTINGS:
        render_listings_view()
    elif table_selection.lower() == TableSelection.VEHICLES:
        render_vehicles_view()
except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.info("Check your database connection and migrations.")

st.sidebar.divider()
st.sidebar.caption(f"CarScout Pipeline v{APP_VERSION}")
