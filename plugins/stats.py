from disco.bot import Plugin
from disco.api.http import Routes
from disco.types import user
from disco.types.base import Unset
from datetime import datetime


class StatPlugin(Plugin):
    def __init__(self, bot, config):
        self.guilds = [x['id'] for x in bot.client.api.http(Routes.USERS_ME_GUILDS_LIST).json()]
        self.tracked_roles = ['admin']
        self.excluded_roles = ['discord_bot_testing']
        self.roles = {}
        # TODO: figure out how to do this without a stupid bool that's used once
        self.first_run = True
        # TODO: properly support more than one guild. this assumes all roles exist on all servers with the same IDs
        for guild in self.guilds:
            for role in bot.client.api.guilds_roles_list(guild):
                self.roles[role.name] = role.id
        super().__init__(bot, config)

    @Plugin.schedule(60)
    def track_status(self):
        if self.first_run:
            self.bot.db.cleanup()
            self.first_run = False
        now = datetime.now()
        known_members = self.bot.db.get_members()
        for guild in self.guilds:
            # For each server we're a member of, collect all of the users on that server
            members = self.bot.client.api.guilds_members_list(guild)
            for member in members:
                # 'member' is simply an ID, but we want more than that. Overwrite the member object straight away
                # This is not best practice but we don't care about 'member' at all, so whatever
                member = self.bot.client.api.guilds_members_get(guild, member)  # lookup member details
                member_id = int(member.id)
                # Check if we know the status of the member, and save it for later
                if member_id in self.bot.client.state.users and not isinstance(self.bot.client.state.users[member_id].presence, Unset):
                    member_presence = self.bot.client.state.users[member_id].presence
                else:
                    # Cache starts as empty - expect to see the error at least once per run
                    print("Member {} not in state tracking - closing stats".format(member))
                    self.bot.db.close_stats(member_id, '', now)
                    continue

                if set(member.roles).intersection([self.roles[x] for x in self.tracked_roles]) and \
                        not set(member.roles).intersection([self.roles[x] for x in self.excluded_roles]):
                    # The role they have is one we track and not an excluded role
                    if member_id not in known_members:
                        self.bot.db.create_member(member_id, str(member.name), now)
                else:
                    # They are in the excluded list or not in the tracked list
                    continue

                if member_presence.status == user.Status.IDLE or not member_presence.game.name:
                    # The user is AFK or they are not playing a game - close their entries
                    self.bot.db.close_stats(member_id, '', now)
                elif member_presence.game.name:
                    # The user is active and playing a game
                    self.bot.db.create_stat(member_id, str(member_presence.game.name), now)
