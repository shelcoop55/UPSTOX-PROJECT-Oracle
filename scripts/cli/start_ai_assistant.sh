#!/bin/bash
# Start the Upstox AI Assistant (Telegram Bot)

# Check if dependencies are installed
if ! python3 -c "import telegram" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the bot
echo "Starting AI Assistant..."
python3 scripts/ai_assistant_bot.py
