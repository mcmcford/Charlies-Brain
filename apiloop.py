import os
import sys
import time
import json
import discord
import mariadb
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

        # check if the loop is active or not
        cursor.execute("SELECT _key FROM config WHERE name = 'active'")
        active_boo = cursor.fetchone()
        print("active_boo[0] = " + str(active_boo[0]))
        if active_boo[0].lower() == "true":
            get_steam_users()

def get_steam_users():
    # get all users who are going to be checked from the database
    cursor.execute("SELECT * FROM users WHERE enabled = 1")
    users_db = cursor.fetchall()

    print("users_db = " + str(users_db))

    cursor.execute("SELECT _key FROM config WHERE name = 'thresholds'")
    thresholds_db = cursor.fetchone()
    thresholds = thresholds_db[0].split(",")

    for user in users_db:
        
        # if the user has just been added to the db then we need to add all their games to the DB
        if user[6] == "" or user[6] == None:
            new_user(user[1])
            return

        print("steam_token = " + steam_token)
        print("user[1] = " + str(user[1]))

        # request each users details from the API
        response = requests.get(f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_token}&steamid={user[1]}&format=json", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
        print("response = " + str(response))
        
        json_data = json.loads(str(response.text))

        games = str(json_data['response']['game_count'])
        print("games = " + str(games))

        if games != str(user[6]):
            print("user has new game")
            pass # go the a method to find the users new game(s)

        if int(games) > 0:
            games = json_data['response']['games']

            for game in games:
                cursor.execute(f"SELECT * FROM games WHERE appid = {game['appid']} AND steam_id = {str(user[1])}")
                game_from_db = cursor.fetchone()

                # check game hours
                check_hours(game,game_from_db,thresholds)


def check_hours(game,game_from_db,thresholds):
    
    # compare previously collected hours to the current hours to see if they have changed
    if int(game['playtime_forever']) != int(game_from_db[1]):

        print(f"{game_from_db[5]} has gained hours in: {game['appid']}")

        # update the database if they have changed
        cursor.execute(f"UPDATE games SET playtime_forever = {game['playtime_forever']}, playtime_windows_forever = {game['playtime_windows_forever']}, playtime_mac_forever = {game['playtime_mac_forever']}, playtime_linux_forever = {game['playtime_linux_forever']} WHERE appid = {game['appid']} AND steam_id = {game_from_db[5]}")
        db.commit()

        # check if the user has passed one of the hours thresholds
        for threshold in thresholds:
            if int(game['playtime_forever']) >= int(threshold) and int(game_from_db[1]) < int(threshold):
                print("user has passed threshold")
                pass



            
def new_user(steam_id):
    response = requests.get(f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_token}&steamid={steam_id}&format=json", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
    print("response = " + str(response))

    # format the response
    json_data = json.loads(str(response.text))

    games = str(json_data['response']['game_count'])
    print("games = " + str(games))

    # update the users game count
    cursor.execute(f"UPDATE users SET games = {games} WHERE steam_id = {steam_id}")
    db.commit()

    # if the user has games then we need to add them to the database
    if int(games) > 0:
        # find each of the games
        games = json_data['response']['games']

        # for each game add it to the database
        for game in games:
            
            print("adding game " + str(game['appid']) + " to DB")
            cursor.execute("INSERT INTO games (appid, playtime_forever, playtime_windows_forever, playtime_mac_forever, playtime_linux_forever, steam_id) VALUES (%s, %s, %s, %s, %s, %s)", (game['appid'], game['playtime_forever'], game['playtime_windows_forever'], game['playtime_mac_forever'], game['playtime_linux_forever'], steam_id))
            db.commit()

def check_steams_users_games():
    cursor.execute("SELECT * FROM users WHERE new_game_notif = 1")
    active_boo = cursor.fetchone()

        


bot.run(bot_token)



