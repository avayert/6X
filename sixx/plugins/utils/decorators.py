from curious.commands import condition, Context

__all__ = [
    'is_owner'
]


def is_owner():
    async def predicate(ctx: Context):
        return ctx.message.author_id == ctx.bot.application_info.owner.id

    return condition(predicate)
