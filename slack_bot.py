# Built-in modules
from datetime import datetime

# Third-party modules
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request

from utils import comment_to_embed

load_dotenv()

def embed_to_slack(embed):
    blocks = [
        {
            "type": "card",
            "title": {
                "type": "mrkdwn",
                "text": f'<{embed["title_url"]}|{embed["title"]}>',
                "verbatim": True
            }
        },
        {
            "type": "markdown",
            "text": embed["content"],
        }
    ]
    if embed["author_img"]:
        blocks[0]["icon"] = {
            "type": "image",
            "image_url": embed["author_img"],
            "alt_text": "Author Image"
        }
    if embed["timestamp"]:
        blocks[0]["subtitle"] = {
            "type": "plain_text",
            "text": datetime.fromisoformat(embed["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        }
    if embed["image"]:
        blocks.append({
            "type": "image",
            "image_url": "https://picsum.photos/200/300", # embed["image"],
            "alt_text": "Comment Image"
        })
    return blocks

def main():
    import json
    print(json.dumps({"blocks": embed_to_slack(comment_to_embed("https://cptdb.ca/topic/20302-manitoba-transit-photography/page/47/#findComment-1055566"))}))

if __name__ == "__main__":
    main()