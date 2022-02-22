import os
import sys
import time
import json
import discord
import mariadb
import datetime
import requests
import traceback
import configparser
from PIL import Image
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
    # get all users who are going to be checked from the database in random order
    cursor.execute("SELECT * FROM users WHERE enabled = 1 ORDER BY RAND()")
    users_db = cursor.fetchall()

    cursor.execute("SELECT _key FROM config WHERE name = 'thresholds'")
    thresholds_db = cursor.fetchone()
    thresholds = thresholds_db[0].split(",")

    for user in users_db:
        date = datetime.datetime.now()
        print(date.strftime("%Y-%m-%d %H:%M:%S") + f" - checking user: {user}") ## debug print
        
        # create a gap between each API request as to avoid API rate limits (shouldn't be hitting them but i am ... so best to be on the safe side)
        # get the time the bot is going to be sleeping for
        cursor.execute("SELECT _key FROM config WHERE name = 'request_sleep'")
        between_user_asleep_int = cursor.fetchone()

        # sleep for the amount of time specified in the config file
        print(f"sleeping for {between_user_asleep_int[0]} seconds")
        time.sleep(int(between_user_asleep_int[0]))

        # if the user has just been added to the db then we need to add all their games to the DB
        if user[6] == "" or user[6] == None:
            date = datetime.datetime.now()
            print(date.strftime("%Y-%m-%d %H:%M:%S") + f" - setting up new user") ## debug print
            new_user(user[1])
            return

        # request each users details from the API
        print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  " - Sending API request")
        response = requests.get(f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_token}&steamid={user[1]}&format=json&include_played_free_games=True", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
        print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  f" - API Response: {response.status_code}")
        increment()
        
        json_data = json.loads(str(response.text))

        try:
            games = str(json_data['response']['game_count'])

            if int(games) > int(user[6]):
                await check_steams_users_games(json_data['response']['games'],str(user[1]))

                # update the users game count
                cursor.execute(f"UPDATE users SET games = {games} WHERE steam_id = '{user[1]}'")
                db.commit()

            if int(games) > 0:
                games = json_data['response']['games']

                for game in games:
                    cursor.execute(f"SELECT * FROM games WHERE appid = {game['appid']} AND steam_id = {str(user[1])}")
                    game_from_db = cursor.fetchone()

                    # if for whatever reason the game isn't in the DB, add it - this means for some reason the game count and the games in the DB are out of sync
                    if game_from_db == None:
                        print("adding game " + str(game['appid']) + " to DB")
                        cursor.execute("INSERT INTO games (appid, playtime_forever, playtime_windows_forever, playtime_mac_forever, playtime_linux_forever, steam_id) VALUES (%s, %s, %s, %s, %s, %s)", (game['appid'], game['playtime_forever'], game['playtime_windows_forever'], game['playtime_mac_forever'], game['playtime_linux_forever'], str(user[1])))
                        db.commit()
                    
                        cursor.execute(f"SELECT * FROM games WHERE appid = {game['appid']} AND steam_id = {str(user[1])}")
                        game_from_db = cursor.fetchone()

                    try:
                        # check game hours
                        await check_hours(game,game_from_db,thresholds)
                    except:
                        error_str = f"SteamID: {str(user[1])}\nAppID: {str(game['appid'])}\nGame = {str(game)}\nGame_from_db = {str(game_from_db)}"
                        await onError(error_str,str(user[0]))
                        traceback.print_exc()

        except:

            # get the column failed_attempts from the database where the steam_id is the same as the current user
            cursor.execute(f"SELECT failed_attempts FROM users WHERE steam_id = '{user[1]}'")

            # get the failed_attempts from the database
            failed_attempts = cursor.fetchone()

            # if the failed_attempts is greater than the max allowed attempts then disable the user
            if int(failed_attempts[0]) >= 2:
                cursor.execute(f"UPDATE users SET enabled = 0 WHERE steam_id = '{user[1]}'")
                db.commit()
                print("user disabled")

                # update the number of failed attempts to 0
                cursor.execute(f"UPDATE users SET failed_attempts = 0 WHERE steam_id = '{user[1]}'")
                db.commit()
            else:
                # increment the failed_attempts
                cursor.execute(f"UPDATE users SET failed_attempts = {int(failed_attempts[0])+1} WHERE steam_id = '{user[1]}'")
                db.commit()
                print("failed attempts incremented for user " + str(user[1]))

            # increment the value in the column failed_attempts in the database

              
