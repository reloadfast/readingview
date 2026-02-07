"""
Notification settings component.
"""

import streamlit as st
from config import config
from database.db import ReleaseTrackerDB
from utils.notifications import (
    check_apprise_health,
    test_apprise_connection,
    get_configured_services,
    get_releases_due_soon,
    build_release_digest,
    send_notification,
)
from utils.scheduler import (
    start_scheduler,
    stop_scheduler,
    is_scheduler_running,
    get_next_run_time,
)


def render_notification_settings(db: ReleaseTrackerDB):
    """
    Render notification configuration panel.

    Args:
        db: Release tracker database
    """
    st.markdown("### Notification Settings")

    # --- Connection Status ---
    _render_connection_status()

    # --- Configured Services ---
    if config.APPRISE_API_URL and config.APPRISE_NOTIFICATION_KEY:
        ok, services = get_configured_services(
            config.APPRISE_API_URL, config.APPRISE_NOTIFICATION_KEY
        )
        if ok and services:
            st.markdown(
                f"**Configured services:** {', '.join(services)}"
            )
        elif ok:
            st.info(
                "No notification services configured yet. "
                "See [NOTIFICATIONS.md](NOTIFICATIONS.md) for setup instructions."
            )

    if not config.APPRISE_API_URL or not config.APPRISE_NOTIFICATION_KEY:
        st.warning(
            "Apprise is not configured. Set `APPRISE_API_URL` and "
            "`APPRISE_NOTIFICATION_KEY` in your `.env` file to enable notifications."
        )
        st.code(
            "ENABLE_NOTIFICATIONS=true\n"
            "APPRISE_API_URL=http://your-apprise-server:8000\n"
            "APPRISE_NOTIFICATION_KEY=your_key",
            language="bash",
        )
        return

    st.markdown("---")

    # --- Notification Preferences ---
    settings = db.get_all_notification_settings()

    st.markdown("#### Preferences")

    # Frequency
    freq_options = ["daily", "weekly", "per-event"]
    current_freq = settings.get("frequency", "daily")
    freq_index = freq_options.index(current_freq) if current_freq in freq_options else 0

    frequency = st.radio(
        "Notification frequency",
        freq_options,
        index=freq_index,
        format_func=lambda x: {
            "daily": "Daily digest",
            "weekly": "Weekly digest",
            "per-event": "Immediate (per event)",
        }[x],
        horizontal=True,
        help="How often should notifications be sent?",
    )

    # Days before release
    days_before = st.slider(
        "Days before release to notify",
        min_value=1,
        max_value=30,
        value=int(settings.get("days_before_release", "7")),
        help="Get notified this many days before a tracked release date",
    )

    # New book detection
    notify_new_books = st.checkbox(
        "Notify when tracked authors have new books detected",
        value=settings.get("notify_new_books", "true") == "true",
        help="Check Open Library periodically for new works by tracked authors",
    )

    # Save button
    if st.button("Save Settings", type="primary"):
        db.set_notification_setting("frequency", frequency)
        db.set_notification_setting("days_before_release", str(days_before))
        db.set_notification_setting("notify_new_books", "true" if notify_new_books else "false")
        st.toast("Settings saved!", icon="✅")

    st.markdown("---")

    # --- Test & Send ---
    st.markdown("#### Test & Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Send Test Notification", use_container_width=True):
            with st.spinner("Sending..."):
                ok, msg = test_apprise_connection(
                    config.APPRISE_API_URL,
                    config.APPRISE_NOTIFICATION_KEY,
                )
            if ok:
                st.toast(msg, icon="✅")
            else:
                st.error(msg)

    with col2:
        if st.button("Send Upcoming Digest Now", use_container_width=True):
            current_days = int(db.get_notification_setting("days_before_release") or "7")
            releases = get_releases_due_soon(db, days_ahead=current_days)
            body = build_release_digest(releases)
            if body:
                with st.spinner("Sending digest..."):
                    ok, msg = send_notification(
                        config.APPRISE_API_URL,
                        config.APPRISE_NOTIFICATION_KEY,
                        title=f"ReadingView: {len(releases)} Upcoming Release(s)",
                        body=body,
                    )
                if ok:
                    st.toast(f"Sent digest with {len(releases)} release(s).", icon="✅")
                else:
                    st.error(msg)
            else:
                st.info("No upcoming releases to notify about.")

    # Preview upcoming digest
    current_days = int(db.get_notification_setting("days_before_release") or "7")
    releases = get_releases_due_soon(db, days_ahead=current_days)
    if releases:
        with st.expander(f"Preview: {len(releases)} release(s) in the next {current_days} days"):
            st.text(build_release_digest(releases))

    st.markdown("---")

    # --- Scheduled Digests ---
    st.markdown("#### Scheduled Digests")
    st.caption(
        "Automatically send release digests on a schedule. "
        "Daily runs at 9:00 AM, weekly runs Monday at 9:00 AM."
    )

    running = is_scheduler_running()

    if running:
        next_run = get_next_run_time()
        st.markdown(
            f'<span style="color:#00cc66;">&#x25cf;</span> '
            f"**Scheduler:** Running (next run: {next_run or 'unknown'})",
            unsafe_allow_html=True,
        )
        if st.button("Stop Scheduler"):
            stop_scheduler()
            st.rerun()
    else:
        st.markdown(
            '<span style="color:#808080;">&#x25cf;</span> '
            "**Scheduler:** Not running",
            unsafe_allow_html=True,
        )
        sched_freq = st.radio(
            "Schedule frequency",
            ["daily", "weekly"],
            index=0 if frequency == "daily" else 1,
            horizontal=True,
            key="sched_freq",
        )
        if st.button("Start Scheduler", type="primary"):
            ok = start_scheduler(frequency=sched_freq)
            if ok:
                st.toast(f"Scheduler started ({sched_freq}).", icon="✅")
            else:
                st.error("Failed to start scheduler. Check logs for details.")


def _render_connection_status():
    """Show Apprise connection status indicator."""
    if not config.APPRISE_API_URL:
        st.markdown(
            '<span style="color:#ff4b4b;">&#x25cf;</span> '
            "**Apprise:** Not configured",
            unsafe_allow_html=True,
        )
        return

    if not config.ENABLE_NOTIFICATIONS:
        st.markdown(
            '<span style="color:#ffa500;">&#x25cf;</span> '
            "**Apprise:** Configured but notifications disabled "
            "(`ENABLE_NOTIFICATIONS=false`)",
            unsafe_allow_html=True,
        )
        return

    ok, msg = check_apprise_health(config.APPRISE_API_URL)
    if ok:
        st.markdown(
            '<span style="color:#00cc66;">&#x25cf;</span> '
            f"**Apprise:** Connected ({config.APPRISE_API_URL})",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="color:#ff4b4b;">&#x25cf;</span> '
            f"**Apprise:** {msg}",
            unsafe_allow_html=True,
        )


def render_notification_status_badge():
    """Small status badge for the app header/sidebar."""
    if not config.ENABLE_NOTIFICATIONS or not config.APPRISE_API_URL:
        return

    ok, _ = check_apprise_health(config.APPRISE_API_URL)
    color = "#00cc66" if ok else "#ff4b4b"
    label = "Notifications: Active" if ok else "Notifications: Disconnected"

    st.sidebar.markdown(
        f'<span style="color:{color};">&#x25cf;</span> {label}',
        unsafe_allow_html=True,
    )
