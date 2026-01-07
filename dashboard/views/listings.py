from dataclasses import asdict

import pandas as pd
import streamlit as st

from dashboard.components.export import render_export_sidebar
from dashboard.components.pagination import render_pagination, render_pagination_controls
from dashboard.views.utils import format_column_name, parse_date_range
from infra.containers import Container


def render_listings_view(container: Container) -> None:
    repo = container.listing_repository()

    st.header("📊 Scraped Listings")

    # Filters
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

    # Page size in sidebar
    page_size = st.sidebar.selectbox(
        "📏 Listings Page Size",
        options=[10, 25, 50, 100],
        index=0,
        key="listings_page_size",
    )

    # Pagination setup
    run_id_val = None if selected_run_id == "All" else selected_run_id
    filter_hash = f"list-{search_id}-{search_title}-{min_price}-{max_price}-{run_id_val}-{min_date}-{max_date}-{page_size}"
    offset = render_pagination(
        total_count=0,
        page_size=page_size,
        page_key="listings",
        filter_hash=filter_hash,
    )

    # Fetch data
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

    # Prepare DataFrame
    df = pd.DataFrame([asdict(listing) for listing in listings])
    df.columns = list(map(format_column_name, df.columns.tolist()))

    # Display table
    current_page = st.session_state.get("listings_page", 1)
    st.write(f"Showing {len(listings)} of {total_count} listings (Page {current_page})")
    st.dataframe(df, width="stretch", hide_index=True)

    # Pagination controls
    render_pagination_controls(
        total_count=total_count,
        page_size=page_size,
        page_key="listings",
    )

    # Export sidebar
    render_export_sidebar(df=df, page_key="listings")
