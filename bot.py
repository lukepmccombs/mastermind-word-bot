from re import M
from discord.abc import Messageable
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
import os
import mastermind
import json


command_prefix = os.environ["COMMAND_PREFIX"]
localisation = None
with open("./localisation.json".format(os.environ["LOCALISATION"]), "rb") as l_file:
    localisation = json.load(l_file)
localisation = {
    k: localisation[k] % command_prefix if "%s" in localisation[k] else localisation[k]
    for k in localisation.keys()
}


def log(msg):
    """Logging function for printing to k8s"""
    print("{}: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))

def make_botuser_handler(bot):
    """Makes a handler for ignoring bot user commands"""
    async def handle_message(message):
        if message.author.bot:
            if message.content.startswith(command_prefix):
                log("[WARN] A bot user with id {} tried to send a command to this bot.")
            return
        await bot.process_commands(message)

    return handle_message


class UserInfo:
    """Stores info about a user"""

    def __init__(self):
        self.dm = None
        self.game: mastermind.MastermindWord = None
        self.daily: mastermind.MastermindWord = None
        self.last_game: mastermind.MastermindWord = None
        self.auto_reply = False


class MastermindWordBot(commands.Cog):
    """Contains functions relative to command processing for the bot"""

    def __init__(self, bot):
        self.bot = bot
        self.users = defaultdict(lambda: UserInfo())
        self.daily_game = mastermind.MastermindWord(daily=True)
        self.daily_time = datetime.now().replace(hour=0, minute=0, second=0)
    
    ### Synchronous helper functions

    def get_daily(self):
        """Returns the daily game, if its been a day since the last one a new game is started"""
        if datetime.now() - self.daily_time > timedelta(days=1):
            self.daily_time = datetime.now().replace(hour=0, minute=0, second=0)
            self.daily_game = mastermind.MastermindWord(daily=True)
        
        return self.daily_game.copy()
    
    ### Asynchronous helper functions
    
    async def send_embed(self, chan: Messageable, msg):
        """Sends a pre formatted embed"""
        pass
    
    async def send_message(self, chan: Messageable, msg):
        """Sends a pre formatted message"""
        await chan.send(msg)

    async def get_user(self, ctx, silent=False) -> UserInfo:
        """Locates the user's info in the database, and notifies if necessary."""

        user = self.users[ctx.author.id]
        if not silent and user.dm is None:
            user.dm = await ctx.author.create_dm()
            await self.send_message(user.dm, localisation["user_intro"])

        return user

    ### Commands

    @commands.command(
        description=localisation["start_desc"],
        usage="['daily' | 'zen' | num = 6]",
        brief=localisation["start_brief"]
    )
    async def start(self, ctx, max_guess: str="6"):
        """Start a game for a user, if possible"""
        user = await self.get_user(ctx)

        if user.game:
            await self.send_message(ctx, localisation["game_ongoing"])
            return
        
        if max_guess == "daily":
            if user.daily == self.daily_game:
                await self.send_message(ctx, localisation["daily_once"])
            
            user.game = self.get_daily()
            user.daily = user.game

            await self.send_message(ctx, localisation["daily_start"])

        else:
            if max_guess == "zen":
                max_guess = -1
                
            else:
                try:
                    max_guess = int(max_guess)
                except ValueError:
                    max_guess = 6
            
            user.game = mastermind.MastermindWord(max_guess)
            await self.send_message(ctx, localisation["game_start"])

        log("[INFO] User {}({}) started a game with word {}".format(ctx.author.display_name, ctx.author.id, user.game.word))


    @commands.command(
        description=localisation["quit_desc"],
        brief=localisation["quit_brief"]
    )
    async def quit(self, ctx):
        """Quits any ongoing games for a user"""
        user = await self.get_user(ctx)

        if user.game:
            if user.game == self.daily_game:
                await self.send_message(ctx, localisation["daily_quit"])
            else:
                await self.send_message(ctx, localisation["game_quit"].format(word=user.game.word))
            
            user.game = None

        else:
            await self.send_message(ctx, localisation["game_none"])
        
        log("[INFO] User {}({}) quit their game.".format(ctx.author.display_name, ctx.author.id))
    

    @commands.command(
        description=localisation["guess_desc"],
        usage="word",
        brief=localisation["guess_brief"]
    )
    async def guess(self, ctx, word: str=None):
        """Performs a guess in the player's ongoing game"""
        if word is None:
            return

        user = await self.get_user(ctx)

        if user.game is None:
            await self.send_message(ctx, localisation["guess_no_game"])
            return
        
        if user.game == self.daily_game and ctx.message.channel != user.dm:
            await self.send_message(ctx, localisation["guess_bad_daily"])
            await self.send_message(user.dm, localisation["guess_bad_daily_warn"])
            return
        
        result = None
        try:
            result = user.game.guess(word)

        except mastermind.MastermindBadWord:
            await self.send_message(ctx, localisation["guess_bad_dict"])
            return

        except mastermind.MastermindMaxGuess:
            await self.send_message(ctx,
                localisation["guess_max_daily"] if user.game == self.daily_game
                    else localisation["guess_max"].format(word=user.game.word)
            )
            user.game = None
            log("[INFO] User {}({}) completed a game.".format(ctx.author.display_name, ctx.author.id))
            return
        
        if all(x==2 for x in result):
            if user.game == self.daily_game:
                await self.send_message(ctx, localisation["daily_complete"].format(
                    turns=user.game.current_guesses(),
                    path=user.game.path_string())
                )
                user.game = None

            else:
                await self.send_message(ctx, localisation["game_complete"].format(
                    turns=user.game.current_guesses(),
                    maxTurns=user.game.max_guess if user.game.max_guess >= 0 else "∞",
                    word=user.game.word,
                    path=user.game.path_string()
                ))
                user.last_game, user.game = user.game, None

            log("[INFO] User {}({}) completed a game.".format(ctx.author.display_name, ctx.author.id))
            
        else:
            await self.send_message(ctx, "{} {} / {}".format(
                mastermind.MastermindWord.res_to_emojis(result),
                user.game.current_guesses(),
                user.game.max_guess if user.game.max_guess >= 0 else "∞"
            ))
    

    @commands.command(
        description=localisation["reply_desc"],
        brief=localisation["reply_brief"]
    )
    async def reply(self, ctx):
        user = await self.get_user(ctx)
        user.auto_reply = not user.auto_reply

        if user.auto_reply:
            await self.send_message(ctx, localisation["reply_enable"])
        else:
            await self.send_message(ctx, localisation["reply_disable"])


    @commands.command(
        description=localisation["brag_desc"],
        usage="['daily']",
        brief=localisation["brag_brief"]
    )
    async def brag(self, ctx, daily: str=None):
        """Displays the path in the player's most recent or daily game"""
        user = await self.get_user(ctx)

        if daily == "daily":
            if user.daily != self.daily_game:
                await self.send_message(ctx, localisation["daily_none"])
                return
            
            await self.send_message(ctx, localisation["daily_brag"].format(
                turns=user.daily.current_guesses(),
                path=user.daily.path_string()
            ))

        elif user.last_game:
            await self.send_message(ctx, localisation["game_brag"].format(
                word=user.last_game.word,
                turns=user.last_game.current_guesses(),
                maxTurns=user.game.max_guess if user.game.max_guess >= 0 else "∞",
                path=user.last_game.path_string()
            ))

        else:
            await self.send_message(ctx, localisation["game_brag_none"])

    ### Listeners

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handles auto reply guesses"""
        user = await self.get_user(message, silent=True)

        if user.auto_reply and message.channel == user.dm and not message.content.startswith(command_prefix):
            await self.guess(await self.bot.get_context(message), message.content.split(" ")[0])
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Logs the starting of the bot"""
        log("[INFO] Bot has started successfully!")
        log("[INFO] Loaded {} words.".format(len(mastermind.MastermindWord.dictionary)))


if __name__ == "__main__":
    bot = commands.Bot(os.environ["COMMAND_PREFIX"])
    bot.on_message = make_botuser_handler(bot)
    bot.add_cog(MastermindWordBot(bot))
    bot.run(os.environ["DISCORD_TOKEN"])