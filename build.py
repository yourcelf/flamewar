#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from PIL import Image, ImageDraw, ImageFont
import yaml

BASE = os.path.dirname(__file__)
#FONT = "/usr/share/fonts/truetype/msttcorefonts/Courier_New.ttf"
#FONT = "/usr/share/fonts/truetype/msttcorefonts/Andale_Mono.ttf"
FONT = "/usr/share/fonts/truetype/ubuntu-font-family/UbuntuMono-R.ttf"
#FONT = "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansMono.ttf"
#FONT = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
#FONT = "/usr/share/fonts/truetype/ttf-liberation/LiberationMono-Regular.ttf"

class Card(object):
    density = 300

    def  __init__(self, width=2.5, height=3.5):
        self.im = Image.new(
                'RGBA',
                (int(width * self.density), int(height * self.density)),
                (255, 255, 255, 255),
        )

    def draw_wrapped_text(self, text, boundaries, rev_indent="", par_height=1,
            font_size=48,
            font_path=FONT):
        font = ImageFont.truetype(font_path, font_size)
        x, y = [a * self.density for a in boundaries[0]]
        mx, my = [a * self.density for a in boundaries[1]]
        width = mx - x

        ypos = y
        paragraphs = text.split("\n")
        draw = ImageDraw.Draw(self.im)
        for par in paragraphs:
            if not par.strip():
                ypos += font.getsize("M")[1] * par_height
                continue
            words = par.split()
            i = 0
            while True:
                if len(words) == 0:
                    break
                fsize = font.getsize(" ".join(words[:i + 1]))
                if fsize[0] > width or i >= len(words):
                    text = " ".join(words[:i])
                    draw.text((x, ypos), text, fill=(0, 0, 0), font=font)
                    ypos = ypos + fsize[1]
                    words = words[i:]
                    if rev_indent and len(words):
                        words[0] = rev_indent + words[0]
                    i = 0
                i += 1

    def load_background(self, filepath):
        bg = Image.open(filepath).resize(self.im.size)
        self.im.paste(bg, (0, 0) + self.im.size)

    def save(self, filename, fmt=None):
        return self.im.save(filename, fmt)

class GoalCard(Card):
    def __init__(self, goal_type, goal, lights, *args, **kwargs):
        super(GoalCard, self).__init__(*args, **kwargs)
        self.load_background(os.path.join(BASE, "images", "goal.png"))
        self.draw_wrapped_text(goal_type.upper(), ((0.32, 0.64), (2.22, 0.86)), font_size=48)
        self.draw_wrapped_text(goal, ((0.33, 0.96), (2.25, 1.95)), font_size=40)
        # Draw stars
        rows = 2 if lights > 4 else 1
        star = Image.open(os.path.join(BASE, "images", "light.png"))
        star_dims = (0.25, 0.25)
        box = ((0.29, 2.41), (2.25, 3.18))
        start_x = box[0][0] + (box[1][0] - box[0][0]) / 2 - star_dims[0] * (lights/rows/2.0)
        start_y = box[1][0] + (box[1][1] - box[1][0]) / 2 - star_dims[1] * (rows/2.0)
        for r in range(rows):
            for i in range(lights / rows):
                dims = [int(self.density * a) for a in (
                    start_x + star_dims[0] * i,
                    start_y + star_dims[1] * r,
                    start_x + star_dims[0] * (i + 1),
                    start_y + star_dims[1] * (r + 1),
                )]
                self.im.paste(star, dims)

class EmailCard(Card):
    def __init__(self, subject, message, lights, flames, *args, **kwargs):
        super(EmailCard, self).__init__(*args, **kwargs)
        self.load_background(os.path.join(BASE, "images", "email.png"))
        self.draw_wrapped_text(str(flames), ((1.55, 0.18), (1.86, 0.39)), font_size=64)
        self.draw_wrapped_text(str(lights), ((1.97, 0.18), (2.25, 0.39)), font_size=64)
        self.draw_wrapped_text(subject, ((0.30, 0.43), (2.16, 1.59)), font_size=36)
        self.draw_wrapped_text(message, ((0.27, 0.70), (2.27, 3.25)), font_size=36)

class InterruptCard(Card):
    def __init__(self, title, description, *args, **kwargs):
        super(InterruptCard, self).__init__(*args, **kwargs)
        self.load_background(os.path.join(BASE, "images", "interrupt.png"))
        self.draw_wrapped_text(title, ((0.25, 0.85), (2.25, 1.35)), font_size=64)
        self.draw_wrapped_text(description, ((0.25, 1.35), (2.25, 3.25)), font_size=40)

class AttentionCard(Card):
    def __init__(self, description, *args, **kwargs):
        # Do this one landscape mode.
        super(AttentionCard, self).__init__(*args, width=3.5, height=2.5, **kwargs)
        self.load_background(os.path.join(BASE, "images", "attention.png"))
        self.draw_wrapped_text(description, ((0.25, 0.85), (2.80, 2.25)), font_size=48)
        self.im = self.im.rotate(90)

def build():
    out = os.path.join(BASE, "cards")
    try:
        os.makedirs(out)
    except OSError:
        pass
    with open("cards.yaml") as fh:
        defs = yaml.load(fh)

    count = 0
    for goal_type, goalinfo in defs['goals'].items():
        for card in goalinfo['cards']:
            GoalCard(
                lights=goalinfo['lights'],
                goal_type=goal_type,
                goal=card,
            ).save(
                os.path.join(out, "goal-%s.png" % count)
            )
            count += 1

    count = 0
    for email in defs['action']['email']:
        EmailCard(**email).save(os.path.join(out, "email-%s.png" % count))
        count += 1

    count = 0
    # Double-up on interrupt cards.
    for i in range(2):
        for interrupt in defs['action']['interrupt']:
            InterruptCard(**interrupt).save(os.path.join(out, "interrupt-%s.png" % count))
            count += 1

    count = 0
    for attention in defs['attention']:
        AttentionCard(attention).save(os.path.join(out, "attention-%s.png" % count))
        count += 1

if __name__ == "__main__":
    build()
