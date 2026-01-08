import datetime
from dataclasses import asdict

import pandas as pd
import streamlit as st

from core.entities.run import RunStatus
from dashboard.components.charts import render_run_duration_chart, render_run_performance_chart
from dashboard.components.export import render_export_sidebar
from dashboard.components.pagination import render_pagination, render_pagination_controls
from dashboard.views.utils import format_column_name, hash_filter_params
from infra.containers import Container

pd.set_option("future.no_silent_downcasting", True)


def render_runs_view(container: Container) -> None:
    repo = container.run_repository()

    # Charts section
    st.header("📈 Run Analytics")

    # Fetch chart data
    run_metrics = repo.get_run_metrics(limit=30)

    # Render charts
    render_run_duration_chart(run_metrics)
    render_run_performance_chart(run_metrics)

    st.markdown("---")

    # Search section
    st.header("📊 Search Runs")

    # collect filter values
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_id = st.text_input("🔍 Search by Run ID", placeholder="Search Run ID ...")
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

    # build search parameters
    search_params = {
        "status": None if status_filter == "All" else status_filter,
        "id_pattern": search_id,
    }

    # pagination setup
    filter_hash = hash_filter_params({**search_params, "page_size": page_size})
    offset = render_pagination(
        page_size=page_size,
        page_key="runs",
        filter_hash=filter_hash,
    )

    # fetch data
    runs, total_count = repo.search(**search_params, offset=offset, limit=page_size)
    if not runs:
        st.info("No runs found matching the search criteria.")
        return

    # display table
    df = pd.DataFrame([asdict(r) for r in runs])
    df.columns = list(map(format_column_name, df.columns.tolist()))
    col_order = list(df)
    completed_at = pd.to_datetime(df["Completed At"].fillna(value=datetime.datetime.now()))
    df["Duration"] = completed_at - df["Started At"]
    col_order.insert(1, "Duration")
    df = df[col_order]

    current_page = st.session_state.get("runs_page", 1)
    st.write(f"Showing {len(runs)} of {total_count} runs (Page {current_page})")
    st.dataframe(df, width="stretch", hide_index=True)

    # pagination controls
    render_pagination_controls(
        total_count=total_count,
        page_size=page_size,
        page_key="runs",
    )

    # export sidebar
    render_export_sidebar(df=df, page_key="runs")
