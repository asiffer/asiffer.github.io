import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Optional

import requests
from pydantic import BaseModel, HttpUrl

namespaces = {
    "hashnode": "https://hashnode.com/rss",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


class RSSItem(BaseModel):
    title: Optional[str]
    link: Optional[HttpUrl]
    description: Optional[str]
    pubDate: Optional[datetime]
    guid: Optional[str]
    image: Optional[HttpUrl]

    def to_html(self) -> str:
        return f"""
        <a class="rss-link shadow-sm rounded-xl border" href="{self.link}">
            <img class="rss-image" src="{self.image}" alt="{self.title}" />
            <div class="rss-info">
                <h3 class="rss-title">{self.title}</h3> 
                <p class="rss-description">{self.description}</p>
            </div>
        </a>
        """


class RSSChannel(BaseModel):
    title: Optional[str]
    link: Optional[HttpUrl]
    description: Optional[str]
    language: Optional[str]
    items: List[RSSItem] = []


def rss_channel_from_xml(xml_str: str) -> RSSChannel:
    root = ET.fromstring(xml_str)
    channel_elem = root.find("channel")
    if channel_elem is None:
        raise ValueError("Invalid RSS feed: missing channel element")
    channel_data = {
        "title": channel_elem.findtext("title"),
        "link": channel_elem.findtext("link"),
        "description": channel_elem.findtext("description"),
        "language": channel_elem.findtext("language"),
        "items": [],
    }
    for item_elem in channel_elem.findall("item"):
        item_data = {
            "title": item_elem.findtext("title"),
            "link": item_elem.findtext("link"),
            "description": item_elem.findtext("description"),
            "pubDate": parsedate_to_datetime(item_elem.findtext("pubDate")),
            "guid": item_elem.findtext("guid"),
            "image": item_elem.findtext("hashnode:coverImage", namespaces=namespaces),
        }
        channel_data["items"].append(RSSItem(**item_data))
    return RSSChannel(**channel_data)


def define_env(env):
    """
    This is the hook for the variables, macros and filters.
    """

    @env.macro
    def rss_feed(url: str) -> str:
        xml_str = requests.get(
            url,
            allow_redirects=True,
            headers={"Accept": "application/xml"},
        ).content.decode("utf-8")
        try:
            channel: RSSChannel = rss_channel_from_xml(xml_str)
        except Exception as e:
            print(f"Error parsing RSS feed: {e}")
            print(f"RSS feed content: {xml_str}")
            return ""

        out = ""
        for feed in channel.items:
            out += feed.to_html()
        return f"""<div class="rss">{out}</div>"""
