"""
Notification utilities using Apprise API.
"""

import logging
from datetime import date, timedelta
from typing import Any, Optional

import requests

from database.db import ReleaseTrackerDB

logger = logging.getLogger(__name__)

# Map Apprise URL scheme prefixes to friendly display names
SCHEME_NAMES: dict[str, str] = {
    "tgram": "Telegram",
    "discord": "Discord",
    "slack": "Slack",
    "mailto": "Email",
    "gotify": "Gotify",
    "pover": "Pushover",
    "ntfy": "ntfy",
    "json": "JSON/Webhook",
    "xml": "XML",
    "msteams": "Microsoft Teams",
    "matrix": "Matrix",
    "signal": "Signal",
    "rocket": "Rocket.Chat",
    "pbul": "Pushbullet",
}


def get_configured_services(api_url: str, key: str) -> tuple[bool, list[str]]:
    """
    Query Apprise for the notification URLs configured under a key.

    Returns:
        (success, list_of_friendly_service_names)
    """
    url = f"{api_url.rstrip('/')}/json/urls/{key}"
    try:
        resp = requests.get(url, params={"privacy": 1}, timeout=10)
        if not resp.ok:
            return False, []

        data = resp.json()
        urls = data.get("urls", [])
        names = []
        for entry in urls:
            raw_url = entry.get("url", "")
            scheme = raw_url.split("://", 1)[0].lower() if "://" in raw_url else ""
            name = SCHEME_NAMES.get(scheme, scheme.capitalize() if scheme else "Unknown")
            if name not in names:
                names.append(name)
        return True, names
    except (requests.exceptions.RequestException, ValueError):
        return False, []


def test_apprise_connection(api_url: str, key: str) -> tuple[bool, str]:
    """
    Test the Apprise connection by sending a test notification.

    Returns:
        (success, message)
    """
    return send_notification(
        api_url,
        key,
        title="ReadingView Test",
        body="Notifications are working correctly!",
        notify_type="info",
    )


def send_notification(
    api_url: str,
    key: str,
    title: str,
    body: str,
    notify_type: str = "info",
) -> tuple[bool, str]:
    """
    Send a notification via Apprise API.

    Args:
        api_url: Apprise API base URL
        key: Notification key / tag
        title: Notification title
        body: Notification body
        notify_type: One of info, success, warning, failure

    Returns:
        (success, message)
    """
    url = f"{api_url.rstrip('/')}/notify/{key}"

    try:
        resp = requests.post(
            url,
            json={"title": title, "body": body, "type": notify_type},
            timeout=15,
        )
        if resp.ok:
            return True, "Notification sent successfully."
        return False, f"Apprise returned {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.ConnectionError:
        return False, f"Could not connect to Apprise at {api_url}"
    except requests.exceptions.Timeout:
        return False, "Connection to Apprise timed out."
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {e}"


def check_apprise_health(api_url: str) -> tuple[bool, str]:
    """
    Check if the Apprise API server is reachable (without sending a notification).

    Returns:
        (reachable, message)
    """
    try:
        resp = requests.get(
            f"{api_url.rstrip('/')}/status",
            timeout=10,
        )
        if resp.ok:
            return True, "Apprise server is reachable."
        # Some Apprise setups don't have /status, try root
        resp = requests.get(api_url.rstrip('/'), timeout=10)
        if resp.ok:
            return True, "Apprise server is reachable."
        return False, f"Apprise returned {resp.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Cannot reach Apprise: {e}"


def get_releases_due_soon(
    db: ReleaseTrackerDB,
    days_ahead: int = 7,
) -> list[dict[str, Any]]:
    """
    Get releases coming up within the next N days.
    """
    today = date.today()
    end = today + timedelta(days=days_ahead)

    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.book_title, a.author_name, r.release_date,
               r.release_date_confirmed, s.series_name, r.book_number
        FROM releases r
        JOIN tracked_authors a ON r.author_id = a.id
        LEFT JOIN tracked_series s ON r.series_id = s.id
        WHERE r.is_active = 1
          AND r.release_date >= ?
          AND r.release_date <= ?
        ORDER BY r.release_date ASC
        """,
        (today.isoformat(), end.isoformat()),
    )
    return [dict(row) for row in cur.fetchall()]


def build_release_digest(releases: list[dict[str, Any]]) -> Optional[str]:
    """Build a notification body from a list of upcoming releases."""
    if not releases:
        return None

    lines = []
    for r in releases:
        series_info = ""
        if r.get("series_name"):
            series_info = f" ({r['series_name']}"
            if r.get("book_number"):
                series_info += f" #{r['book_number']}"
            series_info += ")"

        confirmed = " [confirmed]" if r.get("release_date_confirmed") else ""
        lines.append(
            f"- {r['book_title']} by {r['author_name']}{series_info} "
            f"on {r['release_date']}{confirmed}"
        )

    return "\n".join(lines)
