from dataclasses import asdict

import pandas as pd
import streamlit as st

from dashboard.components.export import render_export_sidebar
from dashboard.components.pagination import render_pagination, render_pagination_controls
from dashboard.views.utils import format_column_name, hash_filter_params, parse_date_range
from infra.containers import Container


def render_vehicles_view(container: Container) -> None:
    """Render the vehicles data view."""
    repo = container.vehicle_repository()

    st.header("📊 Vehicles Data")

    # collect filter values
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
            brands = ["All"] + repo.get_unique_brands()
            selected_brand = st.selectbox("Brand", brands, key="v_brand")
            date_range = st.date_input("Last Visited Range", value=[], key="v_date_range")
            min_date, max_date = parse_date_range(date_range)

    page_size = st.sidebar.selectbox(
        "📏 Vehicles Page Size",
        options=[10, 25, 50, 100],
        index=0,
        key="vehicles_page_size",
    )

    # build search parameters
    search_params = {
        "listing_id": search_id,
        "title": search_title,
        "min_price": min_price,
        "max_price": max_price,
        "brand": None if selected_brand == "All" else selected_brand,
        "min_date": min_date,
        "max_date": max_date,
    }

    # pagination setup
    filter_hash = hash_filter_params({**search_params, "page_size": page_size})
    offset = render_pagination(
        total_count=0,
        page_size=page_size,
        page_key="vehicles",
        filter_hash=filter_hash,
    )

    # fetch data
    vehicles, total_count = repo.search(**search_params, offset=offset, limit=page_size)
    if not vehicles:
        st.info("No vehicles found matching the search criteria.")
        return

    # display table
    df = pd.DataFrame([asdict(v) for v in vehicles])
    df.columns = list(map(format_column_name, df.columns.tolist()))
    current_page = st.session_state.get("vehicles_page", 1)
    st.write(f"Showing {len(vehicles)} of {total_count} vehicles (Page {current_page})")
    st.dataframe(df, width="stretch", hide_index=True)

    # pagination controls
    render_pagination_controls(
        total_count=total_count,
        page_size=page_size,
        page_key="vehicles",
    )

    # export sidebar
    render_export_sidebar(df=df, page_key="vehicles")
