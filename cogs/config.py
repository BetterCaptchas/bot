from discord.ext import commands

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['sprefix', 'setprefix'])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx, *, prefix=None):
        if prefix is None:
            return await ctx.send('yes i will set the prefix to nothing :thumbs_up:')

        if len(prefix) >= 12:
            return await ctx.send('Prefix must not be longer than 12 characters.')

        if prefix is None:
            return await ctx.send('The prefix must not be empty.')

        if ' ' in prefix:
            return await ctx.send('Prefix must not have a space in it.')

        old = await self.bot.pool.fetchval("SELECT prefix FROM guilds WHERE guildId = $1;", ctx.guild.id)

        if old == prefix:
            return await ctx.send('Prefix must not be current prefix.')

        await ctx.send(f'Successfully changed the prefix to `{prefix}`!')
        await self.bot.pool.execute('UPDATE guilds SET prefix = $1 WHERE guildid = $2;', prefix, ctx.guild.id)

def setup(bot):
    bot.add_cog(Config(bot))