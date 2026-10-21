A bot posting the Hacker News stories with 100+ points to [Mastodon](https://github.com/tootsuite/mastodon).

https://hackertribe.io/@HackerNewsBot

![](https://raw.githubusercontent.com/raymestalez/mastodon-hnbot/master/screenshot.png)

# Usage

Create an account for the bot. For convenience, you can use youremail+hnbot@gmail.com, to avoid registering a separate email.

Create config.ini with the following content:

```
[mastodon]
url = https://instance.url
points = 100
email = 
password = 
```

Then run the command:

```
python3 hnbot.py
```

# Configuration via environment variables

Every setting can be passed as an environment variable, which is handy for task
panels such as daidai-panel, Docker or CI. Environment variables take precedence;
`config.ini` is only used as a fallback.

| Variable | config.ini key | Description |
| --- | --- | --- |
| `MASTODON_URL` | `url` | Instance URL, e.g. `https://mastodon.social` (required) |
| `MASTODON_ACCESS_TOKEN` | `access_token` | Access token of the bot account. Recommended: when set, no credential files are created or needed |
| `MASTODON_CLIENT_ID` | `client_id` | Client key of an existing app (optional, used with email/password login) |
| `MASTODON_CLIENT_SECRET` | `client_secret` | Client secret of an existing app (optional) |
| `MASTODON_EMAIL` | `email` | Login email, only used when no access token is set |
| `MASTODON_PASSWORD` | `password` | Login password, only used when no access token is set |
| `HN_POINTS` | `points` | Minimum points of a story (default `100`) |
| `HNBOT_POST_DB` | | Path of the SQLite file that remembers posted stories (default `posts.db`) |
| `HNBOT_CLIENTCRED_TXT` | | Path of the generated client credential file (default `hnbot_clientcred.txt`) |
| `HNBOT_USERCRED_TXT` | | Path of the generated user credential file (default `hnbot_usercred.txt`) |
| `HNBOT_CONFIG` | | Path of the optional config file (default `config.ini`) |

To get an access token, open *Preferences → Development → New application* on
your instance, give it the `write:statuses` scope, and copy "Your access token".

Point `HNBOT_POST_DB` to a persistent location, otherwise the bot forgets what it
has already posted and will toot the same stories again.

# Run it regularly

You can use cron to run the bot regularly.

Run the command:

```
crontab -e
```

And at the end of the file add the line:

```
0,30 * * * * python3 /path/to/the/script/hnbot.py
```

(this will execute every 30 minutes)
