import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
PILOT_ROLE_ID = int(os.getenv("PILOT_ROLE_ID"))
STAFF_ROLE_IDS = list(map(int, os.getenv("STAFF_ROLE_IDS").split(",")))

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.guild_messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

@tree.command(name="logflight", description="Log a flight")
@app_commands.describe(
    flight_number="Flight number",
    flight_time="Flight duration",
    aircraft="Aircraft used",
    departure="Departure airport",
    arrival="Arrival airport",
    screenshot="Screenshot of the flight"
)
async def logflight(interaction: discord.Interaction, flight_number: str, flight_time: str, aircraft: str, departure: str, arrival: str, screenshot: discord.Attachment):
    user_roles = [role.id for role in interaction.user.roles]
    if PILOT_ROLE_ID not in user_roles:
        await interaction.response.send_message("You are not authorized to log flights.", ephemeral=True)
        return

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        await interaction.response.send_message("Log channel not found.", ephemeral=True)
        return

    embed = discord.Embed(title="Flight Logged", color=discord.Color.green())
    embed.add_field(name="Flight Number", value=flight_number, inline=True)
    embed.add_field(name="Flight Time", value=flight_time, inline=True)
    embed.add_field(name="Aircraft", value=aircraft, inline=True)
    embed.add_field(name="Departure", value=departure, inline=True)
    embed.add_field(name="Arrival", value=arrival, inline=True)
    embed.set_image(url=screenshot.url)
    embed.set_footer(text=f"Logged by {interaction.user.name} ({interaction.user.id})")

    await log_channel.send(embed=embed)

    new_flight = {
        "flight_number": flight_number,
        "flight_time": flight_time,
        "aircraft": aircraft,
        "departure": departure,
        "arrival": arrival,
        "user_id": interaction.user.id
    }

    if not os.path.exists("flights.json"):
        with open("flights.json", "w") as f:
            json.dump([], f)

    with open("flights.json", "r") as f:
        flights = json.load(f)

    flights.append(new_flight)

    with open("flights.json", "w") as f:
        json.dump(flights, f, indent=4)

    await interaction.response.send_message("Flight logged successfully!", ephemeral=True)

@tree.command(name="flights", description="Show all logged flights")
async def flights(interaction: discord.Interaction):
    with open("flights.json", "r") as f:
        flights = json.load(f)

    if not flights:
        await interaction.response.send_message("No flights logged yet.", ephemeral=True)
        return

    embed = discord.Embed(title="Logged Flights", color=discord.Color.blue())

    for flight in flights[-10:]:
        embed.add_field(
            name=f"Flight {flight['flight_number']} ({flight['aircraft']})",
            value=f"From {flight['departure']} to {flight['arrival']}\nTime: {flight['flight_time']}\n<@{flight['user_id']}>",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@tree.command(name="deleteflight", description="Delete a flight by number")
@app_commands.describe(flight_number="Flight number to delete")
async def deleteflight(interaction: discord.Interaction, flight_number: str):
    if not any(role.id in STAFF_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    with open("flights.json", "r") as f:
        flights = json.load(f)

    updated_flights = [f for f in flights if f["flight_number"] != flight_number]

    if len(updated_flights) == len(flights):
        await interaction.response.send_message(f"No flight found with number {flight_number}.", ephemeral=True)
        return

    with open("flights.json", "w") as f:
        json.dump(updated_flights, f, indent=4)

    await interaction.response.send_message(f"Flight {flight_number} deleted.", ephemeral=True)

bot.run(BOT_TOKEN)