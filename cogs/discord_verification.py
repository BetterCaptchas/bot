from discord.ext import commands
import discord
import aiohttp


def disconfig_embed(ctx):
    embed = discord.Embed(
        title=f'{ctx.guild.name}',
        description='\n**VerifiedRole**\n`.disconfig verifiedrole <roleid/mention>`'
                    '\n\n**Enabled**\n`.disconfig enabled <true/false>`'
    )
    return embed


async def role_mod_check(role):
    perms = ['kick_members', 'ban_members', 'administrator', 'manage_channels', 'manage_guild',
             'manage_messages', 'mention_everyone', 'manage_nicknames', 'manage_roles', 'manage_webhooks']

    if any([getattr(role.permissions, i) for i in perms]):
        return True
    return False


async def abuse_check(ctx, role):
    if role >= ctx.author.top_role:
        return True
    return False


class DisVerify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='disconfig', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def _helpdis(self, ctx):
        await ctx.send(embed=disconfig_embed(ctx))

    @_helpdis.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def verifiedrole(self, ctx, role: discord.Role):
        abuse = await abuse_check(ctx, role)
        abuse_mod = await role_mod_check(role)
        if abuse is False:
            if abuse_mod is False:
                await self.bot.pool.execute(f'UPDATE verification SET roleid=$1, enabled=$2 WHERE guildid=$3;',
                                            role.id, True, ctx.guild.id)
            else:
                return await ctx.send('You may not set a role that has moderation permissions.')
        else:
            return await ctx.send('You may not set a role that\'s higher or equal to your highest one.')
        await ctx.send(f'Successfully changed the config role to `{role.name}`!')

    @_helpdis.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def enabled(self, ctx, role: bool):
        try:
            if not await self.is_empty(ctx):
                await self.bot.pool.execute(f'UPDATE verification SET enabled=$1 WHERE guildid=$2;', role,
                                            ctx.guild.id)
            else:
                return await ctx.send('You may not enable the module until you setup discord verification.')
        except:
            return await ctx.send('Improper value passed!')
        await ctx.send(f'Successfully changed the value to `{role}`!')

    async def is_empty(self, ctx):
        value = await self.bot.pool.fetchval('SELECT roleid FROM verification WHERE guildid=$1;', ctx.guild.id)

        if value is None:
            return True
        return False

    async def is_verified_enabled(self, ctx):
        value = await self.bot.pool.fetch(f'SELECT enabled, roleid FROM verification WHERE guildid=$1;',
                                          ctx.guild.id)
        role = ctx.guild.get_role(value[0]["roleid"])
        if role is None:
            return False
        if role not in ctx.author.roles:
            return True
        return False

    async def verify_user(self, ctx, user):
        value = await self.bot.pool.fetchval('SELECT roleid FROM verification WHERE guildid=$1;', ctx.guild.id)
        role = ctx.guild.get_role(value)

        if role is None:
            return

        try:
            await user.add_roles(role)
        except discord.HTTPException:
            return

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.guild_only()
    async def verify(self, ctx):
        if await self.is_verified_enabled(ctx):
            embed = discord.Embed(
                title=f'{ctx.guild.name}!',
                description='In order to gain access to this server, you have to verify that you aren\'t a robot. '
                            'Please solve the simple captcha bellow, note that **captchas** are case sensitive.'
                            '\n\n**Why do I have to verify?**\n\nVerification is used to prevent malicious automated '
                            'user-bot attacks against an guild (server).'
                            '\n\n**Your captcha:**'
            )
            embed.timestamp = ctx.message.created_at
            async with aiohttp.ClientSession() as cs:
                async with cs.get('https://ammarsysdev.pythonanywhere.com/api/img') as response:
                    image = await response.json()
                    random_image = image["url"]
                    response.close()

            embed.set_image(url=f"{random_image}")
            try:
                await ctx.author.send(embed=embed)
            except discord.Forbidden:
                return
            await ctx.send('I\'ve sent you a captcha in DMs.')
            solution = image["solution"]

            def check_for_solution(m):
                return m.author == ctx.author and m.channel == ctx.author.dm_channel

            failed_attempts = 0
            while failed_attempts < 3:
                solution_attempt = await self.bot.wait_for('message', check=check_for_solution, timeout=20)

                if solution_attempt.content != solution:
                    failed_attempts += 1
                    if failed_attempts != 3:
                        await ctx.author.send(f'You\'ve got **{failed_attempts}/3** tries left.')

                else:
                    await ctx.author.send(f'Successfully verified you in guild **{ctx.guild.name}**!')
                    return await self.verify_user(ctx, ctx.author)
            await ctx.author.send('Captcha failed, try again.')
        else:
            await ctx.send('This server hasn\'t enabled discord verification or you\'re already verified!')


def setup(bot):
    bot.add_cog(DisVerify(bot))
