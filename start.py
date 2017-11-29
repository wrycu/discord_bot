def disco_main(run=False):
    """
    Creates an argument parser and parses a standard set of command line arguments,
    creating a new :class:`Client`.

    Returns
    -------
    :class:`Client`
        A new Client from the provided command line arguments
    """

    from gevent import monkey

    monkey.patch_all()

    from disco.client import Client, ClientConfig
    from disco.bot import Bot, BotConfig
    from disco.util.token import is_valid_token
    from disco.util.logging import setup_logging

    config = ClientConfig.from_file('config.yaml')

    if not is_valid_token(config.token):
        print('Invalid token passed')
        return

    setup_logging(level='INFO')

    client = Client(config)

    bot_config = BotConfig(config.bot)

    bot = Bot(client, bot_config)

    bot.run_forever()
    return bot


if __name__ == '__main__':
    disco_main(True)
