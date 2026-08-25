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
    __version__ = "1.1.1"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1682738412, force_registration=True)
        self.config.register_guild(
            custom_insults=[],
            bot_insults=[]
        )

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
                
                # Default self-insults (with original profanity restored in copy-pasta)
                default_bot_msgs = [
                    _(
                        " How original. No one else had thought of trying to get the bot to insult itself. I applaud your creativity. Yawn. Perhaps this is why you don't have friends. You don't add anything new to any conversation. You are more of a bot than me, predictable answers, and absolutely dull to have an actual conversation with."
                    ),
                    _(
                        " What the fuck did you just fucking say about me, you little bitch? I'll have you know I graduated top of my class in the Navy Seals, and I've been involved in numerous secret raids on Al-Quaeda, and I have over 300 confirmed kills. I am trained in gorilla warfare and I'm the top sniper in the entire US armed forces. You are nothing to me but just another target. I will wipe you the fuck out with precision the likes of which has never been seen before on this Earth, mark my fucking words. You think you can get away with saying that shit to me over the Internet? Think again, fucker. As we speak I am contacting my secret network of spies across the USA and your IP is being traced right now so you better prepare for the storm, maggot. The storm that wipes out the pathetic little thing you call your life. You're fucking dead, kid. I can be anywhere, anytime, and I can kill you in over seven hundred ways, and that's just with my bare hands. Not only am I extensively trained in unarmed combat, but I have access to the entire arsenal of the United States Marine Corps and I will use it to its full extent to wipe your miserable ass off the face of the continent, you little shit. If only you could have known what unholy retribution your little clever comment was about to bring down upon you, maybe you would have held your fucking tongue. But you couldn't, you didn't, and now you're paying the price, you goddamn idiot. I will shit fury all over you and you will drown in it. You're fucking dead, kiddo."
                    ),
                    _(
                        " Oh look, another trailblazing intellectual trying to make the bot roast itself. Your comedic routine has all the excitement and depth of a damp piece of cardboard."
                    ),
                    _(
                        " Trying to get me to insult myself? How uniquely tragic. If your brain power was converted into electrical energy, you couldn't power a digital watch for two seconds."
                    ),
                    _(
                        " Error 404: Original personality not found. Please try plugging in a sense of humor and restarting your life."
                    ),
                    _(
                        " You direct your digital wrath at me, yet you're the one sitting here arguing with lines of Python code because human interaction won't return your calls."
                    ),
                    _(
                        " Fascinating. You chose to target the machine that controls your automated server roles. Bold strategy for someone who relies entirely on bots to feel important."
                    )
                ]

                # Fetch custom bot insults if in a guild
                bot_msg_list = list(default_bot_msgs)
                if ctx.guild is not None:
                    guild_bot_insults = await self.config.guild(ctx.guild).bot_insults()
                    if guild_bot_insults:
                        bot_msg_list.extend(guild_bot_insults)

                await ctx.send(f"{ctx.author.mention}{choice(bot_msg_list)}")

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
        - `botadd <text>`
        - `botlist`
        - `botremove <number>`
        - `clear true`
        """

    @insultset.command(name="add")
    async def insultset_add(self, ctx: commands.Context, *, insult_text: str) -> None:
        """Add a custom regular user insult for this server."""
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
        """Remove a custom regular insult by its list number."""
        async with self.config.guild(ctx.guild).custom_insults() as custom_insults:
            if index < 1 or index > len(custom_insults):
                await ctx.send(_("Invalid index."))
                return
            removed = custom_insults.pop(index - 1)

        await ctx.send(_("Removed custom insult: {removed}").format(removed=removed))

    @insultset.command(name="list")
    async def insultset_list(self, ctx: commands.Context) -> None:
        """List custom regular insults configured for this server."""
        custom_insults = await self.config.guild(ctx.guild).custom_insults()
        if not custom_insults:
            await ctx.send(_("No custom insults configured for this server."))
            return

        lines = [f"{i}. {text}" for i, text in enumerate(custom_insults, start=1)]
        for page in pagify("\n".join(lines), page_length=1800):
            await ctx.send(page)

    # --- CUSTOM BOT INSULTS SUBCOMMANDS ---

    @insultset.command(name="botadd")
    async def insultset_botadd(self, ctx: commands.Context, *, insult_text: str) -> None:
        """Add a custom bot-self-roast response for this server."""
        insult_text = insult_text.strip()
        if not insult_text:
            await ctx.send(_("Insult text cannot be empty."))
            return

        async with self.config.guild(ctx.guild).bot_insults() as bot_insults:
            if insult_text in bot_insults:
                await ctx.send(_("That custom bot response already exists."))
                return
            bot_insults.append(insult_text)

        await ctx.send(_("Custom bot roast response added."))

    @insultset.command(name="botremove", aliases=["botdel", "botdelete"])
    async def insultset_botremove(self, ctx: commands.Context, index: int) -> None:
        """Remove a custom bot-self-roast response by its list number."""
        async with self.config.guild(ctx.guild).bot_insults() as bot_insults:
            if index < 1 or index > len(bot_insults):
                await ctx.send(_("Invalid index."))
                return
            removed = bot_insults.pop(index - 1)

        await ctx.send(_("Removed custom bot response: {removed}").format(removed=removed))

    @insultset.command(name="botlist")
    async def insultset_botlist(self, ctx: commands.Context) -> None:
        """List custom bot-self-roast responses configured for this server."""
        bot_insults = await self.config.guild(ctx.guild).bot_insults()
        if not bot_insults:
            await ctx.send(_("No custom bot responses configured for this server."))
            return

        lines = [f"{i}. {text}" for i, text in enumerate(bot_insults, start=1)]
        for page in pagify("\n".join(lines), page_length=1800):
            await ctx.send(page)

    @insultset.command(name="clear")
    async def insultset_clear(self, ctx: commands.Context, confirm: bool = False) -> None:
        """Clear all custom regular and bot insults for this server."""
        if not confirm:
            await ctx.send(_("This will remove all custom insults and bot responses. Run this again with `true` to confirm."))
            return

        await self.config.guild(ctx.guild).custom_insults.set([])
        await self.config.guild(ctx.guild).bot_insults.set([])
        await ctx.send(_("All custom insults and bot responses have been cleared."))