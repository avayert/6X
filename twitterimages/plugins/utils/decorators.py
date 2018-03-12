from curious.commands import condition, Context


def is_owner():
    async def predicate(ctx: Context):
        if not hasattr(ctx.bot, 'owner_id'):
            # The type hint implies it only accepts an integer but setting it to
            # None will internally get the AppInfo corresponding to your own bot.
            #
            # Why None is not the default argument that I do not know.
            app = await ctx.bot.get_application(None)
            ctx.bot.owner_id = app.owner.id
        return ctx.message.author_id == ctx.bot.owner_id

    return condition(predicate)
