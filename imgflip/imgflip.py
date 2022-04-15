import logging
import re
from typing import Dict, List, Tuple

import aiohttp
from discord.ext.commands.converter import Converter
from discord.ext.commands.errors import BadArgument
from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import pagify

SEARCH_URL = "https://api.imgflip.com/get_memes"
CAPTION_URL = "https://api.imgflip.com/caption_image"
log = logging.getLogger("red.trusty-cogs.ImgFlip")


class meme2(Converter):
    """
    This will accept user ID's, mentions, and perform a fuzzy search for
    members within the guild and return a list of member objects
    matching partial names

    Guidance code on how to do this from:
    https://github.com/Rapptz/discord.py/blob/rewrite/discord/ext/commands/converter.py#L85
    https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/cogs/mod/mod.py#L24
    """

    async def convert(self, ctx, argument: str) -> Tuple[int, str]:
        result = None
        if not argument.isdigit():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(SEARCH_URL) as r:
                        results = await r.json()
                for memes in results["data"]["memes"]:
                    if argument.lower() in memes["name"].lower():
                        result = memes["id"]
            except Exception:
                result = None

        else:
            result = argument

        if result is None:
            raise BadArgument('meme2 "{}" not found'.format(argument))
        arg = argument
        if " " in argument:
            arg = f'"{argument}"'
        return (result, arg)


class ImgFlipAPIError(Exception):
    """ImgFlip API Error"""

    pass


class Imgflip(commands.Cog):
    """
    Generate memes from imgflip.com API
    """

    __author__ = ["Twentysix", "TrustyJAID"]
    __version__ = "2.1.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 356889977)
        default_global = {"username": "", "password": ""}
        self.config.register_global(**default_global)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """
        Thanks Sinbad!
        """
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """
        Nothing to delete
        """
        return

    async def get_meme2(
        self, meme2: int, boxes: List[Dict[str, str]], username: str, password: str
    ) -> str:
        log.debug(boxes)
        try:
            form_data = aiohttp.FormData()
            form_data.add_field("template_id", meme2)
            form_data.add_field("username", username)
            form_data.add_field("password", password)
            i = 0
            for box in boxes:
                for k, v in box.items():
                    form_data.add_field(f"boxes[{i}][{k}]", v)
                i += 1

            async with aiohttp.ClientSession() as session:
                async with session.post(CAPTION_URL, data=form_data) as r:
                    result = await r.json()
            if not result["success"]:
                raise ImgFlipAPIError(result["error_message"])
        except Exception as e:
            log.error("Error grabbing meme2", exc_info=True)
            raise ImgFlipAPIError(e)
        return result["data"]["url"]

    @commands.command(alias=["listmemes"])
    async def getmemes(self, ctx: commands.Context) -> None:
        """List memes with names that can be used"""
        await ctx.trigger_typing()
        await self.get_memes(ctx)

    async def get_memes(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get(SEARCH_URL) as r:
                results = await r.json()
        meme2list = ", ".join(m["name"] for m in results["data"]["memes"])
        meme2list += (
            "\nFind a meme2 at <https://imgflip.com/meme2templates> - "
            "click `Blank Template` and get the Template ID for more!"
        )
        for page in pagify(meme2list, [", "]):
            await ctx.send(page.lstrip(", "))

    @commands.command()
    async def meme2(self, ctx: commands.Context, text: str) -> None:
        """Create custom memes from imgflip

        `meme2_name` can be the name of the meme2 to use or the ID from imgflip
        `text` is lines of text separated by `|`
        Do `[p]getmemes` to see which meme2 names will work

        You can get meme2 ID's from https://imgflip.com/meme2templates
        click blank template and use the Template ID in place of meme2_name
        """
        user_pass = await self.config.all()
        if not user_pass["username"] or not user_pass["password"]:
            return await ctx.send(
                "You need to set a username and password first with "
                f"`{ctx.prefix}imgflipset <username> <password>`"
            )
        await ctx.trigger_typing()
        text = "".join(
            ctx.message.clean_content.replace(f"{ctx.prefix}{ctx.invoked_with} {meme2[1]}", "")
        )
        search_text: List[str] = re.split(r"\|", text)
        boxes = [{"text": v, "color": "#ffffff", "outline_color": "#000000"} for v in search_text]
        try:
            url = await self.get_meme2(meme2[0], boxes, user_pass["username"], user_pass["password"])
        except Exception:
            return await ctx.send("Something went wrong generating a meme2.")

        await ctx.send(url)

    @commands.command(name="imgflipset", aliases=["memeset"])
    @checks.is_owner()
    async def imgflip_set(self, ctx: commands.Context, username: str, password: str) -> None:
        """Command for setting required access information for the API"""
        await self.config.username.set(username)
        await self.config.password.set(password)
        if ctx.channel.permissions_for(ctx.me).manage_messages:
            await ctx.message.delete()
        await ctx.send("Credentials set!")
