import logging
from time import time, sleep
from random import randrange
from flask.ext.script import Command

from app.services.mbgame_service import MBGameService


logger = logging.getLogger(__name__)
WORKER_PERIOD_SECONDS = 3  # Run every five seconds


class AiWorker(Command):
    previous_run = int(time())
    mbgame_service = MBGameService()

    def run(self):
        while True:
            # Check for games
            active_games = self.mbgame_service.get_active_games()

            # Play games
            for game in active_games:
                if 'piles' not in game:
                    logger.warning('No piles found for game {} with data: {}'.format(game.get('id'), game))
                    continue

                # If there is only one pile left, remove all the beans
                pile, beans = self.last_pile(game['piles'])
                if pile is not None:
                    self.mbgame_service.make_move(game['id'], pile, beans)

                else:
                    sum_bin = self.pile_sum(game['piles'])
                    # If the current pile sum (XOR) is zero, there's no way for us to make it zero,
                    # so we need to just remove a bean from a random pile
                    if sum_bin == 0:
                        self.mbgame_service.make_move(game['id'], randrange(len(game['piles'])), beans=1)
                    else:
                        # Otherwise, find if any pile has all the bits in the sum,
                        # such that we could remove them to create a zero sum
                        #
                        # We find those by creating a mask from an XOR of the piles beans and the pile_sum
                        # and then if a bitwise AND between the sum and the mask results in zero, we have a viable pile
                        for i, num_beans in enumerate(game['piles']):
                            mask = num_beans ^ sum_bin
                            if mask & sum_bin == 0:
                                pile = i
                                break

                        # If we found a pile we can reduce to zero, and we verify we're correct, remove those beans
                        valid_pile = False
                        if pile is not None:
                            game['piles'][pile] -= sum_bin
                            valid_pile = self.pile_sum(game['piles']) == 0
                        if valid_pile:
                            self.mbgame_service.make_move(game['id'], pile, beans=sum_bin)
                        else:
                            # Otherwise, just remove a bean from a random pile
                            self.mbgame_service.make_move(game['id'], randrange(len(game['piles'])), beans=1)

            # Sleep
            current_time = int(time())
            run_seconds = current_time - self.previous_run
            self.previous_run = current_time
            sleep_seconds = WORKER_PERIOD_SECONDS - run_seconds
            if sleep_seconds > 0:
                logger.info('Next run in {} seconds. Took {} seconds to run'.format(sleep_seconds, run_seconds))
                sleep(sleep_seconds)

    @staticmethod
    def pile_sum(piles):
        sum_bin = 0
        for num_beans in piles:
            # To perform a bitwise summation where we don't round, we're really talking about a bitwise XOR
            sum_bin = sum_bin ^ num_beans

        return sum_bin

    @staticmethod
    def last_pile(piles):
        pile = None
        beans = None
        # Look through all piles to see if all but one are empty, and return the non-empty pile in that case
        for i, num_beans in enumerate(piles):
            if num_beans > 0:
                # If we already found a non-empty pile, reset pile to None and break out of the loop
                if pile is not None:
                    pile = None
                    break

                # Record which pile is not empty and how many beans are left
                pile = i
                beans = num_beans

        # If we found a sole non-empty pile then we return it
        if pile is None:
            return None, None

        return pile, beans




