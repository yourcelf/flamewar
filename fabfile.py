import os
from PIL import Image
from fabric.api import *

BASE = os.path.dirname(__file__)

def build():
    with lcd(BASE):
        with settings(warn_only=True):
            local("rm cards/*")
        local("python build.py")

def fetch_build():
    """ Fetch the card defs from an etherpad. """
    with lcd(BASE):
        local("curl -L https://pad.tirl.org:444/p/byconsensus-flamewar-yaml/export/txt > cards.yaml")
        build()

def print_prep():
    """ 
    Prepare for printing on 8.5x11 cardstock. Combine 2.5x3.5 images 3x3.
    """
    outdir = os.path.join(BASE, "print")
    with lcd(BASE):
        local("rm -r %s" % outdir)
        local("mkdir -p %s" % outdir)
    card_dir = os.path.join(BASE, "cards")
    images = [os.path.join(card_dir, f) for f in sorted(os.listdir(card_dir))]
    first = Image.open(images[0])
    for i in range(0, len(images), 9):
        out = Image.new(
                'RGBA', 
                (first.size[0] * 3, first.size[1] * 3), 
                (255,255,255,255)
        )
        for j in range(0, 9):
            if i + j < len(images):
                im = Image.open(images[i + j])
                out.paste(Image.open(images[i + j]), 
                        (
                            im.size[0] * (j % 3),
                            im.size[1] * (int(j / 3)),
                            first.size[0] * (j % 3 + 1),
                            first.size[1] * (int(j / 3) + 1),
                        )
                )
        out.save(os.path.join(outdir, "card-%i.png" % i))
