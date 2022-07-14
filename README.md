# Quick README

Copy bot code folders to bots/

Run `docker-compose up --build`

## PM2 config

Create a `pm2.config.js` file like the following:

```javascript
const WORKDIR = "/marsbots";

module.exports = {
  apps: [
    {
      name: "devbot",
      script: `${WORKDIR}/bot.py`,
      interpreter: "python",
      args: `${WORKDIR}/bots/devbot/devbot.json --cog-path=bots.devbot.devbot --dotenv-path=${WORKDIR}/bots/devbot/.env`,
      watch: [`${WORKDIR}/bots/devbot`],
      watch_delay: 1000,
    },
  ],
};
```

Run `export PM2_CONFIG_PATH=/marsbots/path/to/config`

## Additional Python Requirements

Create a consolidated `requirements.txt` in `bots/` and run `export REQUIREMENTS_FILE=/marsbots/bots/requirements.txt`