async def check_hours(game,game_from_db,thresholds):

    # compare previously collected hours to the current hours to see if they have changed
    # 999999987 is the default value for when people have no hours, this avoids the issue of a bunch of notifications when someone changes their account from private to public
    
    #print("game['playtime_forever']" + str(game['playtime_forever']))
    #print("game_from_db[1]" + str(game_from_db[1]))

    if (int(game['playtime_forever']) != int(game_from_db[1])) and (int(game['playtime_forever']) != 0):

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
    response = requests.get(f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_token}&steamid={steam_id}&format=json&include_played_free_games=True", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
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

    sendmessage_bool = False
    game_names = []
    game_thumbs = []

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

            if user[2] == 1 or str(user[2]) == "1":
                
                sendmessage_bool = True

                # build and embed
                appid = game['appid']
                print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  " - Sending API request")
                response = requests.get(f"https://store.steampowered.com/api/appdetails?appids={game['appid']}&format=json", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
                print((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S") +  f" - API Response: {response.status_code}")

                increment()

                json_data = json.loads(str(response.text))

                gameinfo = json_data[f'{appid}']['data']

                game_names.append(gameinfo['name'])
                game_thumbs.append(gameinfo['header_image'])


                
                
            print(f"user {steam_id} has just got the game {game['appid']}")
    
    if sendmessage_bool == True:
        
        cursor.execute(f"SELECT _key FROM config WHERE name = 'achievement_channel'")
        channel_id = cursor.fetchone()

        userValue = await bot.fetch_user(int(user[0]))


        if len(game_names) == 1:
            description = f"<@!{str(user[0])}> has just got the game:\n"
            title = "New game!"
        else:
            description = f"<@!{str(user[0])}> has just got the games:\n"
            title = "New games!"
            merge_images(game_thumbs)
            
        for game_name in game_names:
            description += f"{game_name}\n"

        embed = discord.Embed(title=title, description=description, color=0x00ff00)
        embed.set_author(name=f"{userValue.name}", icon_url=f"{userValue.avatar_url}")


        if len(game_names) == 1:
            embed.set_thumbnail(url=game_thumbs[0])
            await bot.get_channel(int(channel_id[0])).send(embed=embed)
        else:
            file = discord.File("result.jpeg", filename="image.jpeg")
            embed.set_thumbnail(url="attachment://image.jpeg")
            await bot.get_channel(int(channel_id[0])).send(file=file, embed=embed)

def increment():
    # increase the count of API requests
    cursor.execute("SELECT _key FROM config WHERE name = 'queries'")
    count = cursor.fetchone()
    count = int(count[0]) + 1

    cursor.execute(f"UPDATE config SET _key = {count} WHERE name = 'queries'")
    db.commit()

def merge_images(list):

    i = 0
    result_width = 0
    result_height = 0

    for url in list:
        img_data = requests.get(url).content
        with open(f'image_name{i}.jpeg', 'wb') as handler:
            handler.write(img_data)
        result_width = max(result_width, Image.open(f'image_name{i}.jpeg').size[0])
        result_height += Image.open(f'image_name{i}.jpeg').size[1]
        i += 1
    
    if len(list) >= 4 and len(list) % 2 == 0:
        height = 0

        result = Image.new('RGB', (result_width*2, int(result_height/2)))
        for i in range(0, len(list), 2):
            img1 = Image.open(f'image_name{i}.jpeg')
            img2 = Image.open(f'image_name{i+1}.jpeg')
            result.paste(img1, (0, height))
            result.paste(img2, (result_width, height))
            height += img1.size[1]
    elif len(list) >= 4 and len(list) % 2 != 0:
        height = 0

        result = Image.new('RGB', (result_width*2, int((result_height/2) + (result_height/len(list)/2))))
        for i in range(0, len(list), 2):
            if i != len(list) - 1:
                img1 = Image.open(f'image_name{i}.jpeg')
                img2 = Image.open(f'image_name{i+1}.jpeg')
                result.paste(img1, (0, height))
                result.paste(img2, (result_width, height))
                height += img1.size[1]
            else:
                img1 = Image.open(f'image_name{i}.jpeg')
                img2 = Image.open('default.jpeg')
                result.paste(img1, (0, height))
                result.paste(img2, (result_width, height))
                break

    else:
        result = Image.new('RGB', (result_width, result_height))
        for i in range(len(list)):
            img = Image.open(f'image_name{i}.jpeg')
            result.paste(img, (0, i * img.size[1]))

    # delete all the images
    for i in range(len(list)):
        os.remove(f'image_name{i}.jpeg')

    print("Merged and saved images")
    # save the image
    result.save('result.jpeg')

async def onError(error,user_id):
    
    #get get debug channel from db
    cursor.execute("SELECT _key FROM config WHERE name = ?",("debug_channel",))
    channel_id = cursor.fetchone()


    channel = bot.get_channel(int(channel_id[0]))

    unix_time = time.time()
    time_to_int = round(unix_time,0)


    print(f"\n\n[{time_to_int}] - Guild ID: " + str(user_id))
    print("Error: " + str(error) + "\n")
    await channel.send("<t:" + str(int(time_to_int)) +":F> for user (DiscordID): " + str(user_id) +":\n" + str(error))

bot.run(bot_token)