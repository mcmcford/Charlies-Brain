import os
from re import S
import sys
import datetime
import discord
import mariadb
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



        


bot.run(bot_token)