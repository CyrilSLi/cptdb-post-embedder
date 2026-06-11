# Built-in modules
import os
from datetime import datetime

# Third-party modules
from dotenv import load_dotenv
from flask import Flask, request
from markdown_to_mrkdwn import SlackMarkdownConverter
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from waitress import serve

from utils import * 

def embed_to_slack(embed):
    content = SlackMarkdownConverter().convert(embed["content"])
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'*<{embed["title_url"]}|{embed["title"]}>*\nby <{embed["author_url"]}|{embed["author_name"]}>',
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
    blocks[0]["text"]["text"] = (blocks[0]["text"]["text"] + "\n\n" + content)[:3000] # Slack text block limit
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
                if isinstance(embed, str):
                    unfurls[link["url"]] = {"text": embed}
                else:
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

    flask_app.route("/dataurlsvg", methods=["GET"])(dataURLsvg_to_png)

    serve(flask_app, host="0.0.0.0", port=int(os.getenv("FLASK_PORT")))

if __name__ == "__main__":
    main()