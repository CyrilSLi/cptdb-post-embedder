# Built-in modules
import os
from datetime import datetime
from urllib.parse import quote
from waitress import serve

# Third-party modules
from dotenv import load_dotenv
from markdown_to_mrkdwn import SlackMarkdownConverter
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request

from utils import comment_to_embed

def image_proxy(url):
    return f"https://wsrv.nl/?url={quote(url)}"

def embed_to_slack(embed):
    content = SlackMarkdownConverter().convert(embed["content"])
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'*<{embed["title_url"]}|{embed["title"]}>*\nby <{embed["author_url"]}|{embed["author_name"]}>\n\n{content}',
                "verbatim": True
            }
        }
    ]
    if embed["author_img"]:
        blocks[0]["accessory"] = {
            "type": "image",
            "image_url": image_proxy(embed["author_img"]),
            "alt_text": "Author Image"
        }
    if embed["timestamp"]:
        blocks[0]["text"]["text"] += f'\n<!date^{int(datetime.fromisoformat(embed["timestamp"]).timestamp())}^{{date_long_pretty}} at {{time_secs}}|{datetime.fromisoformat(embed["timestamp"]).strftime("%a, %b %d, %Y at %H:%M:%S")}>'
    if embed["image"]:
        blocks.append({
            "type": "image",
            "image_url": image_proxy(embed["image"]),
            "alt_text": "Comment Image"
        })
    return blocks

def main():
    load_dotenv()
    app = App(
        token=os.getenv("SLACK_BOT_TOKEN"),
        signing_secret=os.getenv("SLACK_SIGNING_SECRET")
    )
    flask_app = Flask(__name__)
    handler = SlackRequestHandler(app)

    @app.event("link_shared")
    def handle_link_shared(event, client):
        try:
            unfurls = {}
            for link in event["links"]:
                embed = comment_to_embed(link["url"])
                if not isinstance(embed, str):
                    unfurls[link["url"]] = {"blocks": embed_to_slack(embed)}
            if unfurls:
                client.chat_unfurl(
                    channel=event["channel"],
                    ts=event["message_ts"],
                    unfurls=unfurls,
                    unfurl_id=event.get("unfurl_id")
                )
        except Exception as e:
            print(f"Error handling link_shared event: {e}")

    @flask_app.route("/slack/events", methods=["POST"])
    def slack_events():
        return handler.handle(request)
    
    serve(flask_app, host="0.0.0.0", port=27832)

if __name__ == "__main__":
    main()