import sys
from collections import defaultdict

import contextlib
import curio
import functools
import inspect
import textwrap
import traceback
from io import StringIO

from curious.commands import Plugin, command, Context

from sixx.plugins.utils import is_owner


class REPL(Plugin):
    def __init__(self, client):
        super().__init__(client)

        self.sessions = set()

    @staticmethod
    def clean_code(code):
        # yikies
        if code.startswith(('```py\n', '```\n')):
            newline_before_end = code.endswith('\n```')
            lines = slice(1, -1 if newline_before_end else None, None)
            code = '\n'.join(code.splitlines()[lines])

        return code.strip('\n` ')

    @command(name='sessions')
    async def sessions_(self, ctx: Context):
        guilds = defaultdict(list)

        for id in self.sessions:
            channel = ctx.bot.find_channel(id)
            guilds[channel.guild].append(channel)

        if not guilds:
            return await ctx.channel.messages.send('No REPL sessions open.')

        message = '```\n'

        for guild, channels in guilds.items():
            message += '{0.id:<20} ({0.name})\n'.format(guild)

            for channel in channels:
                message += '  * {0.id:<20} ({0.name})\n'.format(channel)

        message += '```'

        await ctx.channel.messages.send(message)

    @command()
    @is_owner()
    async def repl(self, ctx: Context):
        # `_` will be added in here later
        env = {
            'ctx': ctx,
            'bot': ctx.bot,
            'client': ctx.bot,  # lol
            'guild': ctx.guild,
            'message': ctx.message,
            'channel': ctx.channel,
            'author': ctx.author,
            'manager': ctx.manager
        }
        env.update(sys.modules)

        dest = ctx.channel.messages

        if ctx.channel.id in self.sessions:
            return await dest.send('A REPL session is already running in this channel.')

        self.sessions.add(ctx.channel.id)  # We can't not set a value, really

        await dest.send(f'```\n{sys.version} on {sys.platform}```')

        def predicate(message):
            return (message.author.id == ctx.author.id and
                    message.channel.id == ctx.channel.id and
                    message.content.startswith('`') and
                    message.content.endswith('`'))

        while True:
            try:
                async with curio.timeout_after(60 * 15):
                    response = await ctx.bot.wait_for('message_create', predicate=predicate)
            except curio.TaskTimeout:
                self.sessions.remove(ctx.channel.id)
                await dest.send('Timed out after 15 minutes.')
                return

            code = self.clean_code(response.content)

            if code in 'quit quit() exit exit()'.split():
                # TODO maybe cool things here?
                self.sessions.remove(ctx.channel.id)
                await dest.send('Exiting.')
                return

            try:
                compiled = compile(code, f'<repl session in {ctx.channel.id}>', 'eval')
            except SyntaxError:
                # Not a simple eval statement

                try:
                    compiled = compile(code, f'<repl session in {ctx.channel.id}>', 'exec')
                except SyntaxError as e:
                    # We failed miserably

                    # traceback.format_exc output was bad
                    message = (
                        '```\n'
                        'Traceback (most recent call last):\n'
                        '  File "{0.filename}, line {0.lineno}, in {3}\n'
                        '    {0.text}\n'
                        '    {1:>{0.offset}}\n'  # Stupid
                        '{2.__name__}: {0.msg}\n'
                        '```'
                    )

                    await dest.send(message.format(e, '^', type(e), __name__))

                    continue
                else:
                    executor = exec
            else:
                executor = eval

            stdout = StringIO()
            # Don't forget to update
            env['message'] = response

            try:
                with contextlib.redirect_stdout(stdout):
                    # Remember:
                    #     TypeError: <executor>() takes no keyword arguments
                    result = executor(compiled, env)

                    if inspect.isawaitable(result):
                        result = await result
            except:
                output = stdout.getvalue()
                message = f'```\n{output}\n{traceback.format_exc()}```'
            else:
                output = stdout.getvalue()
                env['_'] = result

                indent = functools.partial(textwrap.indent, prefix='  ')
                message = '```\nstdout:\n{0}\nresult:\n{1}```'.format(
                    indent(output or '(Empty)'), indent(str(result))
                )

            if len(message) > 2000:
                await dest.send('Output too long.')
            else:
                await dest.send(message)
