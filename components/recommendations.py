"""UI component for the book recommender tab."""

import streamlit as st


def render_recommendations_view():
    """Render the Recommendations tab."""
    import book_recommender
    from book_recommender._config import get_config
    from book_recommender._exceptions import BookRecommenderConfigError

    st.header("Book Recommendations")

    cfg = get_config()
    is_valid, error = cfg.validate()
    if not is_valid:
        st.error(f"Recommender misconfigured: {error}")
        return

    # Check Ollama connectivity
    try:
        from book_recommender._ollama import OllamaClient
        client = OllamaClient(cfg.ollama_url, cfg.embed_model, cfg.llm_model)
        if not client.is_available():
            st.warning(
                f"Ollama is not reachable at `{cfg.ollama_url}`. "
                "Recommendations require a running Ollama instance.\n\n"
                "Set `BOOK_RECOMMENDER_LOG_LEVEL=DEBUG` for detailed diagnostics."
            )
    except Exception as e:
        st.warning(
            f"Could not check Ollama connectivity: {e}\n\n"
            "Set `BOOK_RECOMMENDER_LOG_LEVEL=DEBUG` for detailed diagnostics."
        )

    # --- Ingest section ---
    with st.expander("Add Books to Catalog", expanded=False):
        st.markdown("Add books so the recommender has a catalog to search through.")
        col1, col2 = st.columns(2)
        with col1:
            isbn_input = st.text_input("ISBN", key="rec_isbn")
            if st.button("Ingest by ISBN", key="rec_isbn_btn") and isbn_input:
                with st.spinner("Fetching metadata..."):
                    try:
                        book_id = book_recommender.ingest(isbn=isbn_input)
                        if book_id:
                            st.toast(f"Ingested: {book_id}", icon="✅")
                        else:
                            st.warning("No results found for that ISBN.")
                    except BookRecommenderConfigError as e:
                        st.error(str(e))
        with col2:
            title_input = st.text_input("Title", key="rec_title")
            author_input = st.text_input("Author (optional)", key="rec_author")
            if st.button("Ingest by Title", key="rec_title_btn") and title_input:
                with st.spinner("Fetching metadata..."):
                    try:
                        book_id = book_recommender.ingest(
                            title=title_input,
                            author=author_input or None,
                        )
                        if book_id:
                            st.toast(f"Ingested: {book_id}", icon="✅")
                        else:
                            st.warning("No results found.")
                    except BookRecommenderConfigError as e:
                        st.error(str(e))

    # --- Ingested books section ---
    with st.expander("Ingested Books", expanded=False):
        from book_recommender._db import RecommenderDB
        rec_db = RecommenderDB(cfg.db_path)
        all_books = rec_db.get_all_books()
        if not all_books:
            st.info("No books in the catalog yet. Use the section above to add some.")
        else:
            st.markdown(f"**{len(all_books)}** book(s) in the catalog.")
            for book in all_books:
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    authors_str = ", ".join(book.get("authors", []))
                    st.markdown(f"**{book['title']}** — {authors_str}" if authors_str else f"**{book['title']}**")
                with col_btn:
                    if st.button("Remove", key=f"rec_remove_{book['id']}"):
                        book_recommender.remove_book(book['id'])
                        st.rerun()

    st.markdown("---")

    # --- Recommend section ---
    st.subheader("Get Recommendations")

    prompt_input = st.text_area(
        "Describe what you're looking for",
        placeholder="e.g., epic fantasy with complex magic systems and political intrigue",
        key="rec_prompt",
    )

    if st.button("Recommend", key="rec_go"):
        if not prompt_input.strip():
            st.info("Enter a description of what you'd like to read.")
            return
        with st.spinner("Generating recommendations..."):
            results = book_recommender.recommend(free_text_prompt=prompt_input)
        if not results:
            st.info("No recommendations found. Try adding more books to the catalog first.")
        else:
            # Store results in session state for feedback
            st.session_state["_rec_results"] = results
            st.session_state["_rec_prompt_used"] = prompt_input

    # Render results (persisted in session state across reruns)
    results = st.session_state.get("_rec_results", [])
    prompt_used = st.session_state.get("_rec_prompt_used", "")

    if results:
        for i, rec in enumerate(results):
            with st.container():
                st.markdown(f"**{rec['title']}** — {', '.join(rec.get('authors', []))}")
                if rec.get("description"):
                    st.caption(rec["description"][:300] + ("..." if len(rec["description"] or "") > 300 else ""))
                st.progress(min(rec["score"], 1.0), text=f"Score: {rec['score']:.2f}")
                if rec.get("explanation"):
                    st.markdown(f"*{rec['explanation']}*")

                # Feedback buttons
                fb_col1, fb_col2, fb_col3 = st.columns([1, 1, 6])
                with fb_col1:
                    if st.button("👍", key=f"rec_up_{i}"):
                        book_recommender.submit_feedback(
                            book_id=rec["book_id"],
                            rating=1,
                            source_prompt=prompt_used or None,
                        )
                        st.toast(f"Positive feedback recorded for {rec['title']}")
                with fb_col2:
                    if st.button("👎", key=f"rec_down_{i}"):
                        book_recommender.submit_feedback(
                            book_id=rec["book_id"],
                            rating=-1,
                            source_prompt=prompt_used or None,
                        )
                        st.toast(f"Negative feedback recorded for {rec['title']}")
                st.markdown("---")
