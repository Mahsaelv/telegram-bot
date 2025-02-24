# Travel Bot - Telegram Travel Guide Bot

This Telegram bot helps users calculate the distance between two cities and receive various information such as weather status and tourist attractions of cities.

## Features
- Calculate the distance between two cities
- Estimate travel time by car, train, and airplane
- Display the weather status of the destination
- Provide information about the destination city (population, attractions, foods, etc.)

## Installation and Setup

### 1. Install Dependencies
To install the required dependencies for the project, use the following command:

```bash
pip install -r requirements.txt
```

### 2. API Configuration
Create a .env file In your project, create a .env file and add the following values:

BOT_TOKEN=your_telegram_bot_token

### 3. Running the Bot
After creating the .env file, start the bot by running the following command:
```
python main.py
```
### 4. Using the Bot
Start the bot by typing /start. To calculate the distance, use the /calculate command and enter two cities. To view the weather and more information about a city, click on the available options in the bot's reply.