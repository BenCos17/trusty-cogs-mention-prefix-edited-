from __future__ import annotations

import logging
from typing import Any, List, Optional

import discord
from discord.ext.commands.errors import BadArgument
from redbot.core.commands import commands
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import box, humanize_list, pagify
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from redbot.vendored.discord.ext import menus

from .converters import ChannelUserRole, Trigger

log = logging.getLogger("red.Trusty-cogs.retrigger")
_ = Translator("ReTrigger", __file__)


class ExplainReTriggerPages(menus.ListPageSource):
    def __init__(self, pages: list):
        super().__init__(pages, per_page=1)
        self.pages = pages
        self.select_options = []
        for count, page in enumerate(pages):
            self.select_options.append(discord.SelectOption(label=f"Page {count+1}", value=count))

    def is_paginating(self):
        return True

    async def format_page(self, menu: menus.MenuPages, page):
        if menu.ctx.channel.permissions_for(menu.ctx.guild.me).embed_links:
            em = discord.Embed(
                description=page, colour=await menu.cog.bot.get_embed_colour(menu.ctx.channel)
            )
            em.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
            return em
        else:
            return page


class ReTriggerPages(menus.ListPageSource):
    def __init__(self, triggers: List[Trigger], guild: discord.Guild):
        super().__init__(triggers, per_page=1)
        self.active_triggers = triggers
        self.selection = None
        self.guild = guild
        self.enabled = False
        self.select_options = []
        for count, trigger in enumerate(triggers):
            self.select_options.append(discord.SelectOption(label=trigger.name[:25], value=count))

    def is_paginating(self):
        return True

    async def format_page(self, menu: menus.MenuPages, trigger: Trigger):
        self.selection = trigger
        msg_list = []
        embeds = menu.ctx.channel.permissions_for(menu.ctx.guild.me).embed_links
        good = "\N{WHITE HEAVY CHECK MARK}"
        bad = "\N{NEGATIVE SQUARED CROSS MARK}"
        # trigger = await Trigger.from_json(triggers)
        self.enabled = trigger.enabled
        author = self.guild.get_member(trigger.author)
        if not author:
            try:
                author = await menu.cog.bot.fetch_user(trigger.author)
            except Exception:
                author = discord.Object(id=trigger.author)
                author.name = _("Unknown or Deleted User")
                author.mention = _("Unknown or Deleted User")
                author.avatar_url = "https://cdn.discordapp.com/embed/avatars/1.png"
        blacklist = []
        for y in trigger.blacklist:
            try:
                blacklist.append(await ChannelUserRole().convert(menu.ctx, str(y)))
            except BadArgument:
                continue
        if embeds:
            blacklist_s = ", ".join(x.mention for x in blacklist)
        else:
            blacklist_s = ", ".join(x.name for x in blacklist)
        whitelist = []
        for y in trigger.whitelist:
            try:
                whitelist.append(await ChannelUserRole().convert(menu.ctx, str(y)))
            except BadArgument:
                continue
        if embeds:
            whitelist_s = ", ".join(x.mention for x in whitelist)
        else:
            whitelist_s = ", ".join(x.name for x in whitelist)
        if trigger.response_type:
            responses = humanize_list(trigger.response_type)
        else:
            responses = _("This trigger has no actions and should be removed.")
        timestamp = int(trigger.timestamp)

        info = _(
            "__Name__: **{name}** \n"
            "__Active__: **{enabled}**\n"
            "__Author__: {author}\n"
            "__Count__: **{count}**\n"
            "__Created__: **<t:{created}:R>**\n"
            "__Response__: **{response}**\n"
            "__NSFW__: **{nsfw}**\n"
        )
        if embeds:
            info = info.format(
                name=trigger.name,
                enabled=good if trigger.enabled else bad,
                author=author.mention,
                created=timestamp,
                count=trigger.count,
                response=responses,
                nsfw=trigger.nsfw,
            )
        else:
            info = info.format(
                name=trigger.name,
                enabled=good if trigger.enabled else bad,
                author=author.name,
                created=timestamp,
                count=trigger.count,
                response=responses,
                nsfw=trigger.nsfw,
            )
        text_response = ""
        if trigger.ignore_commands:
            info += _("__Ignore commands__: **{ignore}**\n").format(ignore=trigger.ignore_commands)
        if "text" in trigger.response_type:
            if trigger.multi_payload:
                text_response = "\n".join(t[1] for t in trigger.multi_payload if t[0] == "text")
            else:
                text_response = trigger.text
            if len(text_response) < 200:
                info += _("__Text__: ") + "**{response}**\n".format(response=text_response)
        if trigger.reply is not None:
            info += _("__Replies with Notification__:") + "**{response}**\n".format(
                response=trigger.reply
            )
        if "rename" in trigger.response_type:
            if trigger.multi_payload:
                response = "\n".join(t[1] for t in trigger.multi_payload if t[0] == "rename")
            else:
                response = trigger.text
            info += _("__Rename__: ") + "**{response}**\n".format(response=response)
        if "dm" in trigger.response_type:
            if trigger.multi_payload:
                response = "\n".join(t[1] for t in trigger.multi_payload if t[0] == "dm")
            else:
                response = trigger.text
            info += _("__DM__: ") + "**{response}**\n".format(response=response)
        if "command" in trigger.response_type:
            if trigger.multi_payload:
                response = "\n".join(t[1] for t in trigger.multi_payload if t[0] == "command")
            else:
                response = trigger.text
            info += _("__Command__: ") + "**{response}**\n".format(response=response)
        if "react" in trigger.response_type:
            if trigger.multi_payload:
                emoji_response = [
                    r for t in trigger.multi_payload for r in t[1:] if t[0] == "react"
                ]
            else:
                emoji_response = trigger.text
            server_emojis = "".join(f"<{e}>" for e in emoji_response if len(e) > 5)
            unicode_emojis = "".join(e for e in emoji_response if len(e) < 5)
            info += _("__Emojis__: ") + server_emojis + unicode_emojis + "\n"
        if "add_role" in trigger.response_type:
            if trigger.multi_payload:
                role_response = [
                    r for t in trigger.multi_payload for r in t[1:] if t[0] == "add_role"
                ]
            else:
                role_response = trigger.text
            roles = [menu.ctx.guild.get_role(r) for r in role_response]
            if embeds:
                roles_list = [r.mention for r in roles if r is not None]
            else:
                roles_list = [r.name for r in roles if r is not None]
            if roles_list:
                info += _("__Roles Added__: ") + humanize_list(roles_list) + "\n"
            else:
                info += _("Roles Added: Deleted Roles\n")
        if "remove_role" in trigger.response_type:
            if trigger.multi_payload:
                role_response = [
                    r for t in trigger.multi_payload for r in t[1:] if t[0] == "remove_role"
                ]
            else:
                role_response = trigger.text
            roles = [menu.ctx.guild.get_role(r) for r in role_response]
            if embeds:
                roles_list = [r.mention for r in roles if r is not None]
            else:
                roles_list = [r.name for r in roles if r is not None]
            if roles_list:
                info += _("__Roles Removed__: ") + humanize_list(roles_list) + "\n"
            else:
                info += _("__Roles Added__: Deleted Roles\n")
        if whitelist_s:
            info += _("__Allowlist__: ") + whitelist_s + "\n"
        if blacklist_s:
            info += _("__Blocklist__: ") + blacklist_s + "\n"
        if trigger.cooldown:
            time = trigger.cooldown["time"]
            style = trigger.cooldown["style"]
            info += _("__Cooldown__: ") + "**{}s per {}**\n".format(time, style)
        if trigger.ocr_search:
            info += _("__OCR__: **Enabled**\n")
        if trigger.check_edits:
            info += _("__Checking edits__: **Enabled**\n")
        if trigger.delete_after:
            info += _("__Message deleted after__: {time} seconds.\n").format(
                time=trigger.delete_after
            )
        if trigger.read_filenames:
            info += _("__Read filenames__: **Enabled**\n")
        if trigger.user_mention:
            info += _("__User Mentions__: **Enabled**\n")
        if trigger.everyone_mention:
            info += _("__Everyone Mentions__: **Enabled**\n")
        if trigger.role_mention:
            info += _("__Role Mentions__: **Enabled**\n")
        if trigger.tts:
            info += _("__TTS__: **Enabled**\n")
        if trigger.chance:
            info += _("__Chance__: **1 in {number}**\n").format(number=trigger.chance)
        if embeds:
            # info += _("__Regex__: ") + box(trigger.regex.pattern, lang="bf")
            em = discord.Embed(
                colour=await menu.cog.bot.get_embed_colour(menu.ctx.channel),
                title=_("Triggers for {guild}").format(guild=self.guild.name),
            )
            em.set_author(name=author, icon_url=author.avatar.url)
            if trigger.created_at == 0:
                em.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
            else:
                em.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()} Created")
                em.timestamp = trigger.created_at

            first = True
            for pages in pagify(info, page_length=1024):
                if first:
                    em.description = pages
                    first = False
                else:
                    em.add_field(name=_("Trigger info continued"), value=pages)
            if len(text_response) >= 200:
                use_box = False
                for page in pagify(text_response, page_length=1000):
                    if page.startswith("```"):
                        use_box = True
                    if use_box:
                        em.add_field(
                            name=_("__Text__"), value=box(page.replace("```", ""), lang="text")
                        )
                    else:
                        em.add_field(name=_("__Text__"), value=page)
            for page in pagify(trigger.regex.pattern, page_length=1000):
                em.add_field(name=_("__Regex__"), value=box(page, lang="bf"))
            msg_list.append(em)
        else:
            info += _("Regex: ") + box(trigger.regex.pattern[: 2000 - len(info)], lang="bf")
        if embeds:
            return em
        else:
            return info
        # return await make_embed_from_submission(menu.ctx.channel, self._subreddit, submission)


