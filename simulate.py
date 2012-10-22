#!/usr/bin/env python

"""
This script simulates the game of flamewar, for the purpose of fine-tuning the
scoring.
"""
import re
import os
import yaml
import random
from matplotlib import pyplot

def draw(number, pile):
    return [pile.pop(random.randint(0, len(pile) - 1)) for i in range(number)]

class AttentionPileEmpty(Exception):
    pass
class EmailPileEmpty(Exception):
    pass
class GoalPileEmpty(Exception):
    pass

class Game(object):
    def __init__(self, num_goals=2, num_players=6):
        self.rounds = 0
        self.goal_pile         = []
        self.goal_discard      = []
        self.email_pile        = []
        self.email_discard     = []
        self.interrupt_discard = []
        self.attention_pile    = []
        self.attention_discard = []
        data = yaml.load(
            open(os.path.join(os.path.dirname(__file__), "cards.yaml"))
        )
        # Goals
        for name,props in data['goals'].iteritems():
            lights = props['lights']
            for card in props['cards']:
                self.goal_pile.append(Goal(lights, card))

        # Emails
        for kind, props in data['action'].items():
            if kind == 'email':
                for email in props:
                    self.email_pile.append(
                            Email(email['lights'], email['flames'], email['subject'])
                    )
        #self.email_pile += self.email_pile[:30]

        # Interrupts
        self.email_pile += [
            flamewar(), epicthread(), misdelivered(), voluntold(),
            flamewar(), epicthread(), misdelivered(), voluntold(),
        ]
        random.shuffle(self.email_pile)

        # Attention
        for flavor in data['attention']:
            read_match = re.search("Read (\d+)", flavor)
            send_match = re.search("Send (\d+)", flavor)
            self.attention_pile.append(
                Attention(
                    int(read_match.group(1)), 
                    int(send_match.group(1)) if send_match else 2,
                    flavor)
            )
        #self.attention_pile *= 2

        self.players = [Player(self) for p in range(num_players)]
        self.current_player = 0
        self.goals = draw(num_goals, self.goal_pile)


    def play(self):
        while True:
            self.rounds += 1
            try:
                attention = draw(1, self.attention_pile)[0]
            except ValueError:
                raise AttentionPileEmpty()
            self.attention_discard.append(attention)
            for i in range(attention.read):
                self.players[self.current_player].read_email()
            for i in range(attention.send):
                self.players[self.current_player].send_email()

            if random.random() < 0.1:
                random.choice(self.players).play_interrupt()
            #print "---------------------"
            #self.print_state()
            #import pdb; pdb.set_trace()
            self.current_player += 1
            self.current_player %= len(self.players)
    
    def print_state(self):
        print "Piles:"
        print " email: {0}/{1}".format(len(self.email_pile), len(self.email_discard))
        print " attin: {0}/{1}".format(len(self.attention_pile), len(self.attention_discard))
        print " goals: {0}/{1}".format(len(self.goal_pile), len(self.goal_discard))
        print "Goals:"
        for g in self.goals:
            email_repr = []
            for e in g.emails:
                if e.read:
                    email_repr.append(unicode(e))
                else:
                    email_repr.append("()")
            print "  {lights}/{ltotal}, {flames}/{ftotal}: {emails}".format(
                lights=g.lights_count(),
                ltotal=g.num_lights,
                flames=g.flames_count(),
                ftotal=g.max_flames,
                emails=", ".join("(%s)" % e for e in email_repr)
            )
        print "Players:"
        for i,p in enumerate(self.players):
            up = "*" if i == self.current_player else " "
            print " {up}{i}: {points}pts; [{emails}]".format(
                up=up,
                i=i,
                points=p.get_points(),
                emails=", ".join(unicode(e) for e in p.hand)
            )

class Goal(object):
    max_flames = 3

    def __init__(self, num_lights, flavor=None):
        self.num_lights = num_lights
        self.points = self.num_lights
        self.emails = []
        self.flavor = flavor

    def lights_count(self):
        return sum(e.lights for e in self.emails if e.read)

    def flames_count(self):
        return sum(e.flames for e in self.emails if e.read)

    def is_won(self):
        return self.lights_count() >= self.num_lights

    def is_burned(self):
        return self.flames_count() >= self.max_flames

class Email(object):
    def __init__(self, lights, flames, flavor=None):
        self.lights = lights
        self.flames = flames
        self.flavor = flavor
        self.read = False

    def __unicode__(self):
        return u"({0},{1})".format(self.lights, self.flames)

