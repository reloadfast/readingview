"""
Collections component — user-created named collections for organizing books.
"""

import math
import streamlit as st
from typing import Any, Dict, List
from api.audiobookshelf import AudiobookshelfAPI, AudiobookData
from config.config import config
from database.db import ReleaseTrackerDB
from utils.helpers import render_empty_state
import logging

logger = logging.getLogger(__name__)


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def _fetch_all_items(base_url: str, token: str):
    api = AudiobookshelfAPI(base_url, token)
    items = []
    for lib in api.get_libraries():
        items.extend(api.get_library_items(lib["id"]))
    return items


def render_collections_view(api: AudiobookshelfAPI, db: ReleaseTrackerDB):
    """Render the collections view."""
    st.markdown("### Collections")
    st.caption("Organize your books into custom collections")

    items = _fetch_all_items(api.base_url, api.token)
    item_map = {}
    for item in items:
        meta = AudiobookData.extract_metadata(item)
        item_map[meta["id"]] = meta

    collections = db.get_collections()

    # Create new collection
    with st.expander("Create New Collection"):
        with st.form("new_collection"):
            name = st.text_input("Collection Name", placeholder="e.g., Summer 2026")
            desc = st.text_input("Description (optional)", placeholder="Books to read this summer")
            if st.form_submit_button("Create", type="primary"):
                if name.strip():
                    try:
                        db.create_collection(name.strip(), desc.strip())
                        st.toast(f"Created '{name}'!", icon="✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
                else:
                    st.warning("Name is required.")

    if not collections:
        render_empty_state(
            "No collections yet",
            "Create your first collection above to start organizing your books.",
            icon="📂",
        )
        return

    # Display each collection
    for coll in collections:
        coll_items = db.get_collection_items(coll["id"])
        item_count = len(coll_items)
        desc_text = f" — {coll['description']}" if coll.get("description") else ""

        with st.expander(
            f"📂 {coll['name']} ({item_count} book{'s' if item_count != 1 else ''}){desc_text}",
            expanded=st.session_state.get(f"coll_expanded_{coll['id']}", False),
        ):
            # Collection actions
            act1, act2, act3 = st.columns(3)
            with act1:
                if st.button("Add Books", key=f"coll_add_{coll['id']}", use_container_width=True):
                    st.session_state[f"coll_adding_{coll['id']}"] = True
                    st.session_state[f"coll_expanded_{coll['id']}"] = True
                    st.rerun()
            with act2:
                if st.button("Rename", key=f"coll_rename_{coll['id']}", use_container_width=True):
                    st.session_state[f"coll_renaming_{coll['id']}"] = True
                    st.session_state[f"coll_expanded_{coll['id']}"] = True
                    st.rerun()
            with act3:
                if st.button("Delete Collection", key=f"coll_del_{coll['id']}", use_container_width=True):
                    db.delete_collection(coll["id"])
                    st.toast(f"Deleted '{coll['name']}'", icon="🗑️")
                    st.rerun()

            # Rename form
            if st.session_state.get(f"coll_renaming_{coll['id']}"):
                with st.form(f"rename_coll_{coll['id']}"):
                    new_name = st.text_input("New name", value=coll["name"])
                    new_desc = st.text_input("New description", value=coll.get("description") or "")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.form_submit_button("Save", type="primary"):
                            if new_name.strip():
                                db.rename_collection(coll["id"], new_name.strip(), new_desc.strip())
                                st.session_state.pop(f"coll_renaming_{coll['id']}", None)
                                st.toast("Renamed!", icon="✅")
                                st.rerun()
                    with c2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.pop(f"coll_renaming_{coll['id']}", None)
                            st.rerun()

            # Add books form
            if st.session_state.get(f"coll_adding_{coll['id']}"):
                existing_ids = set(coll_items)
                available = [
                    m for m in item_map.values()
                    if m["id"] not in existing_ids
                ]
                if not available:
                    st.info("All library books are already in this collection.")
                else:
                    with st.form(f"add_to_coll_{coll['id']}"):
                        selected = st.multiselect(
                            "Select books to add",
                            options=[b["id"] for b in available],
                            format_func=lambda bid: f"{item_map[bid]['title']} — {item_map[bid]['author']}",
                        )
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.form_submit_button("Add", type="primary"):
                                for bid in selected:
                                    db.add_to_collection(coll["id"], bid)
                                st.session_state.pop(f"coll_adding_{coll['id']}", None)
                                st.toast(f"Added {len(selected)} book(s)!", icon="✅")
                                st.rerun()
                        with c2:
                            if st.form_submit_button("Cancel"):
                                st.session_state.pop(f"coll_adding_{coll['id']}", None)
                                st.rerun()

            # Display collection books
            if coll_items:
                for lib_id in coll_items:
                    meta = item_map.get(lib_id)
                    if not meta:
                        continue
                    col_cover, col_info, col_action = st.columns([1, 4, 1])
                    with col_cover:
                        st.image(api.get_cover_url(lib_id), width=60)
                    with col_info:
                        st.markdown(f"**{meta['title']}**")
                        st.caption(meta["author"])
                    with col_action:
                        if st.button("Remove", key=f"coll_rm_{coll['id']}_{lib_id}"):
                            db.remove_from_collection(coll["id"], lib_id)
                            st.toast("Removed from collection", icon="✅")
                            st.rerun()
            else:
                st.caption("This collection is empty. Use 'Add Books' above.")
