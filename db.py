from configparser import ConfigParser
from orator import DatabaseManager, Model
from orator.orm import has_many, belongs_to_many, belongs_to
from orator.exceptions.orm import ModelNotFound


class Game(Model):
    __timestamps__ = False
    __fillable__ = ['name', 'firstUser', 'firstSeen']


class Statistic(Model):
    __timestamps__ = False
    __fillable__ = ['gameId', 'userId', 'startTime', 'endTime']

    @belongs_to('userId')
    def user(self):
        return User

    @belongs_to('gameId')
    def game(self):
        return Game


class User(Model):
    __timestamps__ = False  # Disable automatic tracking of creation/update times
    __incrementing__ = False  # Tell Orator not to attempt to auto-increment the PK
    __fillable__ = ['id', 'username', 'realname', 'firstSeen']  # Allow assigning many columns

    @has_many('userId')
    def stats(self):
        return Statistic

    @belongs_to_many('statistics', 'userId', 'gameId')
    def games(self):
        return Game


class ChartingDao:
    def __init__(self):
        conf_obj = ConfigParser()
        conf_obj.read('db.ini')
        conf = {
            'mysql': {
                'driver': 'mysql',
                'host': conf_obj.get('stats', 'host'),
                'user': conf_obj.get('stats', 'user'),
                'password': conf_obj.get('stats', 'password'),
                'database': conf_obj.get('stats', 'db'),
                'prefix': '',
            }
        }
        db = DatabaseManager(conf)
        Model.set_connection_resolver(db)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def get_members():
        """
        Retrieve a list of all Discord members
        :return:
            A LIST of all member IDs
        """
        members = []
        results = User.all()

        for member in results:
            members.append(member.id)
        return members

    @staticmethod
    def member_exists(user_id):
        """
        Check if a member exists in the database
        :param user_id:
            ID of the member being checked
        :return:
            BOOL indicating if the user exists
        """
        return True if User.find(user_id) else False

    @staticmethod
    def create_member(user_id, username, first_seen, real_name=None):
        """
        Insert a new member into the database
        :param user_id:
            ID of the member.  This should be their discord ID
        :param username:
            Username of the member (display name - may be changed by them)
        :param first_seen:
            Date/time representing when the user was first seen
            2017-01-01 00:00:00
        :param real_name:
            IRL name of the member. Not used anywhere currently, but may be assigned.
        :return:
            N/A
        """

        try:
            User.create(id=user_id, username=username, firstSeen=first_seen, realname=real_name)
        except Exception as e:
            print("Failed to save member with ID {}: {}".format(user_id, str(e)))

    @staticmethod
    def get_games():
        """
        Retrieve a list of all known games
        :return:
            All known game IDs and names
            A LIST of tuples - [(1, 'KOTOR'), (2, 'The Witcher 3')]
        """
        games = []
        results = Game.all()
        for game in results:
            games.append((game.id, game.name))
        return games

    @staticmethod
    def get_game_id(game_name):
        """
        Look up the ID of a game given the name
        :param game_name:
            The name of the game to look up
        :return:
            ID of the game if it exists, or None if it does not
        """
        try:
            return Game.where('name', '=', game_name).first_or_fail().id
        except ModelNotFound:
            return None

    @staticmethod
    def create_game(name, first_user, first_seen):
        """
        Create a new game to track stats against
        :param name:
            Name of the game to create. This is not checked for duplicates
        :param first_user:
            ID of the user who was first seen playing the game
        :param first_seen:
            Datetime at which the game was first seen being played
            2017-01-01 00:00:00
        :return:
            ID of the created game
        """
        try:
            return Game.create(name=name, firstUser=first_user, firstSeen=first_seen).id
        except Exception as e:
            print("Failed to save game with name {}: {}".format(name, str(e)))

    @staticmethod
    def get_stats(user_id):
        """
        Look up all currently open entries for a given user
        :param user_id:
            ID of the user you want to look up
        :return:
            Games which are currently in progress
            A LIST of tuples (game ID, entry ID) - [(1, 2000), (2, 9000)]
        """
        in_progress = []
        results = Statistic.where('userId', '=', user_id).where_null('endTime').get()
        for result in results:
            in_progress.append((result.gameId, result.id))
        return in_progress

    @staticmethod
    def close_stat(stat_id, end_time):
        """
        Add an end time to a given entry, marking that the game is no longer being played
        Note that you can invoke "close_stats" to close ALL entries for a given user
        :param stat_id:
            ID of the stat entry to close
        :param end_time:
            Datetime at which this game was finished being played
            2017-01-01 00:00:00
        :return:
            N/A
        """
        Statistic.where('id', '=', stat_id).update(endTime=end_time)

    def close_stats(self, user_id, game_name, end_time):
        """
        Add an end time to all games a user is playing, marking those games as no longer being played
        NOTE: This will exclude game_name
        :param user_id:
            ID of the user you want to close stats for
        :param game_name:
            TODO: make game_name an optional parameter
            Name of the game being played (and, as a result, to exclude)
        :param end_time:
            Datetime at which the game was finished being played
            2017-01-01 00:00:00
        :return:
            N/A
        """
        if game_name == '':
            game_id = -1
        else:
            game_id = Game.where('name', '=', game_name).first().id
        stat_ids = [x[1] for x in self.get_stats(user_id)]  # We only care about the entry ID, not the game ID

        Statistic.where(
            'userId', '=', user_id
        ).where(
            'gameId', '!=', game_id
        ).where_in(
            'id', stat_ids
        ).update(endTime=end_time)

    def create_stat(self, user_id, game_name, start_time):
        """
        Insert a new entry representing a user playing a game
        Note that this function will automatically close any other entries for that user
        :param user_id:
            ID of the user playing the game
        :param game_name:
            Name of the game that the user is playing
        :param start_time:
            The time at which the user started playing the game
        :return:
            N/A
        """
        entries = self.get_stats(user_id)
        game_id = self.get_game_id(game_name)
        if not game_id:
            game_id = self.create_game(game_name, user_id, start_time)

        for entry in entries:
            if entry[0] != game_id:
                self.close_stat(entry[1], start_time)
            else:
                # The game they're playing is the same one that we're currently tracking
                # Don't do anything
                return

        Statistic.create(gameId=game_id, userId=user_id, startTime=start_time)

    @staticmethod
    def cleanup():
        Statistic.where_null('endTime').delete()


if __name__ == '__main__':
    dao = ChartingDao()
    print(dao.member_exists(1337))
