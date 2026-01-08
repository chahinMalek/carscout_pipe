import pandas as pd
import plotly.express as px
import streamlit as st


def render_run_duration_chart(metrics: list[dict]) -> None:
    if not metrics:
        st.info("No completed runs to display.")
        return

    df = pd.DataFrame(metrics)
    df["started_at"] = pd.to_datetime(df["started_at"])
    df = df.sort_values("started_at")
    df["duration_minutes"] = df["duration_seconds"] / 60

    st.subheader("⏱️ Run Durations")
    fig = px.bar(
        df,
        x="started_at",
        y="duration_minutes",
        color="status",
        hover_data=["id"],
        labels={
            "started_at": "Run Started At",
            "duration_minutes": "Duration (min)",
            "id": "Run ID",
            "status": "Status",
        },
        color_discrete_map={"success": "#28a745", "failed": "#dc3545", "running": "#ffc107"},
    )
    # adjust bar thickness to 4 hours (in milliseconds)
    fig.update_xaxes(type="date")
    fig.update_traces(width=1000 * 3600 * 4)
    fig.update_layout(hovermode="x")
    st.plotly_chart(fig, width="stretch")

    with st.expander("📋 Run Details"):
        display_df = df[["id", "started_at", "duration_minutes", "status"]].copy()
        display_df.columns = ["Run ID", "Started At", "Duration (min)", "Status"]
        display_df["Duration (min)"] = display_df["Duration (min)"].round(2)
        st.dataframe(display_df, width="stretch", hide_index=True)


def render_run_performance_chart(metrics: list[dict]) -> None:
    if not metrics:
        st.info("No run data available.")
        return

    st.subheader("📊 Run Statistics")

    df = pd.DataFrame(metrics)
    df["started_at"] = pd.to_datetime(df["started_at"])
    df = df.sort_values("started_at")

    df_melted = df.melt(
        id_vars=["started_at", "id"],
        value_vars=["listings", "vehicles", "errors"],
        var_name="Metric",
        value_name="Count",
    )

    fig = px.line(
        df_melted,
        x="started_at",
        y="Count",
        color="Metric",
        markers=True,
        hover_data=["id"],
        labels={"started_at": "Run Started At", "Count": "Count", "id": "Run ID"},
        color_discrete_map={"listings": "#29b5e8", "vehicles": "#ff4b4b", "errors": "#dc3545"},
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, width="stretch")


def render_listings_per_run_chart(data: list[dict]) -> None:
    if not data:
        st.info("No listing data available.")
        return

    df = pd.DataFrame(data)
    df["run_started_at"] = pd.to_datetime(df["run_started_at"])
    df = df.sort_values("run_started_at")

    st.subheader("🔍 Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Listings", df["listing_count"].sum())
    with col2:
        st.metric("Avg per Run", round(df["listing_count"].mean(), 1))
    with col3:
        st.metric("Max in Single Run", df["listing_count"].max())

    st.subheader("📦 Listings Found per Run")
    fig = px.bar(
        df,
        x="run_started_at",
        y="listing_count",
        hover_data=["run_id"],
        labels={
            "run_started_at": "Run Date",
            "listing_count": "Number of Listings",
            "run_id": "Run ID",
        },
        color_discrete_sequence=["#29b5e8"],
    )
    # adjust bar thickness to 4 hours (in milliseconds)
    fig.update_xaxes(type="date")
    fig.update_traces(width=1000 * 3600 * 4)
    fig.update_layout(showlegend=False, hovermode="x")
    st.plotly_chart(fig, width="stretch")


def render_new_vehicles_per_run_chart(data: list[dict]) -> None:
    if not data:
        st.info("No vehicle discovery data available.")
        return

    df = pd.DataFrame(data)
    df["run_started_at"] = pd.to_datetime(df["run_started_at"])
    df = df.sort_values("run_started_at")

    st.subheader("🔍 Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Vehicles", df["new_vehicle_count"].sum())
    with col2:
        st.metric("Avg per Run", round(df["new_vehicle_count"].mean(), 1))
    with col3:
        st.metric("Max in Single Run", df["new_vehicle_count"].max())

    st.subheader("🚗 Vehicles Discovered per Run")
    fig = px.bar(
        df,
        x="run_started_at",
        y="new_vehicle_count",
        hover_data=["run_id"],
        labels={
            "run_started_at": "Run Date",
            "new_vehicle_count": "New Vehicles",
            "run_id": "Run ID",
        },
        color_discrete_sequence=["#29b5e8"],
    )
    # adjust bar thickness to 4 hours (in milliseconds)
    fig.update_xaxes(type="date")
    fig.update_traces(width=1000 * 3600 * 4)
    fig.update_layout(showlegend=False, hovermode="x")
    st.plotly_chart(fig, width="stretch")
