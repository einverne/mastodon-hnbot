import os
import sqlite3
from configparser import ConfigParser

import feedparser
from mastodon import Mastodon

HACKER_NEWS_BOT = 'HackerNewsBot'

# Every setting can come from an environment variable; config.ini is only a fallback.
HNBOT_USERCRED_TXT = os.getenv('HNBOT_USERCRED_TXT', 'hnbot_usercred.txt')
HNBOT_CLIENTCRED_TXT = os.getenv('HNBOT_CLIENTCRED_TXT', 'hnbot_clientcred.txt')
POST_DB = os.getenv('HNBOT_POST_DB', 'posts.db')
CONFIG_INI = os.getenv('HNBOT_CONFIG', 'config.ini')


class SQLiteDB:

    def __init__(self) -> None:
        if not os.path.exists(POST_DB):
            self.conn = self.create_table()
        else:
            self.conn = sqlite3.connect(POST_DB)
        self.cursor = self.conn.cursor()

    def create_table(self):
        conn = sqlite3.connect(POST_DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE posts (title text, url text);''')
        c.execute('''CREATE INDEX idx_url ON posts (url);''')
        conn.commit()
        return conn

    def save(self, title, url):
        c = self.conn.cursor()
        query = 'INSERT INTO posts (title, url) VALUES (?, ?)'
        c.execute(query, (title, url))
        self.conn.commit()

    def exist(self, url):
        c = self.conn.cursor()
        query = ' SELECT * FROM posts WHERE url = ?'
        c.execute(query, (url,))
        result = c.fetchone()
        if result:
            return True
        else:
            return False


class Settings:

    def __init__(self) -> None:
        self.cfg = ConfigParser()
        self.cfg.read(CONFIG_INI)

    def get(self, env_name, option, default=None):
        value = os.getenv(env_name)
        if value:
            return value
        return self.cfg.get('mastodon', option, fallback=default)

    def require(self, env_name, option):
        value = self.get(env_name, option)
        if not value:
            raise SystemExit("Missing setting: set %s or [mastodon] %s in %s"
                             % (env_name, option, CONFIG_INI))
        return value


def login(settings, instance_url):
    access_token = settings.get('MASTODON_ACCESS_TOKEN', 'access_token')
    if access_token:
        return Mastodon(access_token=access_token, api_base_url=instance_url)

    client_id = settings.get('MASTODON_CLIENT_ID', 'client_id')
    client_secret = settings.get('MASTODON_CLIENT_SECRET', 'client_secret')
    if not (client_id and client_secret):
        # Create app if doesn't exist
        if not os.path.isfile(HNBOT_CLIENTCRED_TXT):
            print("Creating app")
            Mastodon.create_app(
                HACKER_NEWS_BOT,
                to_file=HNBOT_CLIENTCRED_TXT,
                api_base_url=instance_url
            )
        client_id = HNBOT_CLIENTCRED_TXT
        client_secret = None

    # Fetch access token if I didn't already
    if not os.path.isfile(HNBOT_USERCRED_TXT):
        print("Logging in")
        mastodon = Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            api_base_url=instance_url
        )
        email = settings.require('MASTODON_EMAIL', 'email')
        password = settings.require('MASTODON_PASSWORD', 'password')
        mastodon.log_in(email, password, to_file=HNBOT_USERCRED_TXT)

    # Login using generated auth
    return Mastodon(
        client_id=client_id,
        client_secret=client_secret,
        access_token=HNBOT_USERCRED_TXT,
        api_base_url=instance_url
    )


def main():
    settings = Settings()
    db = SQLiteDB()
    points = settings.get('HN_POINTS', 'points', '100')
    url = "https://hnrss.org/newest?points=" + points
    feed = feedparser.parse(url)
    stories = feed["entries"]
    # Make the list of stories who's id isn't in the seen list
    unseen_stories = [story for story in stories if not db.exist(story["id"])]
    if len(unseen_stories) <= 0:
        return

    instance_url = settings.require('MASTODON_URL', 'url')
    mastodon = login(settings, instance_url)
    for story in unseen_stories:
        title = story["title"]
        storyid = story["id"]
        post = title + "\n" + storyid + "\n#hackernews #tech"
        db.save(title, storyid)
        print("Posting " + post)
        mastodon.toot(post)


if __name__ == '__main__':
    main()
