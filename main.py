import os
import discord
import configparser
from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext
from discord_slash.context import MenuContext
from discord_slash.model import ContextMenuType
from discord_slash.utils.manage_commands import create_option

guild_ids_lst = [713068366419722300]

config = configparser.ConfigParser()

if os.path.exists('config.ini') == False:
    config['DEFAULT'] = {'bot_token': '123xyz'}
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

bot = Client(intents=Intents.default())
slash = SlashCommand(bot,sync_commands=True)

@bot.event
async def on_ready():
    print("Logged in as " + str(bot.user))
    print("User ID: " + str(bot.user.id))

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

    if multiple_choice == True:
        embed.set_footer(text="You can vote for multiple options")
    else:
        embed.set_footer(text="Only vote for one option! if you vote for multiple by the end of the poll, your votes won't be counted")

    await ctx.send(embed=embed)

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
        
    
    

bot.run(bot_token)