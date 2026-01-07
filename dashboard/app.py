from enum import Enum

import streamlit as st

from dashboard.views import render_listings_view, render_runs_view, render_vehicles_view
from infra.containers import Container


class TableSelection(str, Enum):
    RUNS = "runs"
    LISTINGS = "listings"
    VEHICLES = "vehicles"

    @classmethod
    def all_selections(cls, capitalize: bool = True) -> list[str]:
        result = [ts.value for ts in cls]
        if capitalize:
            result = [s.capitalize() for s in result]
        return result


@st.cache_resource
def get_container() -> Container:
    """Get or create the application container (cached)."""
    return Container.create_and_patch()


# Constants
PAGE_TITLE = "CarScout Dashboard"
APP_VERSION = get_container().config.app_version()

# page setup
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="🚗",
    layout="wide",
)

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

st.title(f"🚗 {PAGE_TITLE}")
st.markdown("---")

# sidebar navigation
st.sidebar.title("🎮 Navigation")
table_selection = st.sidebar.selectbox(
    "Choose Table",
    TableSelection.all_selections(capitalize=True),
)

# view routing logic
try:
    container = get_container()
    selection = table_selection.lower()

    if selection == TableSelection.RUNS:
        render_runs_view(container)
    elif selection == TableSelection.LISTINGS:
        render_listings_view(container)
    elif selection == TableSelection.VEHICLES:
        render_vehicles_view(container)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.info("Check your database connection and migrations.")

# sidebar footer
st.sidebar.divider()
st.sidebar.caption(f"CarScout Pipeline v{APP_VERSION}")
