import discord
intents = discord.Intents.default()
intents.members = True

from discord.ext import tasks, commands
from random import randint
import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
from datetime import datetime
import json

### make sure intents are included so that the bot can fetch the member list
client = discord.Client(intents=intents)

###todo: move to configs file

### access tokens for discord and youtube api
DISCORD_API_TOKEN = ""
YOUTUBE_API_TOKEN = ""

### links and channel for the video of the week
# these links should be contained to a specific channel
CHANNEL_VIDEO_ID = 0
# link to a playlist with a year of wednesday videos
WEDNESDAY_VIDEO_PLAYLIST_URL = ""
# link to a friday video
FRIDAY_VIDEO_1_URL = ""
# link to another friday video
FRIDAY_VIDEO_2_URL = ""

### keep track of birthdays
CHANNEL_BIRTHDAY_ID = 0

### the video the bot will link when someone uses a specific phrase
LINK_1_URL = ""
LINK_2_URL = ""

### what messages/emojis are responsible for assigning roles
# the ID of the message for the bot to check
ROLE_MESSAGE_ID = 0
# name of the first role it can assign
ROLE_1_NAME = ""
# custom server emoji for the first role it can assign
ROLE_1_EMOJI_ID = 0
# name of the second role it can assign
ROLE_2_NAME = ""
# custom server emoji for the second role it can assign
ROLE_2_EMOJI_ID = 0

BIRTHDAYS = []

@client.event
async def on_ready():
    print('Logging in as {0.user}'.format(client))

    init_birthdays()

    # start the cog so we can have a video on the correct days
    myCog = MyCog()

# save my friend's birthdays in month/day/name/user_id form
# currently don't use the name, but it helps me keep track of who is who
def init_birthdays():
    #todo: move this to a file, just needed this out ASAP
    BIRTHDAYS.clear()
    BIRTHDAYS.append((1, 1, "Sample", 0))


@client.event
# don't use on_reaction_add(), it won't keep the original message cached
async def on_raw_reaction_add(payload):
    if (payload.message_id == ROLE_MESSAGE_ID):
        if (payload.emoji.id == ROLE_1_EMOJI_ID):
            print('Adding', ROLE_1_NAME, "to user", payload.member)
            role = discord.utils.get(payload.member.guild.roles, name=ROLE_1_NAME)
            await payload.member.add_roles(role)
        elif (payload.emoji.id == ROLE_2_EMOJI_ID):
            print('Adding', ROLE_2_NAME, "to user", payload.member)
            role = discord.utils.get(payload.member.guild.roles, name=ROLE_2_NAME)
            await payload.member.add_roles(role)

@client.event
# don't use on_reaction_remove(), it won't keep the original message cached
async def on_raw_reaction_remove(payload):
    if (payload.message_id == ROLE_MESSAGE_ID):
        if (payload.emoji.id == ROLE_1_EMOJI_ID):
            # on_raw_reaction_remove returns a payload with different data than
            # the on_raw_reaction_add payload, notably missing the member object.
            #  In order to access the member, first fetch the guild using the guild_id
            #  then fetch the member from the guild list using the user_id.
            #  This is why the bot needs intents enabled.

            guild = await client.fetch_guild(payload.guild_id)
            role = discord.utils.get(guild.roles, name=ROLE_1_NAME)
            member = await guild.fetch_member(payload.user_id)
            print('Removing', ROLE_1_NAME, "to user", member)
            await member.remove_roles(role)
        elif (payload.emoji.id == ROLE_2_EMOJI_ID):
            guild = await client.fetch_guild(payload.guild_id)
            role = discord.utils.get(guild.roles, name=ROLE_2_NAME)
            member = await guild.fetch_member(payload.user_id)
            print('Removing', ROLE_2_NAME, "to user", member)
            await member.remove_roles(role)


@client.event
async def on_message(message):
    # don't respond to the bot's own messages
    if message.author == client.user:
        return

    # otherwise check if a specific word/phrase is used and react/respond
    if ('!watch this') in message.content.lower():
        await message.channel.send(LINK_1_URL)

    if ('!names') in message.content.lower():
        await message.channel.send(LINK_2_URL)

    if ('clem') in message.content.lower():
        await message.add_reaction('🐈')

    if ('content') in message.content.lower():
        await message.add_reaction('🌽')
        await message.add_reaction('⛺')

class MyCog(commands.Cog):

    def getPlaylist(self):

        # extract playlist id from url
        url = WEDNESDAY_VIDEO_PLAYLIST_URL
        query = parse_qs(urlparse(url).query, keep_blank_values=True)
        playlist_id = query["list"][0]

        # connect with token
        youtube = googleapiclient.discovery.build("youtube", "v3",
                                                  developerKey=YOUTUBE_API_TOKEN)

        # request the playlist items from youtube
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50
        )
        response = request.execute()

        # Keep playlist for later so it doesn't need to fetch every iteration
        video_list = []
        while request is not None:
            response = request.execute()
            video_list += response["items"]
            request = youtube.playlistItems().list_next(request, response)

        return video_list

    def getVars(self):
        varsStream = open('vars.json','r')
        varsDict = json.loads(varsStream.read())
        print("Loading in last printed time after a reset:", varsDict["lastPosted"])
        varsStream.close()

        return varsDict

    def __init__(self):
        self.postedToday = False
        self.playlist = self.getPlaylist()
        self.vars = self.getVars()
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    # check a few times a day so it posts earlier and not later
    @tasks.loop(hours=8.0)
    async def printer(self):
        # the bot get restarted by heroku on most days, so this prevents it from double posting

        # Wednesdays
        if (datetime.now() - datetime.strptime(  self.vars["lastPosted"], "%b %d %Y %I:%M%p")).days >= 1:
            if datetime.today().weekday() == 2:
                # Print the URL for the frog video matching up to this week
                # The playlist started August 30th, 2017, which was the 34th week of that year
                # Therefore offset by (52 - 34 = 18) and mod by total weeks in a year to get the appropriate video of the week
                url = "https://www.youtube.com/watch?v=" + self.playlist[(datetime.today().isocalendar()[1] + 18) % 52]["snippet"]["resourceId"]["videoId"]
                await client.get_channel(CHANNEL_VIDEO_ID).send(url)

            # Fridays
            elif datetime.today().weekday() == 4:
                # 0 is special, 1-9 are normal
                isNormal = randint(0, 9)

                # Post the video in the week leading up to Christmas
                currentDay = datetime.now().timetuple().tm_yday
                isChristmasWeek = currentDay <= 359 and currentDay > 352

                # Post the normal one by default
                url = FRIDAY_VIDEO_1_URL

                # Post the special video 10% of the time, or on Christmas
                if not isNormal or isChristmasWeek:
                    url = FRIDAY_VIDEO_2_URL

                await client.get_channel(CHANNEL_VIDEO_ID).send(url)


            # birthday contains a month, a day, and a person
            for birthday in BIRTHDAYS:
                if datetime.today().month == birthday[0] and datetime.today().day == birthday[1]:
                    await client.get_channel(CHANNEL_BIRTHDAY_ID).send("Happy Birthday, <@" + str(birthday[3]) + "> !")

            # save the date it was last posted in case the bot is restarted
            self.vars["lastPosted"] = datetime.now().strftime("%b %d %Y %I:%M%p")
            with open('vars.json', 'w') as varsFile:
                json.dump(self.vars, varsFile)
            print("Posted today at", self.vars["lastPosted"])


client.run(DISCORD_API_TOKEN)