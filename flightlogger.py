import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Obtenemos el canal de logs y el rol desde el archivo .env
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
PILOT_ROLE_ID = int(os.getenv("PILOT_ROLE_ID"))

# Asegurar archivo JSON
if not os.path.exists("flights.json"):
    with open("flights.json", "w") as f:
        json.dump([], f)

class FlightLogView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(LogFlightButton())

class LogFlightButton(Button):
    def __init__(self):
        super().__init__(label="🛫 Log a Flight", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        if PILOT_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("You don't have permission to use this button.", ephemeral=True)
            return
        await interaction.response.send_message("Use the command: /logflight <flight_no> <duration> <aircraft> <dep> <arr> and attach a screenshot.", ephemeral=True)

@bot.command()
async def logflight(ctx, flight_number, flight_time, aircraft, departure_airport, arrival_airport):
    if PILOT_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("You don't have permission to use this command.")
        return

    if not ctx.message.attachments:
        await ctx.send("Please attach a screenshot.")
        return

    screenshot_url = ctx.message.attachments[0].url
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    embed = discord.Embed(title="✈️ Flight Logged", color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.add_field(name="Flight Number", value=flight_number, inline=True)
    embed.add_field(name="Duration", value=flight_time, inline=True)
    embed.add_field(name="Aircraft", value=aircraft, inline=True)
    embed.add_field(name="From → To", value=f"{departure_airport} → {arrival_airport}", inline=False)
    embed.add_field(name="Pilot", value=ctx.author.mention, inline=True)
    embed.set_image(url=screenshot_url)

    with open("flights.json", "r+") as f:
        data = json.load(f)
        data.append({
            "flight_number": flight_number,
            "flight_time": flight_time,
            "aircraft": aircraft,
            "departure": departure_airport,
            "arrival": arrival_airport,
            "pilot": ctx.author.id,
            "timestamp": now
        })
        f.seek(0)
        json.dump(data, f, indent=2)

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

    await ctx.send("Flight logged.")

@bot.command()
async def totalflights(ctx):
    with open("flights.json", "r") as f:
        flights = json.load(f)
    await ctx.send(f"Total logged flights: `{len(flights)}`")

@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Pilots, click below to log your flight:", view=FlightLogView())

bot.run(os.getenv("BOT_TOKEN"))