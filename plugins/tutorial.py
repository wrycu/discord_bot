from disco.bot import Plugin


class TutorialPlugin(Plugin):
    @Plugin.command('ping')
    def command_ping(self, event):
        self.bot.db.get_user()
        event.msg.reply('Pong!')
