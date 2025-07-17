import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

FLIGHTS_FILE = 'flights.json'

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# Comando para registrar un vuelo
@bot.command()
async def logflight(ctx):
    pilot_role_id = int(os.getenv("PILOT_ROLE_ID"))
    if pilot_role_id not in [role.id for role in ctx.author.roles]:
        return await ctx.send("You don't have permission to use this command.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send("Enter flight number:")
    flight_number = (await bot.wait_for('message', check=check)).content

    await ctx.send("Enter flight time:")
    flight_time = (await bot.wait_for('message', check=check)).content

    await ctx.send("Enter aircraft:")
    aircraft = (await bot.wait_for('message', check=check)).content

    await ctx.send("Enter departure airport:")
    departure = (await bot.wait_for('message', check=check)).content

    await ctx.send("Enter arrival airport:")
    arrival = (await bot.wait_for('message', check=check)).content

    await ctx.send("Now upload a screenshot:")
    msg = await bot.wait_for('message', check=check)
    if not msg.attachments:
        return await ctx.send("You didn't upload a screenshot.")
    screenshot_url = msg.attachments[0].url

    new_flight = {
        "pilot": str(ctx.author),
        "flight_number": flight_number,
        "flight_time": flight_time,
        "aircraft": aircraft,
        "departure": departure,
        "arrival": arrival,
        "screenshot": screenshot_url
    }

    try:
        with open(FLIGHTS_FILE, 'r') as f:
            flights = json.load(f)
    except FileNotFoundError:
        flights = []

    flights.append(new_flight)

    with open(FLIGHTS_FILE, 'w') as f:
        json.dump(flights, f, indent=4)

    log_channel_id = int(os.getenv("LOG_CHANNEL_ID"))
    log_channel = bot.get_channel(log_channel_id)

    embed = discord.Embed(title="✈️ New Flight Logged", color=0x1D82B6)
    embed.add_field(name="Flight Number", value=flight_number, inline=True)
    embed.add_field(name="Flight Time", value=flight_time, inline=True)
    embed.add_field(name="Aircraft", value=aircraft, inline=True)
    embed.add_field(name="From", value=departure, inline=True)
    embed.add_field(name="To", value=arrival, inline=True)
    embed.add_field(name="Pilot", value=str(ctx.author), inline=False)
    embed.set_image(url=screenshot_url)
    await log_channel.send(embed=embed)
    await ctx.send("✅ Flight logged successfully!")

# Comando para mostrar número total de vuelos
@bot.command()
async def totalflights(ctx):
    try:
        with open(FLIGHTS_FILE, 'r') as f:
            flights = json.load(f)
        total = len(flights)
    except FileNotFoundError:
        total = 0

    await ctx.send(f"📊 Total flights logged: {total}")

# Comando para editar un vuelo por ID
@bot.command()
async def editflight(ctx, flight_id: int):
    staff_roles = [int(rid) for rid in os.getenv("STAFF_ROLE_IDS").split(",")]
    if not any(role.id in staff_roles for role in ctx.author.roles):
        return await ctx.send("You don't have permission to edit flights.")

    try:
        with open(FLIGHTS_FILE, 'r') as f:
            flights = json.load(f)
    except FileNotFoundError:
        return await ctx.send("No flights logged yet.")

    if flight_id < 1 or flight_id > len(flights):
        return await ctx.send("Invalid flight ID.")

    flight = flights[flight_id - 1]
    def check(m): return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send("Enter new flight number (or type '-' to skip):")
    new_number = (await bot.wait_for('message', check=check)).content
    if new_number != "-": flight['flight_number'] = new_number

    await ctx.send("Enter new flight time (or type '-' to skip):")
    new_time = (await bot.wait_for('message', check=check)).content
    if new_time != "-": flight['flight_time'] = new_time

    await ctx.send("Enter new aircraft (or type '-' to skip):")
    new_aircraft = (await bot.wait_for('message', check=check)).content
    if new_aircraft != "-": flight['aircraft'] = new_aircraft

    await ctx.send("Enter new departure airport (or type '-' to skip):")
    new_departure = (await bot.wait_for('message', check=check)).content
    if new_departure != "-": flight['departure'] = new_departure

    await ctx.send("Enter new arrival airport (or type '-' to skip):")
    new_arrival = (await bot.wait_for('message', check=check)).content
    if new_arrival != "-": flight['arrival'] = new_arrival

    await ctx.send("Upload new screenshot (or type '-' to skip):")
    msg = await bot.wait_for('message', check=check)
    if msg.content != "-" and msg.attachments:
        flight['screenshot'] = msg.attachments[0].url

    with open(FLIGHTS_FILE, 'w') as f:
        json.dump(flights, f, indent=4)

    await ctx.send(f"✅ Flight #{flight_id} updated successfully.")

# Comando para eliminar un vuelo por ID
@bot.command()
async def deleteflight(ctx, flight_id: int):
    staff_roles = [int(rid) for rid in os.getenv("STAFF_ROLE_IDS").split(",")]
    if not any(role.id in staff_roles for role in ctx.author.roles):
        return await ctx.send("You don't have permission to delete flights.")

    try:
        with open(FLIGHTS_FILE, 'r') as f:
            flights = json.load(f)
    except FileNotFoundError:
        return await ctx.send("No flights logged yet.")

    if flight_id < 1 or flight_id > len(flights):
        return await ctx.send("Invalid flight ID.")

    flights.pop(flight_id - 1)
    with open(FLIGHTS_FILE, 'w') as f:
        json.dump(flights, f, indent=4)

    await ctx.send(f"🗑️ Flight #{flight_id} has been deleted.")
    from keep_alive import keep_alive

# Inicia servidor web para que Render mantenga vivo el bot
keep_alive()

# Inicia el bot
bot.run(os.getenv("BOT_TOKEN"))
