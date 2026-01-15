# Stock bot project setup

## Run

1. Set your bot token as an environment variable:

   `export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"`

2. Start the bot:

   `python bot.py`

The bot uses long polling and replies to incoming messages. Keep the process
running to receive updates.

## Keep it running (systemd)

If your previous agent expired, run the bot as a service so it restarts
automatically after reboots or crashes.

1. Copy the example env file and set your token:

   `cp deploy/stock-bot.env.example /etc/stock-bot.env`

2. Copy the service file and edit paths if needed (defaults to `/opt/stock-bot`):

   `cp deploy/stock-bot.service /etc/systemd/system/stock-bot.service`

3. Enable and start the service:

   `systemctl daemon-reload`
   `systemctl enable --now stock-bot`