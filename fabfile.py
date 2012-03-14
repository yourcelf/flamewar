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
    Prepare for printing on 5x7 cardstock. Combine 2.5x3.5 images four by four.
    """
    outdir = os.path.join(BASE, "print")
    with lcd(BASE):
        local("rm -r %s" % outdir)
        local("mkdir -p %s" % outdir)
    card_dir = os.path.join(BASE, "cards")
    images = [os.path.join(card_dir, f) for f in sorted(os.listdir(card_dir))]
    first = Image.open(images[0])
    for i in range(0, len(images), 4):
        out = Image.new(
                'RGBA', 
                (first.size[0] * 2, first.size[1] * 2), 
                (255,255,255,255)
        )
        for j in range(0, 4):
            if i + j < len(images):
                im = Image.open(images[i + j])
                out.paste(Image.open(images[i + j]), 
                        (
                            im.size[0] * (j % 2),
                            im.size[1] * (int(j / 2)),
                            first.size[0] * (j % 2 + 1),
                            first.size[1] * (int(j / 2) + 1),
                        )
                )
        out.save(os.path.join(outdir, "card-%i.png" % i))
