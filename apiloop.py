import os
import sys
import time
import json
import discord
import mariadb
import datetime
import requests
import configparser
from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext
from discord_slash.context import MenuContext
from discord_slash.model import ContextMenuType
from discord_slash.utils.manage_commands import create_option

guild_ids_lst = [713068366419722300,682542511797043207]

config = configparser.ConfigParser()

if os.path.exists('config.ini') == False:
    config['DEFAULT'] = {'bot_token': '123xyz','steam_api_key': '123xyz'}
    config['DATABASE'] = {'db_username': 'defaultusername','db_password': 'defaultpassword','db_ip': 'dbip','db_port': '3306'}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    
    print("Please go to config.ini and enter your bots details and preferences")
    exit()

config.read('config.ini')

bot_token = config['DEFAULT']['bot_token']
steam_token = config['DEFAULT']['steam_api_key']

db_username = config['DATABASE']['db_username']
db_password = config['DATABASE']['db_password']
db_ip = config['DATABASE']['db_ip']
db_port = int(config['DATABASE']['db_port'])

# Connect to MariaDB Platform
try:
    db = mariadb.connect(
        user=db_username,
        password=db_password,
        host=db_ip,
        port=db_port,
        database="Charlies_AI"
    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

# Get Cursor
cursor = db.cursor()

bot = Client(intents=Intents.default())
slash = SlashCommand(bot,sync_commands=True)

@bot.event
async def on_ready():
    print("Logged in as " + str(bot.user))
    print("User ID: " + str(bot.user.id))
    print("API module")

    ## for loop to check APIS
    ## infinte loop
    while True:
        # get the time the bot is going to be sleeping for
        cursor.execute("SELECT _key FROM config WHERE name = 'sleep'")
        asleep_int = cursor.fetchone()
        time.sleep(int(asleep_int[0]))
        date = datetime.datetime.now()
        print(date.strftime("%Y-%m-%d %H:%M:%S") + " - Beginning Process") ## debug print

        # check if the loop is active or not
        cursor.execute("SELECT _key FROM config WHERE name = 'active'")
        active_boo = cursor.fetchone()

        if active_boo[0].lower() == "true":
            await get_steam_users()

async def get_steam_users():
    # get all users who are going to be checked from the database
    cursor.execute("SELECT * FROM users WHERE enabled = 1")
    users_db = cursor.fetchall()

    cursor.execute("SELECT _key FROM config WHERE name = 'thresholds'")
    thresholds_db = cursor.fetchone()
    thresholds = thresholds_db[0].split(",")

    for user in users_db:

        date = datetime.datetime.now()
        print(date.strftime("%Y-%m-%d %H:%M:%S") + f" - checking user: {user}") ## debug print
        
        # if the user has just been added to the db then we need to add all their games to the DB
        if user[6] == "" or user[6] == None:
            date = datetime.datetime.now()
            print(date.strftime("%Y-%m-%d %H:%M:%S") + f" - setting up new user") ## debug print
            new_user(user[1])
            return

        # request each users details from the API
        print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  " - Sending API request")
        response = requests.get(f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_token}&steamid={user[1]}&format=json", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
        print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  f" - API Response: {response.status_code}")
        increment()
        
        json_data = json.loads(str(response.text))

        try:
            games = str(json_data['response']['game_count'])

            if games != str(user[6]):
                await check_steams_users_games(json_data['response']['games'],str(user[1]))

            if int(games) > 0:
                games = json_data['response']['games']

                for game in games:
                    cursor.execute(f"SELECT * FROM games WHERE appid = {game['appid']} AND steam_id = {str(user[1])}")
                    game_from_db = cursor.fetchone()

                    # check game hours
                    await check_hours(game,game_from_db,thresholds)
        except:
            print("Error")            

