#!/usr/bin/env python3
"""블로그 RSS에서 최근 글을 읽어 README의 '최근 글' 구간을 갱신한다.

RSS를 읽지 못하거나 글이 없으면 README를 건드리지 않고 정상 종료한다.
"""
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import unquote

FEED = "https://blog.baekchan.com/rss.xml"
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- recent-posts:start -->", "<!-- recent-posts:end -->"
COUNT = 5


def fetch_items():
    req = urllib.request.Request(FEED, headers={"User-Agent": "profile-readme-updater"})
    with urllib.request.urlopen(req, timeout=20) as res:
        root = ET.fromstring(res.read())
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        date = item.findtext("pubDate")
        if not title or not link.startswith("https://blog.baekchan.com/"):
            continue
        day = parsedate_to_datetime(date).strftime("%Y-%m-%d") if date else ""
        items.append((day, title, link))
    return items[:COUNT]


def render(items):
    lines = []
    for day, title, link in items:
        safe = title.replace("[", "(").replace("]", ")").replace("|", "·")
        url = unquote(link).replace(" ", "%20").replace("(", "%28").replace(")", "%29")
        lines.append(f"- [{safe}]({url})" + (f" <sub>{day}</sub>" if day else ""))
    return "\n".join(lines)


def main():
    try:
        items = fetch_items()
    except Exception as exc:  # 네트워크·파싱 실패는 기존 목록을 유지한다
        print(f"feed unavailable, README left as is: {exc}")
        return 0
    if not items:
        print("feed has no items, README left as is")
        return 0
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        print("markers not found in README")
        return 1
    block = f"{START}\n{render(items)}\n{END}"
    updated = pattern.sub(lambda _: block, text)
    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print("README updated")
    else:
        print("no change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
