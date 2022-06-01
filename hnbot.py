import os
import sqlite3
from configparser import ConfigParser

import feedparser
from mastodon import Mastodon

HNBOT_USERCRED_TXT = "hnbot_usercred.txt"
HACKER_NEWS_BOT = 'HackerNewsBot'
HNBOT_CLIENTCRED_TXT = 'hnbot_clientcred.txt'
POST_DB = 'posts.db'


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


def main():
    cfg = ConfigParser()
    cfg.read('config.ini')
    db = SQLiteDB()
    url = "https://hnrss.org/newest?points=" + cfg.get('mastodon', 'points')
    feed = feedparser.parse(url)
    stories = feed["entries"]
    # Make the list of stories who's id isn't in the seen list
    unseen_stories = [story for story in stories if not db.exist(story["id"])]
    if len(unseen_stories) <= 0:
        return

    instance_url = cfg.get('mastodon', 'url')

    # Create app if doesn't exist
    if not os.path.isfile(HNBOT_CLIENTCRED_TXT):
        print("Creating app")
        Mastodon.create_app(
            HACKER_NEWS_BOT,
            to_file=HNBOT_CLIENTCRED_TXT,
            api_base_url=instance_url
        )

    # Fetch access token if I didn't already
    if not os.path.isfile(HNBOT_USERCRED_TXT):
        print("Logging in")
        mastodon = Mastodon(
            client_id=HNBOT_CLIENTCRED_TXT,
            api_base_url=instance_url
        )
        email = cfg.get('mastodon', 'email')
        password = cfg.get('mastodon', 'password')
        mastodon.log_in(email, password, to_file=HNBOT_USERCRED_TXT)

    # Login using generated auth
    mastodon = Mastodon(
        client_id=HNBOT_CLIENTCRED_TXT,
        access_token=HNBOT_USERCRED_TXT,
        api_base_url=instance_url
    )
    for story in unseen_stories:
        title = story["title"]
        storyid = story["id"]
        post = title + "\n" + storyid + "\n#hackernews #tech"
        db.save(title, storyid)
        print("Posting " + post)
        mastodon.toot(post)


if __name__ == '__main__':
    main()
