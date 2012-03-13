import os

from PIL import Image, ImageDraw, ImageFont
import yaml

BASE = os.path.dirname(__file__)
FONT = "/usr/share/fonts/truetype/msttcorefonts/Courier_New.ttf"
FONT = "/usr/share/fonts/truetype/msttcorefonts/Andale_Mono.ttf"

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

    def decorate(self):
        raise NotImplementedError

class GoalCard(Card):
    def __init__(self, goal_type, requirements, goal, *args, **kwargs):
        super(GoalCard, self).__init__(*args, **kwargs)
        self.draw_wrapped_text(goal_type.upper(), ((0.25, 0.25), (2, 0.5)), font_size=48)
        self.draw_wrapped_text(goal, ((0.25, 0.5), (2.25, 2.5)), font_size=40)
        self.draw_wrapped_text(requirements, ((0.25, 2.5), (2.25, 3.25)))

class EmailCard(Card):
    def __init__(self, subject, message, lights, flames, *args, **kwargs):
        super(EmailCard, self).__init__(*args, **kwargs)
        self.load_background(os.path.join(BASE, "images", "email.png"))
        self.draw_wrapped_text(str(flames), ((1.71, 0.27), (1.86, 0.39)), font_size=36)
        self.draw_wrapped_text(str(lights), ((1.97, 0.27), (2.25, 0.39)), font_size=36)
        self.draw_wrapped_text(subject, ((0.30, 0.43), (2.16, 1.59)), font_size=36)
        self.draw_wrapped_text(message, ((0.27, 0.70), (2.27, 3.25)), font_size=36)

class InterruptCard(Card):
    def __init__(self, title, description, *args, **kwargs):
        super(InterruptCard, self).__init__(*args, **kwargs)
        self.load_background(os.path.join(BASE, "images", "interrupt.png"))
        self.draw_wrapped_text(title, ((0.25, 0.85), (2.25, 1.35)), font_size=64)
        self.draw_wrapped_text(description, ((0.25, 1.35), (2.25, 3.25)), font_size=36)

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
    for goaltype, goalinfo in defs['goals'].items():
        for goal in goalinfo['cards']:
            GoalCard(goaltype, goalinfo['requirements'], goal).save(
                os.path.join(out, "goal-%s.png" % count)
            )
            count += 1

    count = 0
    for email in defs['action']['email']:
        EmailCard(**email).save(os.path.join(out, "email-%s.png" % count))
        count += 1

    count = 0
    for interrupt in defs['action']['interrupt']:
        InterruptCard(**interrupt).save(os.path.join(out, "interrupt-%s.png" % count))
        count += 1

    count = 0
    for attention in defs['attention']:
        AttentionCard(attention).save(os.path.join(out, "attention-%s.png" % count))
        count += 1

if __name__ == "__main__":
    build()
