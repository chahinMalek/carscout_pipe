import math

import streamlit as st


def render_pagination(
    total_count: int,
    page_size: int,
    page_key: str,
    filter_hash: str,
) -> int:
    """
    Render pagination controls and manage pagination state.

    Args:
        total_count: Total number of records in the dataset.
        page_size: Number of records per page.
        page_key: Unique key for this pagination's session state (e.g., "runs_page").
        filter_hash: Hash of current filter values to detect filter changes.

    Returns:
        The current offset for data fetching.
    """
    page_state_key = f"{page_key}_page"
    filter_hash_key = f"last_{page_key}_filter_hash"

    # Initialize page state if needed
    if page_state_key not in st.session_state:
        st.session_state[page_state_key] = 1

    # Reset page if filters changed
    if filter_hash_key not in st.session_state or st.session_state[filter_hash_key] != filter_hash:
        st.session_state[page_state_key] = 1
        st.session_state[filter_hash_key] = filter_hash

    current_page = st.session_state[page_state_key]
    offset = (current_page - 1) * page_size

    return offset


def render_pagination_controls(
    total_count: int,
    page_size: int,
    page_key: str,
) -> None:
    """
    Render the pagination navigation buttons.

    Args:
        total_count: Total number of records in the dataset.
        page_size: Number of records per page.
        page_key: Unique key for this pagination's session state.
    """
    page_state_key = f"{page_key}_page"
    current_page = st.session_state.get(page_state_key, 1)
    total_pages = math.ceil(total_count / page_size)

    if total_pages <= 1:
        return

    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col2:
        cols = st.columns(5)
        with cols[1]:
            if st.button(
                "⬅️ Previous",
                key=f"{page_key}_prev",
                disabled=current_page <= 1,
            ):
                st.session_state[page_state_key] -= 1
                st.rerun()
        with cols[2]:
            st.write(f"Page {current_page} of {total_pages}")
        with cols[3]:
            if st.button(
                "Next ➡️",
                key=f"{page_key}_next",
                disabled=current_page >= total_pages,
            ):
                st.session_state[page_state_key] += 1
                st.rerun()