async def check_hours(game,game_from_db,thresholds):

    # compare previously collected hours to the current hours to see if they have changed
    # 999999987 is the default value for when people have no hours, this avoids the issue of a bunch of notifications when someone changes their account from private to public
    if (int(game['playtime_forever']) != int(game_from_db[1])) and (int(game['playtime_forever']) != 999999987):

        print(f"{game_from_db[5]} has gained time in: {game['appid']} ({str(game_from_db[1])} to {str(game['playtime_forever'])})")

        # update the database if they have changed
        cursor.execute(f"UPDATE games SET playtime_forever = {game['playtime_forever']}, playtime_windows_forever = {game['playtime_windows_forever']}, playtime_mac_forever = {game['playtime_mac_forever']}, playtime_linux_forever = {game['playtime_linux_forever']} WHERE appid = {game['appid']} AND steam_id = {game_from_db[5]}")
        db.commit()

        # check if the user has passed one of the hours thresholds
        for threshold in thresholds:
            if int(game['playtime_forever']) >= int(threshold) and int(game_from_db[1]) < int(threshold):

                cursor.execute(f"SELECT * FROM users WHERE steam_id = {game_from_db[5]}")
                user = cursor.fetchone()

                if user[4] == 1:
                    print(f"{user[5]} has passed {threshold} hours in {game['appid']}")
                    # build and embed
                    appid = game['appid']
                    print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  " - Sending API request")
                    response = requests.get(f"https://store.steampowered.com/api/appdetails?appids={game['appid']}&format=json", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
                    print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  f" - API Response: {response.status_code}")

                    increment()

                    json_data = json.loads(str(response.text))

                    gameinfo = json_data[f'{appid}']['data']

                    cursor.execute(f"SELECT _key FROM config WHERE name = 'achievement_channel'")
                    channel_id = cursor.fetchone()
                 
                    embed = discord.Embed(title=f"Time Achievement!", description=f"<@!{str(user[0])}> has passed {str(int(int(threshold)/60))} hours in {gameinfo['name']}", color=0x00ff00)
                    # set the author
                    # get discord users avatar
                    userValue = await bot.fetch_user(int(user[0]))
                    embed.set_author(name=f"{userValue.name}", icon_url=f"{userValue.avatar_url}")
                    embed.set_thumbnail(url=gameinfo['header_image'])
                    await bot.get_channel(int(channel_id[0])).send(embed=embed)
            
def new_user(steam_id):
    print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  " - Sending API request")
    response = requests.get(f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_token}&steamid={steam_id}&format=json", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
    print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  f" - API Response: {response.status_code}")

    increment()

    # format the response
    json_data = json.loads(str(response.text))

    games = str(json_data['response']['game_count'])
    print(f"adding {str(games)} of user {steam_id}'s games to the database ")

    # update the users game count
    cursor.execute(f"UPDATE users SET games = {games} WHERE steam_id = {steam_id}")
    db.commit()

    # if the user has games then we need to add them to the database
    if int(games) > 0:
        # find each of the games
        games = json_data['response']['games']

        # for each game add it to the database
        for game in games:
            
            if int(game['playtime_forever']) == 0:
                playtime_forever = 999999987
            else:
                playtime_forever = game['playtime_forever']
            cursor.execute("INSERT INTO games (appid, playtime_forever, playtime_windows_forever, playtime_mac_forever, playtime_linux_forever, steam_id) VALUES (%s, %s, %s, %s, %s, %s)", (game['appid'], playtime_forever, game['playtime_windows_forever'], game['playtime_mac_forever'], game['playtime_linux_forever'], steam_id))
            db.commit()

async def check_steams_users_games(games,steam_id):
    cursor.execute(f"SELECT * FROM games WHERE steam_id = '{steam_id}'")
    games_db = cursor.fetchall()

    for game in games:
        
        found_bool = False

        for game_db in games_db:

            if str(game['appid']) == str(game_db[0]):
                found_bool = True
                break
        
        if found_bool == False:
            print("adding game " + str(game['appid']) + " to DB")
            cursor.execute("INSERT INTO games (appid, playtime_forever, playtime_windows_forever, playtime_mac_forever, playtime_linux_forever, steam_id) VALUES (%s, %s, %s, %s, %s, %s)", (game['appid'], game['playtime_forever'], game['playtime_windows_forever'], game['playtime_mac_forever'], game['playtime_linux_forever'], steam_id))
            db.commit()

            cursor.execute(f"SELECT * FROM users WHERE steam_id = {steam_id}")
            user = cursor.fetchone()

            # build and embed
            appid = game['appid']
            print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  " - Sending API request")
            response = requests.get(f"https://store.steampowered.com/api/appdetails?appids={game['appid']}&format=json", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
            print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  f" - API Response: {response.status_code}")

            increment()

            json_data = json.loads(str(response.text))

            gameinfo = json_data[f'{appid}']['data']

            cursor.execute(f"SELECT _key FROM config WHERE name = 'achievement_channel'")
            channel_id = cursor.fetchone()
            
            embed = discord.Embed(title=f"New game!", description=f"<@!{str(user[0])}> has just got the game: {gameinfo['name']}", color=0x00ff00)
            # set the author
            # get discord users avatar
            userValue = await bot.fetch_user(int(user[0]))
            embed.set_author(name=f"{userValue.name}", icon_url=f"{userValue.avatar_url}")
            embed.set_thumbnail(url=gameinfo['header_image'])
            await bot.get_channel(int(channel_id[0])).send(embed=embed)

            print(f"user {steam_id} has just got the game {game['appid']}")

def increment():
    # increase the count of API requests
    cursor.execute("SELECT _key FROM config WHERE name = 'queries'")
    count = cursor.fetchone()
    count = int(count[0]) + 1

    cursor.execute(f"UPDATE config SET _key = {count} WHERE name = 'queries'")
    db.commit()
        

bot.run(bot_token)