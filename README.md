# cptdb-post-embedder

Embed CPTDB forum comments in Slack and/or Discord.

## Installation

- Install Python dependencies: `pip install -r requirements.txt`
- Ensure that the `Roboto` font is installed on your system.
- Set the following environment variables in `.env`:

```
FLASK_PORT=27832
FLASK_BASE_URL=http://your.server.ip:27832
```

### Slack

- Create a Slack app with the OAuth Bot Token scopes `links:read` and `links:write`.
- Subscribe to the `link_shared` bot event with the Request URL set to `http://your.server.ip:27832/slack/events`.
  - Enable Delayed Events to catch events during downtime.
  - Set the App unfurl domain to `cptdb.ca`.
- Set the following environment variables in `.env`:

```
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=slack-signing-secret
```

### Discord

- Create a Discord app with the `Send Messages` Bot Permission.
- Set the following environment variable in `.env`:

```
DISCORD_TOKEN=your-discord-bot-token
```

### Running the server

```bash
# Slack only
python slack_bot.py

# Discord only
python discord_bot.py

# Both (Make sure the Slack bot is running first so the Discord bot can use the same Flask server)
python slack_bot.py
python discord_bot.py

# Run in background (Unix-like systems)
python ~/cptdb-post-embedder/slack_bot.py > /dev/null 2>&1 & disown
sleep 1 # Ensure the Flask server is up
python ~/cptdb-post-embedder/discord_bot.py > /dev/null 2>&1 & disown
```

## Usage

**Slack**: this bot will automatically unfurl CPTDB comment links shared in channels it has access to.

**Discord**: run `/cptdb` then enter a CPTDB comment link in the prompt. The bot will send an embed of the comment.