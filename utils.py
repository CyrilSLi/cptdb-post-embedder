# Built-in modules
import re
from urllib.parse import urlparse

# Third-party modules
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def comment_to_embed(url):
    if not re.fullmatch(r"https://cptdb.ca/topic/.+?#(?:findComment|comment)-[0-9]+", url):
        return "Error: Invalid comment URL"

    comment_id = urlparse(url).fragment.split("-")[-1]

    page = BeautifulSoup(requests.get(url).content, "html.parser")

    comment = page.select_one(f"article#elComment_{comment_id}")
    content = comment.select_one(f'div[data-role="commentContent"]') if comment else None
    if not content:
        return "Error: Comment not found"
    
    embed_image = content.select_one("img.ipsImage")["src"] if content.select_one("img.ipsImage") else None
    for img in content.select("a .ipsImage"):
        img.decompose()

    return {
        "title": page.select_one("h1").text.strip() if page.select_one("h1") else "CPTDB Comment",
        "title_url": url,
        "author_name": comment.select_one("h3 a").text.strip() if comment.select_one("h3 a") else "Unknown Author",
        "author_img": comment.select_one(".cAuthorPane_photoWrap img")["src"] if comment.select_one(".cAuthorPane_photoWrap img") else None,
        "author_url": comment.select_one("h3 a")["href"] if comment.select_one("h3 a") else None,
        "timestamp": comment.select_one("time")["datetime"] if comment.select_one("time") else None,
        "image": embed_image,
        "content": html_to_markdown(str(content))
    }

def html_to_markdown(html):
    markdown = md(html).strip()

    markdown = re.sub(r"\n>", "\n> ", markdown) # Discord requires a space after ">" in blockquotes
    markdown = re.sub(r"!\[(.)\]\(.+?twemoji.+?\)", r"\1", markdown) # Remove emoji links
    markdown = markdown.replace("//cptdb.ca", "https://cptdb.ca") # Fix relative links
    markdown = re.sub(r"\n+", "\n", markdown) # Remove extra newlines
    markdown = re.sub(r"(?:\n> )+", "\n> ", markdown) # Remove extra newlines in blockquotes

    return markdown.strip()