from random import choice
from typing import Optional

import discord
from redbot.core import Config, commands
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.chat_formatting import pagify

_ = Translator("Insult", __file__)
from .insults_data import insults

@cog_i18n(_)
class Insult(commands.Cog):
    """Airenkun's Insult Cog"""

    __author__ = ["Airen", "JennJenn", "TrustyJAID","BenCos17",]
    __version__ = "1.0.1"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1682738412, force_registration=True)
        self.config.register_guild(custom_insults=[])

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

    @commands.command(aliases=["takeitback"])
    async def insult(self, ctx: commands.Context, user: Optional[discord.Member] = None) -> None:
        """
        Send a random insult.

        If `user` is provided, that member is insulted.
        If `user` is omitted, you are insulted.

        Examples:
        - `[p]insult @User`
        - `[p]insult`
        """

        msg = " "
        all_insults = list(insults)
        if ctx.guild is not None:
            all_insults.extend(await self.config.guild(ctx.guild).custom_insults())

        if not all_insults:
            await ctx.send(_("No insults are configured."))
            return

        if user:

            if user.id == self.bot.user.id:
                user = ctx.message.author
                bot_msg = [
                    _(
                        " How original. No one else had thought of trying to get the bot to insult itself. I applaud your creativity. Yawn. Perhaps this is why you don't have friends. You don't add anything new to any conversation. You are more of a bot than me, predictable answers, and absolutely dull to have an actual conversation with."
                    ),
                    _(
                        " What the fuck did you just fucking say about me, you little bitch? Iâ€™ll have you know I graduated top of my class in the Navy Seals, and Iâ€™ve been involved in numerous secret raids on Al-Quaeda, and I have over 300 confirmed kills. I am trained in gorilla warfare and Iâ€™m the top sniper in the entire US armed forces. You are nothing to me but just another target. I will wipe you the fuck out with precision the likes of which has never been seen before on this Earth, mark my fucking words. You think you can get away with saying that shit to me over the Internet? Think again, fucker. As we speak I am contacting my secret network of spies across the USA and your IP is being traced right now so you better prepare for the storm, maggot. The storm that wipes out the pathetic little thing you call your life. Youâ€™re fucking dead, kid. I can be anywhere, anytime, and I can kill you in over seven hundred ways, and thatâ€™s just with my bare hands. Not only am I extensively trained in unarmed combat, but I have access to the entire arsenal of the United States Marine Corps and I will use it to its full extent to wipe your miserable ass off the face of the continent, you little shit. If only you could have known what unholy retribution your little â€œcleverâ€ comment was about to bring down upon you, maybe you would have held your fucking tongue. But you couldnâ€™t, you didnâ€™t, and now youâ€™re paying the price, you goddamn idiot. I will shit fury all over you and you will drown in it. Youâ€™re fucking dead, kiddo."
                    ),
                ]
                await ctx.send(f"{ctx.author.mention}{choice(bot_msg)}")

            else:
                await ctx.send(user.mention + msg + choice(all_insults))
        else:
            await ctx.send(ctx.message.author.mention + msg + choice(all_insults))

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def insultset(self, ctx: commands.Context) -> None:
        """
        Manage server custom insults.

        Subcommands:
        - `add <text>`
        - `list`
        - `remove <number>`
        - `clear true`
        """

    @insultset.command(name="add")
    async def insultset_add(self, ctx: commands.Context, *, insult_text: str) -> None:
        """
        Add a custom insult for this server.

        Example:
        - `[p]insultset add Your custom insult here`
        """
        insult_text = insult_text.strip()
        if not insult_text:
            await ctx.send(_("Insult text cannot be empty."))
            return

        async with self.config.guild(ctx.guild).custom_insults() as custom_insults:
            if insult_text in custom_insults:
                await ctx.send(_("That custom insult already exists."))
                return
            custom_insults.append(insult_text)

        await ctx.send(_("Custom insult added."))

    @insultset.command(name="remove", aliases=["del", "delete"])
    async def insultset_remove(self, ctx: commands.Context, index: int) -> None:
        """
        Remove a custom insult by its list number.

        Use `[p]insultset list` to find the number.
        Example:
        - `[p]insultset remove 2`
        """
        async with self.config.guild(ctx.guild).custom_insults() as custom_insults:
            if index < 1 or index > len(custom_insults):
                await ctx.send(_("Invalid index."))
                return
            removed = custom_insults.pop(index - 1)

        await ctx.send(_("Removed custom insult: {removed}").format(removed=removed))

    @insultset.command(name="list")
    async def insultset_list(self, ctx: commands.Context) -> None:
        """
        List custom insults configured for this server.

        Example:
        - `[p]insultset list`
        """
        custom_insults = await self.config.guild(ctx.guild).custom_insults()
        if not custom_insults:
            await ctx.send(_("No custom insults configured for this server."))
            return

        lines = [f"{i}. {text}" for i, text in enumerate(custom_insults, start=1)]
        for page in pagify("\n".join(lines), page_length=1800):
            await ctx.send(page)

    @insultset.command(name="clear")
    async def insultset_clear(self, ctx: commands.Context, confirm: bool = False) -> None:
        """
        Clear all custom insults for this server.

        You must confirm with `true`.
        Example:
        - `[p]insultset clear true`
        """
        if not confirm:
            await ctx.send(_("This will remove all custom insults. Run this again with `true` to confirm."))
            return

        await self.config.guild(ctx.guild).custom_insults.set([])
        await ctx.send(_("All custom insults have been cleared."))