class ReTriggerSelectOption(discord.ui.Select):
    def __init__(self, options: List[discord.SelectOption], placeholder: str):
        super().__init__(min_values=1, max_values=1, options=options, placeholder=placeholder)

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        await self.view.show_checked_page(index)


class StopButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int],
    ):
        super().__init__(style=style, row=row)
        self.style = style
        self.emoji = "\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}"

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        await self.view.message.delete()


class ForwardButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int],
    ):
        super().__init__(style=style, row=row)
        self.style = style
        self.emoji = "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}"

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_checked_page(self.view.current_page + 1)


class BackButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int],
    ):
        super().__init__(style=style, row=row)
        self.style = style
        self.emoji = "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}"

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_checked_page(self.view.current_page - 1)


class LastItemButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int],
    ):
        super().__init__(style=style, row=row)
        self.style = style
        self.emoji = (
            "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\N{VARIATION SELECTOR-16}"
        )

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_page(self.view._source.get_max_pages() - 1)


class FirstItemButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int],
    ):
        super().__init__(style=style, row=row)
        self.style = style
        self.emoji = (
            "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\N{VARIATION SELECTOR-16}"
        )

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_page(0)


class ToggleTriggerButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int],
    ):
        super().__init__(style=style, row=row)
        self.style = discord.ButtonStyle.red
        self.emoji = "\N{NEGATIVE SQUARED CROSS MARK}"
        self.label = _("Disable Trigger")

    def modify(self):
        self.style = (
            discord.ButtonStyle.red if self.view.source.enabled else discord.ButtonStyle.green
        )
        self.emoji = (
            "\N{NEGATIVE SQUARED CROSS MARK}"
            if self.view.source.enabled
            else "\N{WHITE HEAVY CHECK MARK}"
        )
        self.label = _("Disable Trigger") if self.view.source.enabled else _("Enable Trigger")

    async def callback(self, interaction: discord.Interaction):
        """Enables and disables triggers"""
        member = interaction.user
        trigger = self.view.source.selection
        guild = self.view.source.guild
        if await self.view.cog.can_edit(member, self.view.source.selection):
            trigger.toggle()
            async with self.view.cog.config.guild(guild).trigger_list() as trigger_list:
                trigger_list[trigger.name] = await trigger.to_json()
            await self.view.show_checked_page(self.view.current_page)


class DeleteTriggerButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int],
    ):
        super().__init__(style=style, row=row, label=_("Delete Trigger"))
        self.style = style
        self.emoji = "\N{PUT LITTER IN ITS PLACE SYMBOL}"

    async def keep_trigger(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=_("Okay this trigger will not be deleted."), view=None
        )

    async def delete_trigger(self, interaction: discord.Interaction):
        self.view.source.selection.disable()
        done = await self.view.cog.remove_trigger(
            interaction.guild_id, self.view.source.selection.name
        )
        if done:
            # page = await self.view._source.get_page(self.current_page)
            # kwargs = await self.view._get_kwargs_from_page(page)
            await interaction.response.edit_message(
                content=_("This trigger has been deleted."), view=None
            )

    async def callback(self, interaction: discord.Interaction):
        """Enables and disables triggers"""
        member = interaction.user
        if await self.view.cog.can_edit(member, self.view.source.selection):
            new_view = discord.ui.View()
            approve_button = discord.ui.Button(style=discord.ButtonStyle.green, label=_("Yes"))
            approve_button.callback = self.delete_trigger
            deny_button = discord.ui.Button(style=discord.ButtonStyle.red, label=_("No"))
            deny_button.callback = self.keep_trigger
            new_view.add_item(approve_button)
            new_view.add_item(deny_button)
            await interaction.response.send_message(
                _("Are you sure you want to delete trigger {name}?").format(
                    name=self.view.source.selection.name
                ),
                ephemeral=True,
                view=new_view,
            )


