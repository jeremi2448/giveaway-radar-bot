import os
import tweepy
import asyncio
from telegram import Bot
import sqlite3
import re
from datetime import datetime
import httpx

# === CONFIG (tout vient des variables d'environnement) ===
TOKEN = os.getenv("8537483737:AAEP1YK-3VV2hKJMntjdoGHt_UXOVoAW4vg")
CHANNEL = os.getenv("@GiveawayRadarChannel") 
BEARER = os.getenv("AAAAAAAAAAAAAAAAAAAAALNQ5wEAAAAARojfYZx44Bbh7oBAXoLhASQU6zo%3DBh2bZ8frMs2QBQSNSMslXh6tpVIy3422TaWURBax6rn8QJNLHy")

bot = Bot(token=TOKEN)
client = tweepy.Client(bearer_token=BEARER)

conn = sqlite3.connect("giveaways.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS posted (tweet_id TEXT UNIQUE)''')
conn.commit()

KEYWORDS = 'giveaway OR win OR "to win" OR contest OR "giving away" -is:retweet lang:en'

async def send_giveaway(tweet, user):
    text = tweet.text.lower()
    
    # Filtre anti-scam + qualité
    if any(scam in text for scam in ["dm me", "telegram me", "whatsapp", "send me"]):
        return
    if user.followers_count < 1000:
        return
        
    category = "🎁"
    if any(x in text for x in ["iphone","macbook","airpods","samsung"]): category = "📱"
    elif any(x in text for x in ["ps5","xbox","nintendo","steam"]): category = "🎮"
    elif any(x in text for x in ["$","paypal","cash","gift card"]): category = "💰"
    elif any(x in text for x in ["btc","eth","sol","nft","crypto"]): category = "🪙"

    prize = text.split("giving away")[-1].split("|")[0].split("\n")[0][:60] + "..."

    message = f"""
{category} GIVEAWAY RADAR

🎁 {prize.capitalize()}
👤 @{user.username} ({user.followers_count//1000}k followers)

🔗 https://twitter.com/{user.username}/status/{tweet.id}

⚡ Détecté à l'instant !
    """.strip()

    await bot.send_message(chat_id=CHANNEL, text=message, disable_web_page_preview=False)

async def main():
    print("🚀 Giveaway Radar Bot démarré !")
    seen_ids = set()

    while True:
        try:
            tweets = client.search_recent_tweets(
                query=KEYWORDS,
                max_results=30,
                tweet_fields=['author_id'],
                user_fields=['username','public_metrics'],
                expansions=['author_id']
            )

            if not tweets.data:
                await asyncio.sleep(180)
                continue

            users = {u.id: u for u in tweets.includes['users']}
            
            for tweet in tweets.data:
                if tweet.id in seen_ids:
                    continue
                    
                c.execute("SELECT 1 FROM posted WHERE tweet_id=?", (str(tweet.id),))
                if c.fetchone():
                    continue

                user = users[tweet.author_id]
                await send_giveaway(tweet, user)
                
                c.execute("INSERT INTO posted VALUES (?)", (str(tweet.id),))
                conn.commit()
                seen_ids.add(tweet.id)

            print(f"✅ Scan terminé - {len(tweets.data)} tweets vérifiés - {datetime.now().strftime('%H:%M')}")
            
        except Exception as e:
            print("Erreur :", e)

        await asyncio.sleep(180)  # toutes les 3 minutes (parfait pour Render gratuit)

if __name__ == "__main__":
    asyncio.run(main())
