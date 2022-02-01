import random

class MastermindBadWord(Exception):
    """Raised when a user uses an invalid word"""
    pass

class MastermindMaxGuess(Exception):
    """Raised when a user reaches the maximum number of guesses"""
    pass

class LFM:
    """Letter Frequency Map, for letter coloring"""

    def __init__(self, word):
        self._map = {}

        for c in word:
            if c not in self._map:
                self._map[c] = 0
            self._map[c] += 1

    def __getitem__(self, key):
        """Functionally similar to a defaultdict"""
        if key in self._map:
            return self._map[key]
        else:
            return 0
    
    def __setitem__(self, key, value):
        self._map[key] = value

    def __and__(self, other: object):
        """Calculates the intersection of two frequency maps"""
        new_lfm = LFM("")

        for c in self._map:
            val = min(self[c], other[c])
            if val != 0:
                new_lfm._map[c] = val
        
        return new_lfm


class MastermindWord:
    """Contains logic for conducting a game of Mastermind"""

    # Loads the daily and general dictionaries
    daily_select = None
    dictionary = None

    with open("daily-words.txt", "r") as d_file:
        dictionary = set(d_file.read().split("\n"))
        daily_select = dictionary.copy()
    with open("dictionary.txt", "r") as g_file:
        dictionary |= set(g_file.read().split("\n"))

    daily_select = list(daily_select)
    dictionary = list(dictionary)

    def __init__(self, max_guess=6, word=None, daily=False):
        self.word = random.choice(
                MastermindWord.daily_select if daily else MastermindWord.dictionary
            ) if word is None else word

        self.lfm = LFM(self.word)
        self.max_guess = max_guess
        self.guess_path = []
    
    def __eq__(self, __o: object) -> bool:
        """Equality for determining if a user has completed a given game already"""
        return self and __o and self.word == __o.word
    
    def __ne__(self, __o: object) -> bool:
        """For use in opposition to eq"""
        return not self or not __o or self.word != __o.word

    def copy(self):
        """Creates a functionally equivalent game that passes __eq__ """
        return MastermindWord(self.max_guess, self.word)

    def current_guesses(self):
        """Returns guesses taken to reach current point"""
        return len(self.guess_path)

    def guess(self, word):
        """
        Executes a guess and stores the result in the game's path
        Returns the results as a tuple of integers, where 0 is no matches, 1 is a partial match, and 2 is a full match
        Raises an MastermindBadWord if the word is invalid or not in the dictionary
        Raises MastermindMaxGuess if the user has hit the maximum number of guesses in this game
        """
        if len(word) != 5 or word not in MastermindWord.dictionary:
            raise MastermindBadWord
        
        intersect_lfm = self.lfm & LFM(word)
        
        res = [0, 0, 0, 0, 0]
        for i, c in enumerate(word):
            if c == self.word[i]:
                res[i] = 2
                intersect_lfm[c] -= 1
        
        for i, c in enumerate(word):
            if not res[i] and intersect_lfm[c]:
                res[i] = 1
                intersect_lfm[c] -= 1

        self.guess_path.append(tuple(res))
        
        if len(self.guess_path) == self.max_guess and not all(x == 2 for x in res):
            raise MastermindMaxGuess

        return tuple(res)
    
    def path_string(self):
        """Returns a string of emojis representing the path taken to reach this point"""
        return "\n".join(MastermindWord.res_to_emojis(res) for res in self.guess_path)

    @staticmethod
    def res_to_emojis(res):
        """Converts a result into a string of emojis"""
        lookup = [":black_large_square:", ":yellow_square:", ":green_square:"]
        return "".join(lookup[i] for i in res)