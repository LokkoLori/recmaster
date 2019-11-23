# -*- coding: utf-8 -*-

import jsonpickle
import json
from random import randrange
from shutil import copyfile
import shlex
import sys

def rec_random(i):
    return randrange(i)

SESSIN_FILE = ".recsession"

class MatchPoint:

    def __init__(self, competitor, isWinner, result):

        self.competitor = competitor
        self.isWinner = isWinner
        self.result = result

class Match:

    def __init__(self, pair):

        self.pair = pair
        self.rounds = []


class TurnRule:

    def __init__(self, matchNumToWin, greaterIsBetter):

        self.matchNumToWin = matchNumToWin
        self.greaterIsBetter = greaterIsBetter

class Turn:

    def __init__(self, name, competitors, rule):

        self.name = name
        self.competitors = competitors
        self.rule = rule
        self.matches = []
        self.winners = []


    def matchMaking(self):

        if len(self.competitors) < 2:
            raise Exception("No competitor left")

        pair = []
        for p in range(2):

            i = rec_random(len(self.competitors))
            pair.append(self.competitors[i])
            del self.competitors[i]

        print("left seat: {0} right seat: {1}".format(pair[0], pair[1]))
        self.matches.append(Match(pair))

    def changePlayer(self, right):

        if not self.matches:
            raise Exception("There's not active match in play")

        if not self.competitors:
            raise Exception("There's no player ramins")

        actMatch = self.matches[-1]

        if actMatch.rounds:
            raise Exception("The match is already started")

        changedPlayer = actMatch.pair[right]

        i = rec_random(len(self.competitors))
        actMatch.pair[right] = self.competitors[i]
        del self.competitors[i]
        self.competitors.append(changedPlayer)

        print("left seat: {0} right seat: {1}".format(actMatch.pair[0], actMatch.pair[1]))

    def switchPlayers(self):

        if not self.matches:
            raise Exception("There's not active match in play")

        actMatch = self.matches[-1]

        splayer = actMatch.pair[0]
        actMatch.pair[0] = actMatch.pair[1]
        actMatch.pair[1] = splayer

        print("left seat: {0} right seat: {1}".format(actMatch.pair[0], actMatch.pair[1]))


    def matchResult(self, winner, points, isCorrection=False):

        if not self.matches:
            raise Exception("There's not active match in play")

        actMatch = self.matches[-1]

        if isCorrection:
            pass

        matchPointPair = []
        for p in range(2):
            mp = MatchPoint(actMatch.pair[p], p==winner, points[p])
            matchPointPair.append(mp)

        actMatch.rounds.append(matchPointPair)

        matchWinner = None
        for p in range(2):
            competitor = actMatch.pair[p]
            wonn = 0
            for r in actMatch.rounds:
                for mp in r:
                    if mp.competitor == competitor and mp.isWinner:
                        wonn += 1
                        if wonn >= self.rule.matchNumToWin:
                            matchWinner = competitor

        if matchWinner:
            print("the winner is "+matchWinner)
            self.winners.append(matchWinner)
            return True

        return False

    def newTurn(self):

        if self.competitors:
            raise Exception("There are remaining competitors in the turn")

        if len(self.winners) > 1 and len(self.winners) % 2 == 1:
            hopeBoard = {}
            for m in self.matches:
                for r in m.rounds:
                    for pi in range(2):
                        p = r[pi]
                        if p.competitor in self.winners:
                            continue
                        if p.competitor not in hopeBoard:
                            hopeBoard[p.competitor] = []
                        hopeBoard[p.competitor].append(p.result)

            for h in hopeBoard:
                hopeBoard[h] = sorted(hopeBoard[h], reverse=not self.rule.greaterIsBetter)

            if self.rule.greaterIsBetter:
                hopewinner = max(hopeBoard.items(), key=lambda x: x[1])[0]
            else:
                hopewinner = min(hopeBoard.items(), key=lambda x: x[1])[0]

            print("the hopewinner is " + hopewinner)
            self.winners.append(hopewinner)

        name = self.name + "+"
        if len(self.winners) == 4:
            name = "elődöntő"
        elif len(self.winners) == 2:
            name = "döntő"

        print(name + " has been started with headcount of " + str(len(self.winners)))
        return Turn(name, list(self.winners), TurnRule(self.rule.matchNumToWin, self.rule.greaterIsBetter))


class Tournamet:

    def __init__(self, name, firstTurn):
        self.name = name
        self.turns = [firstTurn]


    def save(self, fn=None):

        if not fn:
            fn = self.name #todo: conversion needed
        try:
            copyfile(fn, fn+".bak")
        except Exception as e:
            pass

        jsonstr = jsonpickle.encode(self)
        obj = json.loads(jsonstr)
        with open(fn, "w") as f:
            json.dump(obj, f, indent=4)

        with open(SESSIN_FILE, "w") as f:
            f.write(fn)

    @staticmethod
    def load(fn):
        with open(fn) as f:
            retobj = jsonpickle.decode(f.read())

        with open(SESSIN_FILE, "w") as f:
            f.write(fn)

        return retobj


def main(args):

    tournament = None
    turn = None

    if args:
        tournament = Tournamet.load(args[0])
    else:
        try:
            with open(SESSIN_FILE) as f:
                fn = f.read()
                tournament = Tournamet.load(fn)
                turn = tournament.turns[-1]
        except Exception as e:
            pass

    while(1):
        input = raw_input("r.e.c: ")
        c = shlex.split(input)

        if not c:
            continue

        if c[0] == "c" or c[0] == "create":
            name = c[1]
            competitors = c[2:-2]
            rule = TurnRule(int(c[-2]), int(c[-1]))
            turn = Turn("selejtező", competitors, rule)
            tournament = Tournamet(name, turn)
            turn.matchMaking()

        if c[0] == "ap":
            turn.competitors += c[1:]

        if c[0] == "sp":
            turn.switchPlayers()

        if c[0] == "cp":
            turn.changePlayer(int(c[1]))

        if c[0] == "r":

            over = turn.matchResult(int(c[1]), [int(c[2]), int(c[3])])
            if over:
                if turn.competitors:
                    turn.matchMaking()
                else:
                    if len(turn.winners) == 1:
                        print("we have a champion!!!")
                        tournament.save()
                        exit(0)

                    turn = turn.newTurn()
                    tournament.turns.append(turn)
                    tournament.turns.append(turn)
                    turn.matchMaking()

        if tournament:
            tournament.save()

if __name__ == "__main__":

    main(sys.argv[1:])




