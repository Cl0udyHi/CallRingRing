import discord
from dotenv import load_dotenv
import os
import json
import aiohttp

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")

client = discord.Client(enable_debug_events=True)

async def get_user_name(user_id):
    user = client.get_user(int(user_id))
    if user:
        return user.name
    try:
        user = await client.fetch_user(int(user_id))
        return user.name
    except:
        return str(user_id)

async def bot_dm(content):
    if not BOT_TOKEN or not client.user:
        print("BOT_TOKEN not set or not connected")
        return
    user_id = str(client.user.id)
    print(f"Attempting to DM user {user_id} via bot...")
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}
        async with session.post(
            "https://discord.com/api/v10/users/@me/channels",
            headers=headers, json={"recipient_id": user_id}
        ) as r:
            if r.status != 200:
                print(f"DM channel creation failed: HTTP {r.status} - {await r.text()}")
                return
            dm = await r.json()
            print(f"DM channel created: {dm['id']}")
        async with session.post(
            f"https://discord.com/api/v10/channels/{dm['id']}/messages",
            headers=headers, json={"content": content}
        ) as r:
            if r.status != 200:
                print(f"DM send failed: HTTP {r.status} - {await r.text()}")
            else:
                print("DM sent successfully!")

@client.event
async def on_ready():
    print(f"Logged in as: {client.user}")
    if BOT_TOKEN:
        print("Bot DM notifications enabled")
    await client.fetch_private_channels()
    print("Listening for calls...")

@client.event
async def on_socket_raw_receive(data):
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            d = parsed.get("d")
            if not isinstance(d, dict):
                return
            event = parsed.get("t")
            ongoing = d.get("ongoing_rings", {})
            if not ongoing:
                return

            if event in ("CALL_CREATE", "CALL_UPDATE"):
                for ringee_id, ringer_id in ongoing.items():
                    if ringee_id == str(client.user.id):
                        name = await get_user_name(ringer_id)
                        print(f"\n{name} is ringing you! (ringer_id={ringer_id})")
                        await bot_dm(f"<@{ringer_id}> ({name}) is calling you! 🔔")
        except json.JSONDecodeError:
            pass

client.run(TOKEN)
