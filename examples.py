from configparser import ConfigParser
from orator import DatabaseManager, Model
from orator.orm import has_many, has_one, belongs_to_many, belongs_to


class Game(Model):
    pass


class Statistic(Model):
    @belongs_to('userId')
    def user(self):
        return User

    @belongs_to('gameId')
    def game(self):
        return Game


class User(Model):
    @has_many('userId')
    def stats(self):
        return Statistic

    @belongs_to_many('statistics', 'userId', 'gameId')
    def games(self):
        return Game


class Db:
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

    def get_user(self):
        results = User.find('108337116919910400')
        print(results.username)
        print(results.games[0].name)
        print(results.stats[0].startTime)
        return
        # Examples
        # OR statement
        results = Statistic.where('startTime', '>=', '2016-03-11 00:06:24').or_where('endTime', '!=','2016-03-11 01:02:38').get()
        # AND statement
        results = Statistic.where('startTime', '>=', '2016-03-11 00:06:24').where('endTime', '!=',
                                                                                  '2016-03-11 01:02:38').get()
        # Filter based on a relationship
        results = Statistic.where('startTime', '>=', '2016-03-11 00:06:24').where_has('user', lambda q: q.where('username', '!=', 'VashTheBlade')).get()
        # results = Statistic.where('startTime', '>=', '2016-03-11 00:06:24').get()
        print(results[1].id)
        print(results[1].user.username)
        print(results[1].game.name)
        print(results.count())


if __name__ == '__main__':
    db = Db()
    db.get_user()