class ReTriggerMenu(discord.ui.View):
    def __init__(
        self,
        source: menus.PageSource,
        cog: Optional[commands.Cog] = None,
        page_start: int = 0,
        clear_reactions_after: bool = True,
        delete_message_after: bool = False,
        timeout: int = 180,
        message: discord.Message = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            timeout=timeout,
        )
        self.cog = cog
        self.page_start = page_start
        self.ctx = None
        self.message = None
        self._source = source
        self.forward_button = ForwardButton(discord.ButtonStyle.grey, 0)
        self.back_button = BackButton(discord.ButtonStyle.grey, 0)
        self.first_item = FirstItemButton(discord.ButtonStyle.grey, 0)
        self.last_item = LastItemButton(discord.ButtonStyle.grey, 0)
        self.stop_button = StopButton(discord.ButtonStyle.red, 1)
        self.delete_button = DeleteTriggerButton(discord.ButtonStyle.red, 1)
        self.toggle_button = ToggleTriggerButton(discord.ButtonStyle.grey, 1)
        self.add_item(self.first_item)
        self.add_item(self.back_button)
        self.add_item(self.forward_button)
        self.add_item(self.last_item)
        self.add_item(self.toggle_button)
        self.add_item(self.delete_button)
        self.add_item(self.stop_button)
        self.current_page = page_start
        self.select_view: Optional[ReTriggerSelectOption] = None
        self.author = None

    @property
    def source(self):
        return self._source

    async def on_timeout(self):
        await self.message.edit(view=None)

    async def start(self, ctx: commands.Context):
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def send_initial_message(self, ctx, channel):
        """|coro|
        The default implementation of :meth:`Menu.send_initial_message`
        for the interactive pagination session.
        This implementation shows the first page of the source.
        """
        is_slash = False

        if isinstance(ctx, discord.Interaction):
            is_slash = True
            self.author = ctx.user
        else:
            self.author = ctx.author
        if self.ctx is None:
            self.ctx = ctx

        page = await self._source.get_page(self.page_start)
        kwargs = await self._get_kwargs_from_page(page)
        self.toggle_button.modify()
        if len(self.source.active_triggers) < 2:
            self.forward_button.disabled = True
            self.back_button.disabled = True
            self.first_item.disabled = True
            self.last_item.disabled = True
        else:
            options = self.source.select_options[:25]
            if len(self.source.select_options) > 25 and self.current_page > 12:
                options = self.source.select_options[
                    self.current_page - 12 : self.current_page + 13
                ]
            self.select_view = ReTriggerSelectOption(
                options=options, placeholder=_("Pick a Trigger")
            )
            self.add_item(self.select_view)
        if is_slash:
            self.message = await ctx.followup.send(**kwargs, view=self, wait=True)
        else:
            self.message = await channel.send(**kwargs, view=self)
        return self.message

    async def _get_kwargs_from_page(self, page):
        value = await discord.utils.maybe_coroutine(self._source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {"content": value, "embed": None}
        elif isinstance(value, discord.Embed):
            return {"embed": value, "content": None}

    async def show_page(self, page_number):
        page = await self._source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        self.toggle_button.modify()
        if len(self.source.active_triggers) < 2:
            self.forward_button.disabled = True
            self.back_button.disabled = True
            self.first_item.disabled = True
            self.last_item.disabled = True
        else:
            self.remove_item(self.select_view)
            options = self.source.select_options[:25]
            if len(self.source.select_options) > 25 and page_number > 12:
                options = self.source.select_options[page_number - 12 : page_number + 13]
            self.select_view = ReTriggerSelectOption(
                options=options, placeholder=_("Pick a Trigger")
            )
            self.add_item(self.select_view)
        await self.message.edit(**kwargs, view=self)

    async def show_checked_page(self, page_number: int) -> None:
        max_pages = self._source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(page_number)
            elif page_number >= max_pages:
                await self.show_page(0)
            elif page_number < 0:
                await self.show_page(max_pages - 1)
            elif max_pages > page_number >= 0:
                await self.show_page(page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: discord.Interaction):
        """Just extends the default reaction_check to use owner_ids"""
        if interaction.user.id not in (self.author.id,):
            await interaction.response.send_message(
                content=_("You are not authorized to interact with this."), ephemeral=True
            )
            return False
        return True


class BaseMenu(discord.ui.View):
    def __init__(
        self,
        source: menus.PageSource,
        cog: commands.Cog,
        clear_reactions_after: bool = True,
        delete_message_after: bool = False,
        timeout: int = 180,
        message: discord.Message = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            timeout=timeout,
        )
        self.cog = cog
        self.bot = None
        self.message = message
        self._source = source
        self.ctx = None
        self.current_page = kwargs.get("page_start", 0)
        self.forward_button = ForwardButton(discord.ButtonStyle.grey, 0)
        self.back_button = BackButton(discord.ButtonStyle.grey, 0)
        self.first_item = FirstItemButton(discord.ButtonStyle.grey, 0)
        self.last_item = LastItemButton(discord.ButtonStyle.grey, 0)
        self.stop_button = StopButton(discord.ButtonStyle.red, 0)
        self.add_item(self.first_item)
        self.add_item(self.back_button)
        self.add_item(self.forward_button)
        self.add_item(self.last_item)
        self.add_item(self.stop_button)
        self.select_view = ReTriggerSelectOption(
            options=self.source.select_options, placeholder=_("Pick a page")
        )
        self.add_item(self.select_view)

    @property
    def source(self):
        return self._source

    async def on_timeout(self):
        await self.message.edit(view=None)

    async def start(self, ctx: commands.Context):
        self.ctx = ctx
        self.bot = self.cog.bot
        # await self.source._prepare_once()
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page):
        value = await discord.utils.maybe_coroutine(self._source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {"content": value, "embed": None}
        elif isinstance(value, discord.Embed):
            return {"embed": value, "content": None}

    async def send_initial_message(self, ctx, channel):
        """|coro|
        The default implementation of :meth:`Menu.send_initial_message`
        for the interactive pagination session.
        This implementation shows the first page of the source.
        """
        is_slash = False

        if isinstance(ctx, discord.Interaction):
            is_slash = True
            self.author = ctx.user
        else:
            self.author = ctx.author
        if self.ctx is None:
            self.ctx = ctx
        page = await self._source.get_page(self.current_page)
        kwargs = await self._get_kwargs_from_page(page)
        if is_slash:
            self.message = await ctx.followup.send(**kwargs, view=self, wait=True)
        else:
            self.message = await channel.send(**kwargs, view=self)
        return self.message

    async def show_page(self, page_number):
        page = await self._source.get_page(page_number)
        self.current_page = self.source.pages.index(page)
        kwargs = await self._get_kwargs_from_page(page)
        await self.message.edit(**kwargs)

    async def show_checked_page(self, page_number: int) -> None:
        max_pages = self._source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(page_number)
            elif page_number >= max_pages:
                await self.show_page(0)
            elif page_number < 0:
                await self.show_page(max_pages - 1)
            elif max_pages > page_number >= 0:
                await self.show_page(page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: discord.Interaction):
        """Just extends the default reaction_check to use owner_ids"""
        if interaction.user.id not in (self.author.id,):
            await interaction.response.send_message(
                content=_("You are not authorized to interact with this."), ephemeral=True
            )
            return False
        return True
