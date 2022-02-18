from http.client import responses
import os
from re import S
import sys
import json
import datetime
import discord
import requests
import mariadb
import configparser
import random as rand
from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext
from discord_slash.context import InteractionContext, MenuContext
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

db_username = config['DATABASE']['db_username']
db_password = config['DATABASE']['db_password']
db_ip = config['DATABASE']['db_ip']
db_port = int(config['DATABASE']['db_port'])

class connect():
    def __init__(self):
        # Connect to MariaDB Platform
        try:
            self.db = mariadb.connect(
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
        self.cursor = self.db.cursor()

def disconnect(database):
    # Disconnect from MariaDB Platform
    cur = database.cursor
    d = database.db
    cur.close()
    d.close()


bot = Client(intents=Intents.default())
slash = SlashCommand(bot,sync_commands=True)

@bot.event
async def on_ready():
    print("Logged in as " + str(bot.user))
    print("User ID: " + str(bot.user.id))
    print("Command module")

    await bot.change_presence(activity=discord.Game(name="if you see me - no you dont"))


@slash.slash(name="poll",description="Create a reaction poll!",
    options=[
        create_option(
            name="title",
            description="Title of the poll",
            option_type=3,
            required=True),
        create_option(
            name="multiple_choice",
            description="True or False on whether this is multiple choice or not",
            option_type=5,
            required=True),
        create_option(
            name="option_one",
            description="Option One in the poll",
            option_type=3,
            required=True),
        create_option(
            name="option_two",
            description="Option Two in the poll",
            option_type=3,
            required=True),
        create_option(
            name="option_three",
            description="Option Three in the poll",
            option_type=3,
            required=False),
        create_option(
            name="option_four",
            description="Option Four in the poll",
            option_type=3,
            required=False),
        create_option(
            name="option_five",
            description="Option Five in the poll",
            option_type=3,
            required=False),
        create_option(
            name="option_six",
            description="Option Six in the poll",
            option_type=3,
            required=False),
        create_option(
            name="option_seven",
            description="Option Seven in the poll",
            option_type=3,
            required=False),
        create_option(
            name="option_eight",
            description="Option Eight in the poll",
            option_type=3,
            required=False),
        create_option(
            name="option_nine",
            description="Option Nine in the poll",
            option_type=3,
            required=False),
        create_option(
            name="option_ten",
            description="Option Ten in the poll",
            option_type=3,
            required=False)
        ],
    guild_ids=guild_ids_lst)
# the reason some of these are declared as a random string is to ensure the command suceeds (no null pass overs) and the user likely wont use that string in a poll
async def _poll(ctx, title, option_one, option_two, option_three = "DefString12083", option_four = "DefString12083", option_five = "DefString12083", option_six = "DefString12083", option_seven = "DefString12083", option_eight = "DefString12083", option_nine = "DefString12083", option_ten = "DefString12083", multiple_choice = False):
    
    database = connect()
    cur = database.cursor
    d = database.db

    print(f"Info:\ntitle: {title}")
    print(f"multiple choice: {multiple_choice}")
    print(f"option1: {option_one}")
    print(f"option2: {option_two}")
    print(f"option3: {option_three}")
    print(f"option4: {option_four}")
    print(f"option5: {option_five}")
    print(f"option6: {option_six}")
    print(f"option7: {option_seven}")
    print(f"option8: {option_eight}")
    print(f"option9: {option_nine}")
    print(f"option10: {option_ten}")

    # compile into list and set default values to null
    list = [option_one, option_two, option_three, option_four, option_five, option_six, option_seven, option_eight, option_nine, option_ten]
    emojis = [":zero:",":one:",":two:",":three:",":four:",":five:",":six:",":seven:",":eight:",":nine:"]
    emojis_unicode = ['0\u20e3','1\u20e3','2\u20e3','3\u20e3','4\u20e3','5\u20e3','6\u20e3','7\u20e3','8\u20e3','9\u20e3']
    Description = ""
    interations = 0

    for i in list:
        if i == "DefString12083":
            # set value to = ""
            list[list.index(i)] = ""
        else:
            Description = Description + f"{emojis[interations]} {i}\n"
            interations = interations + 1

    embed = discord.Embed(title=f"{title}", description=Description, color=discord.Color.blue())

    #get an ID for the poll by querying the database and incrementing the ID by 1
    cur.execute("SELECT count(*) FROM Polls")
    find = cur.fetchone()[0]

    id = str(find).zfill(7)

    print(f"ID: {id}")

    if multiple_choice == True:
        embed.set_footer(text=f"You can vote for multiple options • ID: {id}")
    else:
        embed.set_footer(text=f"Only vote for one option! if you have multiple votes by the end of the poll, your votes won't be counted • ID: {id}")

    message = await ctx.send(embed=embed)

    cur.execute("INSERT INTO Polls (message_id, title, opt1, opt2, opt3, opt4, opt5, opt6, opt7, opt8, opt9, opt10, multi, poll_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (message.id, title, list[0], list[1], list[2], list[3], list[4], list[5], list[6], list[7], list[8], list[9], multiple_choice, id))
    d.commit()

    for x in range(interations):
        if x == 0:
            emoji = '0\u20e3'
            await ctx.message.add_reaction(emoji)
        elif x == 1:
            emoji = '1\u20e3'
            await ctx.message.add_reaction(emoji)
        elif x == 2:
            emoji = '2\u20e3'
            await ctx.message.add_reaction(emoji)
        elif x == 3:
            emoji = '3\u20e3'
            await ctx.message.add_reaction(emoji)
        elif x == 4:
            emoji = '4\u20e3'
            await ctx.message.add_reaction(emoji)
        elif x == 5:
            emoji = '5\u20e3'
            await ctx.message.add_reaction(emoji)
        elif x == 6:
            emoji = '6\u20e3'
            await ctx.message.add_reaction(emoji)
        elif x == 7:
            emoji = '7\u20e3'
            await ctx.message.add_reaction(emoji)
        elif x == 8:
            emoji = '8\u20e3'
            await ctx.message.add_reaction(emoji)
        elif x == 9:
            emoji = '9\u20e3'
            await ctx.message.add_reaction(emoji)

    disconnect(database)


@slash.slash(name="endpoll",description="Ends a poll", options=[create_option(
            name="poll_id",
            description="The ID of the poll you would like to end",
            option_type=3,
            required=True)], guild_ids=guild_ids_lst) 
async def _endpoll(ctx, poll_id = 0):
    print(f"Info:\npoll_id: {poll_id}")

    database = connect()
    cursor = database.cursor
    db = database.db

    cursor.execute("SELECT * FROM Polls WHERE poll_id = %s", (poll_id,))
    poll = cursor.fetchone()

    if poll == None:
        await ctx.send("That poll doesn't exist")
        return
    
    if "End1221:" in str(poll[1]):
        await ctx.send("That poll has already been ended")
        return

    channel = bot.get_channel(ctx.channel.id)
    msg = await channel.fetch_message(int(poll[0]))
            
    reactions = msg.reactions

    temp = []

    for reaction in reactions:
        temp.append([reaction.count,""])

    i = 0
    for x in range(12):
        if x < 2 or x > 12:
            pass
        else:
            if poll[x] != "":
                temp[i][1] = poll[x]
                i = i + 1

    temp.sort(reverse=True)

    description = "**"
    y = 0
    for x in range(len(temp)):
        description = description + f"{temp[x][0]} - {temp[x][1]}"

        if y == 0:
            description = description + "**\n"
            y = 1
        else:
            description = description + "\n"
    
    print(description)

    embed = discord.Embed(title=f"{poll[1]}", description=description, color=discord.Color.red())
    embed.set_footer(text=f"Poll ended @ {datetime.datetime.now()} • ID: {poll_id}")
    await ctx.send(embed=embed)

    rename = "End1221:" + poll[1]
    cursor.execute("UPDATE Polls SET title = %s WHERE poll_id = %s", (rename, poll_id))
    db.commit()

    disconnect(database)

@slash.slash(name="toggle_new_game_notifications",description="Enable / Disable notifications in discord when you get a new game", options=[create_option(
            name="toggle",
            description="Enable / Disable notifications in discord when you get a new game",
            option_type=5,
            required=True)], guild_ids=guild_ids_lst) 
async def _toggle_new_game_notifications(ctx,toggle: bool):

    database = connect()
    cursor = database.cursor
    db = database.db

    cursor.execute(f"SELECT new_game_notif FROM users WHERE discord_id = '{ctx.author.id}'")
    new_game_notif = cursor.fetchone()[0]

    if new_game_notif == 1 and toggle == True:
        await ctx.send("You already have notifications enabled")
        disconnect(database)
        return
    elif new_game_notif == 0 and toggle == False:
        await ctx.send("You already have notifications disabled")
        disconnect(database)
        return

    if toggle == True:
        cursor.execute("UPDATE users SET new_game_notif = %s WHERE discord_id = %s", (1, ctx.author.id))
        db.commit()

        await ctx.send("Notifications will now be posted when you get a new game")

    elif toggle == False:
        cursor.execute("UPDATE users SET new_game_notif = %s WHERE discord_id = %s", (0, ctx.author.id))
        db.commit()
        
        await ctx.send("Notifications will no longer be posted when you get a new game")

    disconnect(database)

    
@slash.slash(name="toggle_hours_notifications",description="Enable / Disable notifications in discord when you achieve a certain amount of hours in a game", options=[create_option(
            name="toggle",
            description="Enable / Disable notifications in discord when you get pass an hours freshhold in a game",
            option_type=5,
            required=True)], guild_ids=guild_ids_lst) 
async def _toggle_hours_notifications(ctx,toggle: bool):

    database = connect()
    cursor = database.cursor
    db = database.db

    cursor.execute(f"SELECT game_hours_notif FROM users WHERE discord_id = '{ctx.author.id}'")
    new_game_notif = cursor.fetchone()[0]

    if new_game_notif == 1 and toggle == True:
        await ctx.send("You already have notifications enabled")
        disconnect(database)
        return
    elif new_game_notif == 0 and toggle == False:
        await ctx.send("You already have notifications disabled")
        disconnect(database)
        return

    if toggle == True:
        cursor.execute("UPDATE users SET game_hours_notif = %s WHERE discord_id = %s", (1, ctx.author.id))
        db.commit()

        await ctx.send("Notifications will now be posted when you get a new game")

    elif toggle == False:
        cursor.execute("UPDATE users SET game_hours_notif = %s WHERE discord_id = %s", (0, ctx.author.id))
        db.commit()
        
        await ctx.send("Notifications will no longer be posted when you get a new game")

    disconnect(database)

@slash.slash(name="gamestats",description="Get your hour stats in games", options=[create_option(
            name="user_id",
            description="The @mention or user ID of the user you would like to get stats for",
            option_type=3,
            required=False)], guild_ids=guild_ids_lst) 
async def _gamestats(ctx, user_id = None):
        
    # clean the user id
    if user_id == None:
        user_id = ctx.author.id
    else:
        user_id = user_id.replace("<","").replace(">","").replace("@","").replace("!","").replace("#","").replace("&","").replace(" ","")

    database = connect()
    cursor = database.cursor
    db = database.db

    #get the users steam_id from the users table using their discord_id
    cursor.execute("SELECT steam_id FROM users WHERE discord_id = ?", (user_id,))
    
    try:
        steam_id = cursor.fetchone()[0]
        await ctx.send(f"Generating report now =)")
    except:
        await ctx.send(f"Looks like the user {user_id} isn't in the system yet")
        disconnect(database)
        return


    # get the users 'playtime_forever' from the games table using their steam_id,  ignoring any rows where the playtime_forever is 999999987
    cursor.execute("SELECT playtime_forever FROM games WHERE steam_id = ? AND playtime_forever != 999999987", (steam_id,))
    playtime_forever = cursor.fetchall()

    total_playtime = 0

    for game in playtime_forever:
        # add together all the playtime_forever values
        total_playtime += int(game[0])
    
    #convert the total_playtime from minutes to hours
    total_playtime = total_playtime / 60

    # round total playtime hours to 2 decimal places
    total_playtime = round(total_playtime, 2)

    # convert to days
    days = total_playtime / 24

    days = round(days, 2)

    # get the users top 10 games from the games table using their steam_id, ignoring any rows where the playtime_forever is 999999987
    cursor.execute("SELECT appid,playtime_forever FROM games WHERE steam_id = ? AND playtime_forever != 999999987 ORDER BY playtime_forever DESC LIMIT 10", (steam_id,))
    top_10_games = cursor.fetchall()

    disconnect(database)

    description = f"Total Playtime: {total_playtime} hours (or {days} days).\n\nMost played games:\n"

    for game in top_10_games:
        # convert the playtime_forever from minutes to hours
        hours = game[1] / 60
        # round the playtime_forever to 2 decimal places
        hours = round(hours, 2)

        response = requests.get(f"https://store.steampowered.com/api/appdetails?appids={game[0]}&format=json", headers={"User-Agent": "Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)"})
        json_data = json.loads(str(response.text))

        

        try:
            gameinfo = json_data[f'{game[0]}']['data']

            name = gameinfo['name']
        except:
            print(json_data)
            name = f"**Error: {game[0]}**"

        description += f"{name}: {hours} hours\n"


    # fetch the discord name of the user using their discord_id
    userDetails = await ctx.guild.fetch_member(user_id)
    name = userDetails.name
    pfp = userDetails.avatar_url

    # create a discord embed to display the users stats
    games_embed = discord.Embed(title=f"{name}'s Stats", description=description)
    games_embed.set_thumbnail(url=pfp)
    games_embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar_url)

    print(name)
    print(pfp)
    print(description)

    # send the embed
    #await InteractionContext.send(ctx, embed=games_embed)
    # ctx.send doesn't work for some reason :shrug:
    # will probably overhaul the entire bot at some point
    message = await ctx.channel.send(embed=games_embed)

@slash.slash(name="Gamertag",description="Generate a random gamertag", guild_ids=guild_ids_lst) 
async def _gamertag(ctx):  

    # find the length of the text files 'Nouns.txt' and 'Adjectives.txt'
    nouns_file = open("Nouns.txt", "r")
    nouns_list = nouns_file.readlines()
    nouns_file_length = len(nouns_list)
    
    adjectives_file = open("Adjectives.txt", "r")
    adjectives_list = adjectives_file.readlines()
    adjectives_file_length = len(adjectives_list)
    
    # generate a random number between 1 and the length of the text files
    noun_index = rand.randint(1, nouns_file_length)
    adjective_index = rand.randint(1, adjectives_file_length)

    # generate a random number between 1 and 5
    # this will decide if a number will be added to the end of the gamertag
    include_int = rand.randint(1, 5)


    # get the noun and adjective from the text files
    noun = nouns_list[noun_index - 1]
    adjective = adjectives_list[adjective_index - 1]

    

    # close the opened files
    adjectives_file.close()
    nouns_file.close()

    # remove the newline character from the noun and adjective
    noun = noun.replace("\n", "")
    adjective = adjective.replace("\n", "")

    # capitalize the first letter of the noun and adjective
    noun = noun.capitalize()
    adjective = adjective.capitalize()

    # if the random number generated is 1, add a number to the end of the gamertag
    if include_int == 1:
        gamertag = f"{adjective}{noun}{rand.randint(1, 99)}"
    else:
        gamertag = f"{adjective}{noun}"

    # return a message @ing the person who called the command, but not pinging them 
    await ctx.send(f"**{gamertag}**")

@slash.slash(name="Roulette",description="Russian Roulette. Simple.", guild_ids=guild_ids_lst) 
async def _roulette(ctx):  

    # check if the user is an admin
    if ctx.author.guild_permissions.administrator:

        responses = ["you're an admin, you can't take the risk!","No!, not allowed","You know what happened last time you tried this. Not. Again."]

        # generate a random number between 1 and and the length of the responses list
        response_index = rand.randint(0, len(responses)-1)


        await ctx.send(f"{ctx.author.mention} {responses[response_index]}")
        return
    
    # generate a random number between 1 and 6 (7 to be a little less risky)
    roll = rand.randint(1, 7)

    # if the random number generated is 1, give them the role 'dead'
    if roll == 1:

        # get the name of a random user in the server
        random_user = rand.choice(ctx.guild.members)

        dead_responses = ['get fucked!',f'couldn\'t take living in the same world as {random_user} anymore!','passed away in the early hours of this morning','Died ... Ha!','you\'re dead!']
        # generate a random number between 1 and and the length of the responses list
        response_index = rand.randint(0, len(dead_responses)-1)

        await ctx.author.add_roles(ctx.guild.get_role(944070170203291709))
        await ctx.author.add_roles(ctx.guild.get_role(901624226665078784))
        await ctx.send(f"{ctx.author.mention} {dead_responses[response_index]}")
    else:

        # list of responses for when the user is alive
        alive_responses = ['you\'re still alive!','you\'re going to live another day!','you\'re alive i guess.','you survived ... somehow.','you\'re alive!','you live on','you live on unfortunately']
        # generate a random number between 1 and and the length of the responses list
        response_index = rand.randint(0, len(alive_responses)-1)

        await ctx.send(f"{ctx.author.mention} {alive_responses[response_index]}")

        


        


bot.run(bot_token)