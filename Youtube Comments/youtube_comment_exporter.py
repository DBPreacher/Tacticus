#!/usr/bin/env python3
"""
YouTube Comment Exporter

Exports every publicly available top-level comment and every publicly
available reply for a YouTube video to both CSV and JSON.

Setup:
  1. Put your YouTube Data API v3 key into API_KEY below.
  2. Run:
       python youtube_comment_exporter.py
  3. Paste a YouTube video URL when prompted.

No third-party Python packages are required.
"""

import csv
import json
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# ADD YOUR YOUTUBE DATA API V3 KEY HERE
# ---------------------------------------------------------------------------
API_KEY = "AIzaSyDELs2mnk4cdrR3FcvTTqVbqbwvriK1eUI"

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def extract_video_id(value: str) -> str:
    """Accept a YouTube URL or a raw 11-character video ID."""
    value = value.strip()

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError:
        parsed = None

    if parsed:
        host = parsed.netloc.lower().split(":")[0]
        path = parsed.path.strip("/")

        if host in {"youtu.be", "www.youtu.be"}:
            candidate = path.split("/")[0]
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
                return candidate

        if host.endswith("youtube.com"):
            query = urllib.parse.parse_qs(parsed.query)
            if "v" in query and query["v"]:
                candidate = query["v"][0]
                if re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
                    return candidate

            parts = path.split("/")
            if len(parts) >= 2 and parts[0] in {"shorts", "live", "embed"}:
                candidate = parts[1]
                if re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
                    return candidate

    match = re.search(r"(?:v=|youtu\.be/|shorts/|live/|embed/)([A-Za-z0-9_-]{11})", value)
    if match:
        return match.group(1)

    raise ValueError("Could not find a valid YouTube video ID in that input.")


def api_get(endpoint: str, params: dict) -> dict:
    params = dict(params)
    params["key"] = API_KEY

    url = f"{YOUTUBE_API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "YouTubeCommentExporter/1.0"}
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            details = json.loads(body)
            message = details.get("error", {}).get("message", body)
        except json.JSONDecodeError:
            message = body

        raise RuntimeError(f"YouTube API error {exc.code}: {message}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc


def channel_id_from_snippet(snippet: dict) -> str:
    channel = snippet.get("authorChannelId") or {}
    return channel.get("value", "") if isinstance(channel, dict) else str(channel)


def make_row(comment: dict, *, video_id: str, parent_id: str = "", is_reply: bool = False,
             thread_index: int = 0, total_reply_count: int = 0) -> dict:
    snippet = comment.get("snippet", {})

    return {
        "platform": "YouTube",
        "video_id": video_id,
        "thread_index": thread_index,
        "comment_id": comment.get("id", ""),
        "parent_id": parent_id,
        "is_reply": is_reply,
        "author": snippet.get("authorDisplayName", ""),
        "author_channel_id": channel_id_from_snippet(snippet),
        "author_channel_url": snippet.get("authorChannelUrl", ""),
        "text": snippet.get("textOriginal") or snippet.get("textDisplay", ""),
        "likes": snippet.get("likeCount", 0),
        "published_at": snippet.get("publishedAt", ""),
        "updated_at": snippet.get("updatedAt", ""),
        "total_reply_count": total_reply_count if not is_reply else "",
    }


def get_all_replies(parent_comment_id: str, video_id: str, thread_index: int) -> list[dict]:
    """Fetch ALL replies. commentThreads may contain only a subset, so use comments.list."""
    rows = []
    page_token = None

    while True:
        params = {
            "part": "snippet",
            "parentId": parent_comment_id,
            "maxResults": 100,
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token

        data = api_get("comments", params)

        for comment in data.get("items", []):
            rows.append(
                make_row(
                    comment,
                    video_id=video_id,
                    parent_id=parent_comment_id,
                    is_reply=True,
                    thread_index=thread_index,
                )
            )

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return rows


def get_all_comments(video_id: str) -> list[dict]:
    rows = []
    page_token = None
    thread_index = 0

    while True:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "order": "time",
        }
        if page_token:
            params["pageToken"] = page_token

        data = api_get("commentThreads", params)

        for thread in data.get("items", []):
            thread_index += 1
            thread_snippet = thread.get("snippet", {})
            top_level = thread_snippet.get("topLevelComment", {})
            top_id = top_level.get("id", "")
            reply_count = int(thread_snippet.get("totalReplyCount", 0) or 0)

            rows.append(
                make_row(
                    top_level,
                    video_id=video_id,
                    is_reply=False,
                    thread_index=thread_index,
                    total_reply_count=reply_count,
                )
            )

            if reply_count > 0 and top_id:
                rows.extend(get_all_replies(top_id, video_id, thread_index))

            print(
                f"\rFetched {thread_index} threads / {len(rows)} total comments & replies...",
                end="",
                flush=True,
            )

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    print()
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    fieldnames = [
        "platform",
        "video_id",
        "thread_index",
        "comment_id",
        "parent_id",
        "is_reply",
        "author",
        "author_channel_id",
        "author_channel_url",
        "text",
        "likes",
        "published_at",
        "updated_at",
        "total_reply_count",
    ]

    # utf-8-sig makes the CSV open cleanly in Excel with Unicode names/text.
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict], path: Path, video_id: str) -> None:
    payload = {
        "video_id": video_id,
        "exported_comment_count": len(rows),
        "comments": rows,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    if API_KEY == "PASTE_YOUR_API_KEY_HERE" or not API_KEY.strip():
        print("\nERROR: Add your YouTube Data API v3 key to API_KEY near the top of this script.")
        print('Example: API_KEY = "AIza..."\n')
        sys.exit(1)

    raw = input("Paste YouTube video URL or video ID: ").strip()

    try:
        video_id = extract_video_id(raw)
        print(f"Video ID: {video_id}")
        print("Downloading public comments and replies...")
        rows = get_all_comments(video_id)
    except (ValueError, RuntimeError) as exc:
        print(f"\nERROR: {exc}\n")
        sys.exit(1)

    csv_path = Path(f"{video_id}_youtube_comments.csv")
    json_path = Path(f"{video_id}_youtube_comments.json")

    write_csv(rows, csv_path)
    write_json(rows, json_path, video_id)

    top_level = sum(1 for row in rows if not row["is_reply"])
    replies = len(rows) - top_level

    print(f"\nDone.")
    print(f"Top-level comments: {top_level}")
    print(f"Replies:            {replies}")
    print(f"Total exported:     {len(rows)}")
    print(f"\nCSV:  {csv_path.resolve()}")
    print(f"JSON: {json_path.resolve()}")
    print("\nUpload either file to ChatGPT for analysis.")


if __name__ == "__main__":
    main()
