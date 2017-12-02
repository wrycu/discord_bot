from disco.bot import Plugin


class RolePlugin(Plugin):
    def __init__(self, bot, config):
        self.allowed_roles = ['tags']
        self.required_roles = ['admin']
        super().__init__(bot, config)

    def load(self, ctx):
        super(RolePlugin, self).load(ctx)

    @Plugin.command('add_role', '<user:str> <role:str...>')
    def add_role(self, event, user, role):
        users = {}
        roles = {}

        for key, value in event.guild.members.items():
            users[str(value.user)] = key

        for key, value in event.guild.roles.items():
            roles[value.name] = key

        if not set(event.guild.get_member(event.author.id).roles).intersection([roles[x] for x in self.required_roles]):
            event.msg.reply('You do not have permission to use this feature.')
            return
        if role not in roles:
            event.msg.reply('That role does not exist!')
            return
        if role not in self.allowed_roles:
            event.msg.reply('You are not allowed to assign this role.')
            return
        user = user.replace('<', '').replace('>', '').replace('@', '')
        try:
            event.guild.get_member(user).add_role(roles[role])
        except ValueError:
            event.msg.reply('User does not exist!  Make sure you @ tag them')
            return
        event.msg.reply('The \'{}\' role has been added to the requested user.'.format(role))
        return

    @Plugin.command('remove_role', '<user:str> <role:str...>')
    def remove_role(self, event, user, role):
        users = {}
        roles = {}

        for key, value in event.guild.members.items():
            users[str(value.user)] = key

        for key, value in event.guild.roles.items():
            roles[value.name] = key

        if not set(event.guild.get_member(event.author.id).roles).intersection([roles[x] for x in self.required_roles]):
            event.msg.reply('You do not have permission to use this feature.')
            return
        if role not in roles:
            event.msg.reply('That role does not exist!')
            return
        if role not in self.allowed_roles:
            event.msg.reply('You are not allowed to un-assign this role.')
            return
        user = user.replace('<', '').replace('>', '').replace('@', '')
        try:
            event.guild.get_member(user).remove_role(roles[role])
        except ValueError:
            event.msg.reply('User does not exist!  Make sure you @ tag them')
            return
        event.msg.reply('The \'{}\' role has been removed from the requested user.'.format(role))
        return
