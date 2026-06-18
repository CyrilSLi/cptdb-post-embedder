# Built-in modules
import os, re
from base64 import urlsafe_b64decode
from urllib.parse import quote, unquote, urlparse

# Third-party modules
import requests
from bs4 import BeautifulSoup
from cairosvg import svg2png
from dotenv import load_dotenv
from flask import request, Response, send_file
from markdownify import markdownify as md

from minimal_dmp import minimal_dmp

__all__ = ["comment_to_embed", "dataURLsvg_to_png", "image_proxy", "truncate_text", "proj_path"]

def comment_to_embed(url):
    comment_id = re.fullmatch(r"https://cptdb.ca/topic/.+?(?:#findComment-|#comment-|&comment=)([0-9]+)", url)
    if not comment_id:
        return "Error: Invalid comment URL"
    comment_id = comment_id.group(1)

    resp = requests.get(url)
    if resp.status_code == 403:
        return "Error: Unable to access comment (likely a topic that requires an account to view)"
    elif resp.status_code != 200:
        return f"Error: Unable to access comment (HTTP {resp.status_code})"
    page = BeautifulSoup(resp.content, "html.parser")

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

    markdown = re.sub(r"(\A|\n)[^\S\n]+", r"\1", markdown) # Remove spaces at the start of lines
    markdown = re.sub(r"[^\S\n]+(\n|\Z)", r"\1", markdown) # Remove spaces at the end of lines
    markdown = re.sub(r"(\A|\n)>[^\S\n]*", r"\1> ", markdown) # Ensure 1 space at the start of blockquote lines

    markdown = re.sub(r"!\[(.)\]\(.+?twemoji.+?\)", r"\1", markdown) # Remove emoji links
    markdown = markdown.replace("//cptdb.ca", "https://cptdb.ca") # Fix relative links

    # Remove extra newlines in blockquotes
    markdown = re.sub(r"(\A|(?:\A|\s)\n)> (\n> )+", r"\1> ", markdown)
    markdown = re.sub(r"(\n> )+(\Z|\n[^>])", r"\2", markdown)


    # These two regex remove extra newlines while preserving 2 newlines between blockquotes and between non-blockquotes to keep them separate.
    markdown = re.sub(r"((?:\A|\n)> .*?)\n{3,}(> .*?(?:\n|\Z))", r"\1\n\n\2", markdown) # 2 newlines between two blockquotes
    markdown = re.sub(r"((?:\A|\n)[^\s>].*?)\n{2,}(> .*?(?:\n|\Z))", r"\1\n\2", markdown) # 1 newline between non-blockquote and blockquote
    markdown = re.sub(r"((?:\A|\n)> .*?)\n{2,}([^\s>].*?(?:\n|\Z))", r"\1\n\2", markdown) # 1 newline between blockquote and non-blockquote
    markdown = re.sub(r"((?:\A|\n)[^\s>].*?)\n{3,}([^\s>].*?(?:\n|\Z))", r"\1\n\n\2", markdown) # 2 newlines between two non-blockquotes

    return markdown.strip()

def dataURLsvg_to_png():
    try:
        if "diff" in request.args and "v" in request.args:
            dmp = minimal_dmp()
            with open(proj_path("dataurlsvg_templates.txt")) as f:
                template = f.readlines()[int(request.args.get("v"))].strip()
                svg_data = dmp.patch(template, request.args.get("diff")).strip()
        elif "svg" in request.args:
            svg_data = request.args.get("svg")
        else:
            return send_file("cptdb_logo.png", mimetype="image/png")

        if ";base64," in svg_data:
            svg_data = urlsafe_b64decode(svg_data.split(";base64,", 1)[1]).decode()
        else:
            svg_data = svg_data.split(",", 1)[1]

        svg_data = re.sub(r'font-family=".+?Roboto.+?"', 'font-family="Roboto"', svg_data)

        background = re.search(r"background:#[0-9a-f]+", svg_data)
        if background:
            background = background.group(0).split(":")[1]
        else:
            background = "black"

        return Response(svg2png(bytestring=svg_data.encode(), background_color=background, output_width=240, output_height=240), mimetype="image/png")
    except Exception as e:
        return send_file("cptdb_logo.png", mimetype="image/png")

def image_proxy(url, use_http_proxy=True):
    load_dotenv()
    if not url:
        return None

    elif url.startswith("http"):
        if url.startswith("https://wsrv.nl/") or not use_http_proxy:
            return url
        return f"https://wsrv.nl/?url={quote(url)}"

    elif url.startswith("data:image/svg+xml"):
        try:
            with open(proj_path("dataurlsvg_templates.txt")) as f: # Use diff-match-patch to find a shorter representation of the SVG
                diffs = []
                unquoted_url = unquote(url)
                dmp = minimal_dmp()
                for template in f.readlines():
                    diffs.append(dmp.diff(template.strip(), unquoted_url))
                index, shortest_diff = min(enumerate(diffs), key=lambda x: len(x[1]))
                if len(shortest_diff) < len(url):
                    return f"{os.getenv('FLASK_BASE_URL')}/dataurlsvg?v={index}&diff={shortest_diff}"

        except Exception as e:
            pass # If anything goes wrong with diff just use the original URL
        return f"{os.getenv('FLASK_BASE_URL')}/dataurlsvg?svg={url}"

    else:
        return send_file("cptdb_logo.png", mimetype="image/png")

def truncate_text(text, limit):
    if len(text) <= limit:
        return text
    return text[:limit-3] + "..."

def proj_path (file):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)