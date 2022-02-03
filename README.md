# Mastermind Word Bot
A wordle clone formatted as a bot for use on private discord servers.
Ignore the committed token, it does nothing

## Usage
This repository is built as a Dockerfile with three environment variables that can be set.
Only `DISCORD_TOKEN` must be set.


| Environment Variable | Description |
| --- | --- |
| `LOCALISATION` | The localisation used for the bot's replies. Only `en` is available for now. |
| `COMMAND_PREFIX` | The prefix needed for bot commands. This can be any string, and defaults to `%` |
| `DISCORD_TOKEN` | The discord token corresponding to the bot you want to use. |


Once the bot has been started, it can be used in the following way:

To start a game, use `%start` in any channel the bot has access to.
The bot will encourage play in private DMs, but you can guess in any channel it can access.

To guess, use `%guess <word>` until you succeed with the final guess.
The bot will reply with your results, but if you want to show off to your friends, `%brag` will print out your path again.

At any time use `%quit` to preemptively end a game.

For more commands with detailed descriptions of their uses and paramaters, use `%help`.
