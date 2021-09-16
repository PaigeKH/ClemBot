import discord
intents = discord.Intents.default()
intents.members = True

import os

from discord.ext import tasks, commands
from random import randint
import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

### make sure intents are included so that the bot can fetch the member list
client = discord.Client(intents=intents)

### sensitive data for congigs moved to the .env file
load_dotenv()

### access tokens for discord and youtube api
DISCORD_API_TOKEN = os.getenv("DISCORD_API_TOKEN")
YOUTUBE_API_TOKEN = os.getenv("YOUTUBE_API_TOKEN")

### links and channel for the video of the week
# these links should be contained to a specific channel
CHANNEL_VIDEO_ID = int(os.getenv("CHANNEL_VIDEO_ID"))
# link to a playlist with a year of wednesday videos
WEDNESDAY_VIDEO_PLAYLIST_URL = os.getenv("WEDNESDAY_VIDEO_PLAYLIST_URL")
# link to a friday video
FRIDAY_VIDEO_1_URL = os.getenv("FRIDAY_VIDEO_1_URL")
# link to another friday video
FRIDAY_VIDEO_2_URL = os.getenv("FRIDAY_VIDEO_2_URL")

### keep track of birthdays
CHANNEL_BIRTHDAY_ID = int(os.getenv("CHANNEL_BIRTHDAY_ID"))
BIRTHDAYS = json.loads(os.getenv("BIRTHDAYS"))

### the video the bot will link when someone uses a specific phrase
LINK_1_URL = os.getenv("LINK_1_URL")
LINK_2_URL = os.getenv("LINK_2_URL")
LINK_3_URL = os.getenv("LINK_3_URL")
LINK_4_URL = os.getenv("LINK_4_URL")
LINK_5_URL = os.getenv("LINK_5_URL")
LINK_6_URL = os.getenv("LINK_6_URL")
LINK_7_URL = os.getenv("LINK_7_URL")
LINK_8_URL = os.getenv("LINK_8_URL")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
PERSON_1_ID = int(os.getenv("PERSON_1_ID"))
PERSON_1_NAME = os.getenv("PERSON_1_NAME")
PERSON_2_ID = int(os.getenv("PERSON_2_ID"))

### what messages/emojis are responsible for assigning roles
# the ID of the message for the bot to check
ROLE_MESSAGE_ID = int(os.getenv("ROLE_MESSAGE_ID"))
# name of the first role it can assign
ROLE_1_NAME = os.getenv("ROLE_1_NAME")
# custom server emoji for the first role it can assign
ROLE_1_EMOJI_ID = int(os.getenv("ROLE_1_EMOJI_ID"))
ROLE_1_EMOJI_NAME = os.getenv("ROLE_1_EMOJI_NAME")
# name of the second role it can assign
ROLE_2_NAME = os.getenv("ROLE_2_NAME")
# custom server emoji for the second role it can assign
ROLE_2_EMOJI_ID = int(os.getenv("ROLE_2_EMOJI_ID"))
ROLE_2_EMOJI_NAME = os.getenv("ROLE_2_EMOJI_NAME")

EMBED_CHANNEL_ID = int(os.getenv("EMBED_CHANNEL_ID"))
EMBED_CHANNEL_IMAGE_URL = os.getenv("EMBED_CHANNEL_IMAGE_URL")
EMBED_TITLE = os.getenv("EMBED_TITLE")
EMBED_TEXT = os.getenv("EMBED_TEXT")

TEST_CHANNEL_ID = int(os.getenv("TEST_CHANNEL_ID"))


@client.event
async def on_ready():
    print('Logging in as {0.user}'.format(client))

    #only call this once to format a roles message
    #await post_roles_message()

    # start the cog so we can have a video on the correct days
    myCog = MyCog()

@client.event
# don't use on_reaction_add(), it won't keep the original message cached
async def on_raw_reaction_add(payload):
    if payload.member == client.user:
        return
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

### don't use the client.command override because they are limiting
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

    if ('!bouldering') in message.content.lower():
        await message.channel.send(LINK_3_URL)

    # a kind of spammy message, so only let one specific person use it to tag their friend
    if ('!meow') in message.content.lower() and message.author.id == PERSON_1_ID:
        await message.channel.send("Meow, it's me, your cat, <@" + str(PERSON_2_ID) + ">. " + PERSON_1_NAME + " told me to share this important message with you.")

    # I don't have perms to delete clembot's messages if needed so I'll work around this
    if ('!purge') in message.content.lower() and message.author.id == BOT_OWNER_ID:
        command = message.content.lower().split()
        if (len(command) > 1) and command[1].isnumeric():
            delete_num = int(command[1])
            async for msg in message.channel.history(limit=100):
                if delete_num > 0 and msg.author == client.user:
                    delete_num -= 1
                    print("Deleting message:", msg, msg.content)
                    await msg.delete()
        else:
            print("Err with !purge, ", command[1], "is not a number")


    if ('clem') in message.content.lower():
        await message.add_reaction('🐈')

    if ('content') in message.content.lower():
        await message.add_reaction('🌽')
        await message.add_reaction('⛺')

