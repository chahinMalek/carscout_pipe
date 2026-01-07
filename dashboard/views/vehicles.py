import datetime
from dataclasses import asdict

import pandas as pd
import streamlit as st

from dashboard.components.export import render_export_sidebar
from dashboard.components.pagination import render_pagination, render_pagination_controls
from dashboard.views.utils import format_column_name
from infra.containers import Container


def render_vehicles_view(container: Container) -> None:
    """Render the vehicles data view."""
    repo = container.vehicle_repository()

    st.header("📊 Vehicles Data")

    # Filters
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
            min_date, max_date = _parse_date_range(date_range)

    # Page size in sidebar
    page_size = st.sidebar.selectbox(
        "📏 Vehicles Page Size",
        options=[10, 25, 50, 100],
        index=0,
        key="vehicles_page_size",
    )

    # Pagination setup
    brand_val = None if selected_brand == "All" else selected_brand
    filter_hash = f"veh-{search_id}-{search_title}-{min_price}-{max_price}-{brand_val}-{min_date}-{max_date}-{page_size}"
    offset = render_pagination(
        total_count=0,
        page_size=page_size,
        page_key="vehicles",
        filter_hash=filter_hash,
    )

    # Fetch data
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

    # Prepare DataFrame
    df = pd.DataFrame([asdict(v) for v in vehicles])
    df.columns = list(map(format_column_name, df.columns.tolist()))

    # Display table
    current_page = st.session_state.get("vehicles_page", 1)
    st.write(f"Showing {len(vehicles)} of {total_count} vehicles (Page {current_page})")
    st.dataframe(df, width="stretch", hide_index=True)

    # Pagination controls
    render_pagination_controls(
        total_count=total_count,
        page_size=page_size,
        page_key="vehicles",
    )

    # Export sidebar
    render_export_sidebar(df=df, page_key="vehicles")


def _parse_date_range(
    date_range: list | tuple,
) -> tuple[datetime.datetime | None, datetime.datetime | None]:
    min_date = None
    max_date = None
    if isinstance(date_range, list | tuple):
        if len(date_range) == 2:
            min_date = datetime.datetime.combine(date_range[0], datetime.time.min)
            max_date = datetime.datetime.combine(date_range[1], datetime.time.max)
        elif len(date_range) == 1:
            min_date = datetime.datetime.combine(date_range[0], datetime.time.min)

    return min_date, max_date
