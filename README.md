# Danger Dorker - Google Dork Search Bot By Xssgit47

![Release](https://img.shields.io/badge/Release-v1.0-red.svg)

## Supported Search Engines

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/368px-Google_2015_logo.svg.png" alt="Google" height="100">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Bing_logo.svg/200px-Bing_logo.svg.png" alt="Bing" height="100">
  <img src="https://upload.wikimedia.org/wikipedia/en/thumb/8/88/DuckDuckGo_logo.svg/200px-DuckDuckGo_logo.svg.png" alt="DuckDuckGo" height="100">
</p>

<p align="center">
  <span style="background-color: #4285F4; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">GOOGLE</span>
  <span style="background-color: #00A4EF; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">BING</span>
  <span style="background-color: #DE5833; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">DUCKDUCKGO</span>
</p>

## Search Features

<p align="center">
  <span style="background-color: #673AB7; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">INTEXT</span>
  <span style="background-color: #FF5722; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">INTITLE</span>
  <span style="background-color: #009688; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">INURL</span>
  <span style="background-color: #E91E63; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">FILETYPE</span>
  <span style="background-color: #3F51B5; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">SITE</span>
  <span style="background-color: #4CAF50; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">EXT</span>
</p>

## Bot Features

<p align="center">
  <span style="background-color: #2196F3; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">ADMIN CONTROL</span>
  <span style="background-color: #FF9800; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">RATE LIMITING</span>
  <span style="background-color: #9C27B0; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">MULTI-ENGINE</span>
  <span style="background-color: #795548; color: white; padding: 5px 10px; border-radius: 5px; margin: 5px;">PROXY SUPPORT</span>
</p>

## Setup Instructions

1. Clone this repository
```bash
git clone https://github.com/Xssgit47/Dorker.git
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Install Chrome browser and ChromeDriver for Selenium

4. Create a `.env` file with your Telegram bot token and admin ID:
```
TELEGRAM_BOT_TOKEN=your_token_here
ADMIN_ID=your_telegram_id
```

5. Start the bot
```bash
python dorker.py
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Get started with the bot |
| `/help` | Show help information |
| `/dork [query]` | Perform a Google dork search (admin only) |
| `/whoami` | Show your Telegram ID |
| `/setadmin [id]` | Set a new admin ID (admin only) |
| `/engine [name]` | Set search engine (Google, Bing, DuckDuckGo) |
| `/status` | Show bot status and rate limits |

## Example Usage

```
/dork intext:password filetype:txt
/engine Bing
/dork inurl:admin intitle:login
```

## Troubleshooting

If you're experiencing issues with Google blocking requests:

1. Try using a different search engine with `/engine [name]`
2. Reduce the frequency of searches
3. Use more specific dork queries
4. Add proxies in the script (optional)

## Requirements

- Python 3.7+
- Chrome browser (for Selenium)
- ChromeDriver (for Selenium)
- Telegram Bot Token

## License

This project is licensed under the MIT License.