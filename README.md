# TON NFT Verificator Telegram bot
:gem: Easy way to verify the holders of your NFT collection on the TON blockchain

## How bot works:

1. NFT holder writes a message to your bot
2. Bot sends the details for the transfer
3. Holder confirms ownership of the wallet
4. Bot sends a link to a private chat

## How to run bot

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/TON-Punks/ton-nft-verify-bot/tree/main)

### .env variables

You need to specify these env variables to run this bot. If you run it locally, you can also write them in `.env` text file.

``` bash
DATABASE_URL=       # PotsgreSQL database URL
BOT_TOKEN=          # Telegram bot API token from @BotFather // Example: 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
COLLECTION=         # TON address of NFT collection. // Example: EQAo92DYMokxghKcq-CkCGSk_MgXY5Fo1SPW20gkvZl75iCN
TONCENTER_API_KEY=  # toncenter.com API key from @tonapibot
HEROKU_APP_NAME=    # Name of your Heroku app for webhook setup (optional)
```

### Run bot locally

First, you need to install all dependencies:

```bash
pip install -r requirements.txt
```

Then you can run the bot. Don't forget to create `.env` file in the root folder with all required params (read above).

``` bash
python main.py
```

## Working with Database
If you want to add a user to the list of holders, but the collection has not yet reached the mint, you can add the necessary wallets to the **contest** table
