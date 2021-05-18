# Deskom Bot

Deskom is a Simple Python Discord bot that monitors Eskom's site for load-shedding stage changes and announces them to server channels.

![Maintenance](https://img.shields.io/maintenance/yes/2021?style=flat-square)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/Moon-developer/Discord-Eskom?style=flat-square)
![GitHub](https://img.shields.io/github/license/Moon-developer/Discord-Eskom?style=flat-square)
![Pylint](https://img.shields.io/github/workflow/status/Moon-developer/Discord-Eskom/Pylint?logo=GitHub&label=Pylint&style=flat-square)

## Setup

Download the executable from the release package.  
Might need to change file permissions with `chmod`

```shell
$ chmod +x bot
```

Now execute the file while passing in the bot token.

```shell
$ ./bot --token <your-bot-token-here>
```

## Manual Installation

First we clone the bot:

```shell
$ git clone https://github.com/qoder-za/Discord-Eskom.git deskom 
$ cd deskom
```

Next we need to set up some environment variables for the bot. Create a `.env` file in project root.

```shell
$ touch .env
```

Open the file and add the following

```dotenv
DISCORD_TOKEN = <your-bot-token-here>
```

Save and close the file.  
Now we install the required dependencies and run start the bot up.

```shell
$ pip install -r requirements.txt
$ python bot.py
```

## USAGE

Once your bot is running and invited to a server you can run the following commands on discord:

```
send message: !eskom announce #channel
send message: !eskom disable
send message: !eskom stage
send message: !eskom help
```

The `announce` command allows you to set a channel to announce on.

## Author

developer: [Marco Fernandes](https://github.com/moon-developer)
