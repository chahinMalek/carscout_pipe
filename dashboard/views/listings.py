from dataclasses import asdict

import pandas as pd
import streamlit as st

from dashboard.components.charts import render_listings_per_run_chart
from dashboard.components.export import render_export_sidebar
from dashboard.components.pagination import render_pagination, render_pagination_controls
from dashboard.views.utils import format_column_name, hash_filter_params, parse_date_range
from infra.containers import Container


def render_listings_view(container: Container) -> None:
    repo = container.listing_repository()

    # Chart section
    st.header("📈 Listings Analytics")
    listings_per_run = repo.get_listings_per_run(limit=30)
    render_listings_per_run_chart(listings_per_run)

    st.markdown("---")

    # Search section
    st.header("📊 Search Listings")

    # collect filter values
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
            min_date, max_date = parse_date_range(date_range)

    page_size = st.sidebar.selectbox(
        "📏 Listings Page Size",
        options=[10, 25, 50, 100],
        index=0,
        key="listings_page_size",
    )

    # build search parameters
    search_params = {
        "listing_id": search_id,
        "title": search_title,
        "min_price": min_price,
        "max_price": max_price,
        "run_id": None if selected_run_id == "All" else selected_run_id,
        "min_date": min_date,
        "max_date": max_date,
    }

    # pagination setup
    filter_hash = hash_filter_params({**search_params, "page_size": page_size})
    offset = render_pagination(
        page_size=page_size,
        page_key="listings",
        filter_hash=filter_hash,
    )

    # fetch data
    listings, total_count = repo.search(**search_params, offset=offset, limit=page_size)
    if not listings:
        st.info("No listings found matching the search criteria.")
        return

    # display table
    df = pd.DataFrame([asdict(listing) for listing in listings])
    df.columns = list(map(format_column_name, df.columns.tolist()))
    current_page = st.session_state.get("listings_page", 1)
    st.write(f"Showing {len(listings)} of {total_count} listings (Page {current_page})")
    st.dataframe(df, width="stretch", hide_index=True)

    # pagination controls
    render_pagination_controls(
        total_count=total_count,
        page_size=page_size,
        page_key="listings",
    )

    # export sidebar
    render_export_sidebar(df=df, page_key="listings")