async def post_roles_message():
    channel = client.get_channel(EMBED_CHANNEL_ID)

    # embedBanner = discord.Embed(color=discord.Color.blue())
    # embedBanner.set_image(url=EMBED_CHANNEL_IMAGE_URL)
    # await channel.send(embed=embedBanner)

    embedText = discord.Embed(title="Roles", color=discord.Color.blue())
    embedText.add_field(name=EMBED_TITLE, value=EMBED_TEXT, inline=False)
    messageCoroutine = channel.send(embed=embedText)
    message = await messageCoroutine
    await message.add_reaction("<:" + ROLE_1_EMOJI_NAME + ":" + str(ROLE_1_EMOJI_ID) + ">")
    await message.add_reaction("<:" + ROLE_2_EMOJI_NAME + ":" + str(ROLE_2_EMOJI_ID) + ">")


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

    def __init__(self):
        self.postedBirthdayToday = False
        self.postedVideoToday = False
        self.playlist = self.getPlaylist()
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    # check a few times a day so it posts earlier and not later
    @tasks.loop(hours=8.0)
    async def printer(self):
        # the bot get restarted by heroku on most days, so this prevents it from double posting
        # I can't save a file on heroku to list last posted time, so search for a matching post

        # standardize to west coast time zone
        today = datetime.utcnow() - timedelta(hours=7)

        # birthday and videos get posted to different channels, so I search both
        channel = client.get_channel(CHANNEL_VIDEO_ID)
        messages = await channel.history(limit=200).flatten()


        for msg in messages:
            if msg.author == client.user and msg.created_at.date() == datetime.utcnow().date(): #and message is from today

                if ("🐸" in msg.content and today.weekday() == 2) or\
                        ((FRIDAY_VIDEO_1_URL in msg.content or FRIDAY_VIDEO_2_URL in msg.content) and today.weekday() == 4):
                    self.postedVideoToday = True
                    print("Already posted today:", msg.content, "at", msg.created_at)
                    break
                else:
                    self.postedVideoToday = False

        channel = client.get_channel(CHANNEL_BIRTHDAY_ID)
        messages = await channel.history(limit=200).flatten()

        for msg in messages:
            if msg.author == client.user and msg.created_at.date() == datetime.utcnow().date(): #and message is from today
                if ("Happy Birthday" in msg.content):
                    self.postedBirthdayToday = True
                    print("Already posted today:", msg.content, "at", msg.created_at)
                    break
                else:
                    self.postedBirthdayToday = False


        # now make the daily post
        if not (self.postedBirthdayToday or self.postedVideoToday):
            # Wednesdays
            if today.weekday() == 2:
                # Print the URL for the frog video matching up to this week
                # The playlist started August 30th, 2017, which was the 34th week of that year
                # Therefore offset by (52 - 34 = 18) and mod by total weeks in a year to get the appropriate video of the week
                url = "https://www.youtube.com/watch?v=" + self.playlist[(datetime.today().isocalendar()[1] + 18) % 52]["snippet"]["resourceId"]["videoId"]
                print("Posting a Wednesday video at", datetime.today())

                await client.get_channel(CHANNEL_VIDEO_ID).send(url + " 🐸")


            # Fridays
            elif today.weekday() == 4:
                # 0 is special, 1-9 are normal
                isNormal = randint(0, 9)

                # Post the video in the week leading up to Christmas
                currentDay = today.timetuple().tm_yday
                isChristmasWeek = currentDay <= 359 and currentDay > 352

                # Post the normal one by default
                url = FRIDAY_VIDEO_1_URL

                # Post the special video 10% of the time, or on Christmas
                if not isNormal or isChristmasWeek:
                    url = FRIDAY_VIDEO_2_URL

                print("Posting a Friday video at", datetime.today())

                await client.get_channel(CHANNEL_VIDEO_ID).send(url)


            # birthday contains a month, a day, and a person
            for birthday in BIRTHDAYS["Birthdays"]:
                if today.month == birthday[0] and today.day == birthday[1]:
                    print("Posting a Birthday message for", birthday[2], "at", datetime.today())
                    await client.get_channel(CHANNEL_BIRTHDAY_ID).send("Happy Birthday, <@" + str(birthday[3]) + "> !")

def check(message):
    return message.author == client.user


client.run(DISCORD_API_TOKEN)