class Interrupt(object):
    def __call__(self, game):
        pass

    def __unicode__(self):
        return self.flavor

class Attention(object):
    def __init__(self, read, send, flavor=None):
        self.read = read
        self.send = send
        self.flavor = flavor

class flamewar(Interrupt):
    flavor = "Flame war"
    def __call__(self, game):
        goal = random.choice(game.goals)
        goal.is_won = lambda: sum(e.flames for e in goal.emails if e.read) > 10
        goal.is_burned = lambda: False
        goal.points = 10

class epicthread(Interrupt):
    flavor = "Epic thread"
    def __call__(self, game):
        goal = random.choice(game.goals)
        goal.num_lights *= 2
        goal.max_flames *= 2
        goal.points *= 2

class misdelivered(Interrupt):
    flavor = "Misdelivered"
    def __call__(self, game):
        for goal in game.goals:
            for i,email in enumerate(goal.emails):
                if email.read:
                    goal.emails.pop(i)
                    return

class voluntold(Interrupt):
    flavor = "Voluntold"
    def __call__(self, game):
        player = random.choice(game.players)
        player.read_email()
        player.read_email()
        player.send_email()
        player.send_email()

class Player(object):
    def __init__(self, game):
        self.game = game
        self.hand = []
        for i in range(5):
            self.draw()
        self.winnings = []

    def draw(self):
        try:
            self.hand += draw(1, self.game.email_pile)
        except ValueError:
            raise EmailPileEmpty()

    def get_points(self):
        return sum(g.points for g in self.winnings)

    def read_email(self):
        pool = []
        for g in self.game.goals:
            for e in g.emails:
                if not e.read:
                    pool.append(e)
        if len(pool) > 0:
            random.choice(pool).read = True

    def send_email(self):
        goal = random.choice(self.game.goals)
        try:
            email = draw(1, [e for e in self.hand if isinstance(e, Email)])[0]
        except ValueError:
            return
        self.hand.remove(email)
        goal.emails.append(email)
        if goal.is_burned() or goal.is_won():
            self.game.goals.remove(goal)
            try:
                self.game.goals += draw(1, self.game.goal_pile)
            except ValueError:
                raise GoalPileEmpty()
            self.game.email_discard += goal.emails
            if goal.is_burned():
                self.game.goal_discard.append(goal)
            else:
                self.winnings.append(goal)
        self.draw()

    def play_interrupt(self):
        for c in self.hand:
            if isinstance(c, Interrupt):
                c(self.game)
                self.hand.remove(c)
                self.game.interrupt_discard.append(c)
                self.draw()

def mass_run():
    empties = {
        'email': 0,
        'attention': 0,
        'goal': 0,
    }
    scores = []
    winning_scores = []
    flameouts = []
    won_flamewars = []
    lost_flamewars = []
    won_goals = []
    rounds = []
    remaining_email = []
    for i in xrange(100):
        g = Game()
        try:
            g.play()
        except EmailPileEmpty:
            empties['email'] += 1
        except GoalPileEmpty:
            empties['goal'] += 1
        except AttentionPileEmpty:
            empties['attention'] += 1
        scores += [p.get_points() for p in g.players]
        winning_scores.append(max(p.get_points() for p in g.players))
        won_goals.append(sum(len(p.winnings) for p in g.players))
        flameouts.append(len(g.goal_discard))
        won_flamewar_count = 0
        for p in g.players:
            for w in p.winnings:
                if w.points == 10:
                    won_flamewar_count += 1
        won_flamewars.append(won_flamewar_count)
        lost_flamewars.append(
            len([goal for goal in g.goals if goal.points == 10])
        )
        rounds.append(g.rounds)
        remaining_email.append(len(g.email_pile))


    print empties

    pyplot.figure(1)
    i = 1
    for title, thing in [
            ('scores', scores),
            ('winning scores', winning_scores),
            ('flameouts', flameouts),
            ('# of won goals', won_goals),
            ('# of rounds', rounds),
            ('won flamewars', won_flamewars),
            ('lost flamewars', lost_flamewars),
            ('remaining email', remaining_email),
            ]:
        pyplot.subplot(3, 3,  i)
        i += 1
        pyplot.title(title)
        pyplot.hist(thing)

    pyplot.show()

if __name__ == "__main__":
    mass_run()
