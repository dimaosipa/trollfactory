# FabrikaTroliv - Telegram Bot for News Transformation

This Telegram bot transforms official news into anonymous insider-style posts for your Telegram channel. It uses OpenAI's GPT-4o to create compelling, mysterious content formatted as insider leaks from government and military sources.

## Features

- Receives forwarded news messages from authorized users
- Uses OpenAI GPT-4o to transform the content into insider-style posts
- Publishes the transformed content to a specified Telegram channel
- Includes rate limiting to avoid OpenAI API request limits
- Implements user authorization to secure bot access
- Uses asynchronous processing for better performance
- Comprehensive logging for all operations

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Telegram Bot token (obtained from [BotFather](https://t.me/botfather))
- OpenAI API key
- A Telegram channel where the bot is admin

### Installation

1. **Clone or download this repository**

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Edit the `.env` file in the project directory and add your credentials:

   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   TELEGRAM_CHANNEL_ID=your_channel_id
   ADMIN_USER_ID=your_telegram_user_id
   ```

   - **TELEGRAM_BOT_TOKEN**: Obtain from [BotFather](https://t.me/botfather)
   - **OPENAI_API_KEY**: Get from the [OpenAI Dashboard](https://platform.openai.com/account/api-keys)
   - **TELEGRAM_CHANNEL_ID**: The ID of your channel (usually starts with `-100`)
   - **ADMIN_USER_ID**: Your Telegram user ID (can be obtained from [@userinfobot](https://t.me/userinfobot))

4. **Make your bot an admin of the target channel**

## Usage

1. **Start the bot**

   ```bash
   python bot.py
   ```

2. **Interacting with the bot**

   - Send `/start` to the bot to verify it's working
   - Forward any news article to the bot
   - The bot will process the text, transform it into an insider-style post, and publish it to your channel
   - You'll receive a confirmation message when the post is published

## Post Format

The generated posts follow this format:

1. A mysterious introduction hinting at leaked information
2. A clear statement about the event based on "leaked" data
3. Confirmation through indirect facts or statements
4. Strategic analysis in a numbered list or brief points
5. Conclusion with a hint about future events or leaks

## Stopping the Bot

To stop the bot, press `Ctrl+C` in the terminal where it's running, or use the following commands to find and kill the process:

```bash
# Find the process ID
ps aux | grep "python" | grep "bot.py"

# Kill the process
kill -9 <PID>
```

## Logs

Logs are stored in `bot.log` in the project directory. Check this file for debugging information and operation history.

## Troubleshooting

If the bot doesn't respond:

1. Check that all environment variables are correctly set in the `.env` file
2. Ensure the bot is an admin in your Telegram channel
3. Verify your OpenAI API key is valid and has sufficient quota
4. Check the `bot.log` file for error messages
5. Make sure you're using the correct Telegram user ID for authorization

## Security Notes

- Keep your `.env` file secure and never commit it to public repositories
- The bot only accepts commands from the authorized admin user ID
- Rate limiting is implemented to prevent excessive API usage

## License

This project is for personal use.