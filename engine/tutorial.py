"""A guided first game, in the terminal, with nothing else needed.

Runs entirely on the phone: no browser, no wifi, no GitHub. Ten short lessons
that build a real playable game one row at a time. You choose the tiles
yourself -- being told which tile to use teaches nothing -- and you play what
you have built at four points along the way.

    python3 spark.py tutorial
"""

from . import brain, runner
from .builder import CLEAR, ask, ask_yes, header, menu

PAUSE = "press enter to go on "


# --------------------------------------------------------------------------
# presentation
# --------------------------------------------------------------------------

def lesson(number, title, *paragraphs):
    print(CLEAR + "=" * 46)
    print(" Lesson %d of 10 -- %s" % (number, title))
    print("=" * 46 + "\n")
    for text in paragraphs:
        print(wrap(text) + "\n")


def wrap(text, width=44, indent=" ", hang=None):
    """Fold text to the screen. A line that starts indented is left alone."""
    if text.startswith("    "):
        return text
    hang = indent if hang is None else hang
    words, line, out = text.split(), "", []
    for word in words:
        if len(line) + len(word) + 1 > width:
            out.append((indent if not out else hang) + line)
            line = word
        else:
            line = (line + " " + word).strip()
    out.append((indent if not out else hang) + line)
    return "\n".join(out)


def bullet(text):
    return wrap("- " + text, width=42, indent="  ", hang="    ")


def quiz(question, options, correct, why):
    """Ask until they get it. Being wrong is explained, never punished."""
    print(wrap(question) + "\n")
    while True:
        index = menu(options, "which one", allow_back=False)
        if index == correct:
            print("\n " + wrap(why).strip() + "\n")
            ask(PAUSE)
            return
        print("\n " + wrap("Not that one. " + options[correct] +
                           " is what we want here -- try again.").strip() + "\n")


def show_brain(character):
    print(" %s's brain now:" % character["kind"])
    if not character["brain"]:
        print("   (empty)")
    for row in character["brain"]:
        print("   " + brain.describe_row(row))
    print()


def playtest(project, note):
    print(wrap(note) + "\n")
    if ask_yes(" Try it now", True):
        runner.play(project)


def row(when, do):
    return {"when": when, "do": do}


def tile(name, **args):
    return {"tile": name, "args": args}


# --------------------------------------------------------------------------
# the lessons
# --------------------------------------------------------------------------

def run():
    project = brain.new_project("mygame")

    # -- 1 ----------------------------------------------------------------
    lesson(1, "What a game is here",
           "A game is a cast of characters. Each character has a brain. "
           "A brain is a list of rows, and every row reads the same way:",
           "    WHEN something is true   DO something",
           "That is the whole system. Everything you build is rows of that "
           "shape. You will have a playable game in about ten minutes, and "
           "you will not type any code.",
           "This runs entirely on your phone. No internet is involved.")
    ask(PAUSE)

    # -- 2 ----------------------------------------------------------------
    lesson(2, "Your character",
           "First you need somebody to be. Characters are drawn as a single "
           "letter or symbol on a grid.")
    glyph = (ask(" One letter or symbol for your hero", "@") or "@")[:1]
    hero = brain.new_character("hero", glyph)
    hero.update({"color": "cyan", "health": 3, "count": 1, "role": "player"})
    project["characters"].append(hero)
    print("\n " + wrap("Your hero is '%s'. Its role is player, which means the "
                       "game ends if it dies. Health 3, so it can take three "
                       "hits." % glyph).strip() + "\n")
    ask(PAUSE)

    # -- 3 ----------------------------------------------------------------
    lesson(3, "Making it move",
           "Right now your hero just stands there, because its brain is "
           "empty. A character does nothing unless a row tells it to.",
           "To move when you press the up arrow, you need a row whose WHEN "
           "half notices the key.")
    quiz("Which WHEN tile notices a key being pressed?",
         ["always", "key <key> is pressed", "every <n> ticks"], 1,
         "Right. 'always' fires every single tick, and 'every n ticks' fires "
         "on a timer -- neither one cares what you press.")
    for key, direction in (("up", "up"), ("down", "down"),
                           ("left", "left"), ("right", "right")):
        hero["brain"].append(row([tile("key", key=key)],
                                 [tile("move", dir=direction)]))
    print(CLEAR)
    print(" I have added all four directions for you:\n")
    show_brain(hero)
    print(wrap("Notice they are four separate rows. Rows do not interfere "
               "with each other; each one is read every tick and fires if its "
               "WHEN half is true.") + "\n")
    playtest(project, "You can drive your hero around now. Press q to come "
                      "back when you have had enough.")

    # -- 4 ----------------------------------------------------------------
    lesson(4, "Something to collect",
           "An empty world is dull. Let us add apples. Apples need no brain "
           "at all -- they only have to sit there and be collected.")
    apple = brain.new_character("apple", "o")
    apple.update({"color": "green", "count": 5})
    project["characters"].append(apple)
    print(" " + wrap("Five apples, drawn as 'o', added. They have an empty "
                     "brain, which is perfectly normal.").strip() + "\n")
    ask(PAUSE)

    # -- 5 ----------------------------------------------------------------
    lesson(5, "Picking them up",
           "Walking over an apple should score a point and make the apple "
           "vanish. That is one row with two DO tiles in it.",
           "A row can hold several DO tiles. They all run when the row "
           "fires.")
    quiz("Which WHEN tile notices you are standing on an apple?",
         ["I see <kind> within <n>", "I am touching <kind>",
          "the score is at least <n>"], 1,
         "Yes. 'I see' notices things at a distance; 'I am touching' means "
         "right next to you, which is what picking something up means.")
    hero["brain"].append(row(
        [tile("touch", kind="apple")],
        [tile("score", amount=1), tile("vanish", target="it"),
         tile("say", text="yum!")]))
    print(CLEAR)
    show_brain(hero)
    print(wrap("Read that last row aloud and it says what it does. That is "
               "the point of the whole system.") + "\n")
    playtest(project, "Go and eat some apples. Watch the score.")

    # -- 6 ----------------------------------------------------------------
    lesson(6, "The most important word: it",
           "Look at that row again: 'make it disappear'. Which apple is 'it'?",
           "'it' is whatever the WHEN half found. 'I am touching apple' finds "
           "the apple you touched and hands it to the DO tiles. Without that, "
           "the row could not know which apple to remove.",
           "The tiles that find an 'it' are 'I see' and 'I am touching'. The "
           "tiles that use it are 'move toward it', 'hurt it', and 'make it "
           "disappear'.",
           "This is the piece that makes tiles connect to each other instead "
           "of just sitting side by side.")
    ask(PAUSE)

    # -- 7 ----------------------------------------------------------------
    lesson(7, "Winning",
           "A game needs an ending. There are five apples, so eating all "
           "five should win it.")
    quiz("Which WHEN tile checks how many points you have?",
         ["my health is below <n>", "the score is at least <n>",
          "<n>% of the time"], 1,
         "Correct. It becomes true the moment your score reaches the number, "
         "and the row fires.")
    hero["brain"].append(row([tile("score_at_least", value=5)],
                             [tile("win")]))
    print(CLEAR)
    show_brain(hero)
    playtest(project, "Eat all five apples and the game should announce that "
                      "you have won.")

    # -- 8 ----------------------------------------------------------------
    lesson(8, "An enemy",
           "Now something to avoid. A bug that chases you needs a row that "
           "finds you and a row that moves toward what it found.")
    bug = brain.new_character("bug", "B")
    bug.update({"color": "red", "health": 2, "count": 2})
    project["characters"].append(bug)
    quiz("The bug must notice you from across the room. Which WHEN tile?",
         ["I am touching <kind>", "I see <kind> within <n>", "always"], 1,
         "Right. 'I see hero within 8' finds you up to eight squares away, "
         "and hands you over as 'it'.")
    bug["brain"].append(row(
        [tile("timer", every=2), tile("see", kind="hero", range=8)],
        [tile("move", dir="toward it")]))
    print(CLEAR)
    show_brain(bug)
    print(wrap("That row has two WHEN tiles, which means AND: both must be "
               "true. 'every 2 ticks' is what stops the bug being as fast as "
               "you are. Take it out and the bug becomes impossible to "
               "escape -- that is how you tune difficulty here.") + "\n")
    ask(PAUSE)

    # -- 9 ----------------------------------------------------------------
    lesson(9, "Getting hurt",
           "A chase with no consequence is not much of a chase. When the bug "
           "reaches you it should take a heart off you.",
           "Your hero has 3 health, and is the only character whose role is "
           "player, so when it runs out the game is lost.")
    bug["brain"].append(row(
        [tile("timer", every=4), tile("touch", kind="hero")],
        [tile("damage", target="it", amount=1),
         tile("say", text="the bug bit you!")]))
    print(CLEAR)
    show_brain(bug)
    print(wrap("'every 4 ticks' again, so standing next to a bug costs you a "
               "heart now and then rather than instantly ending the game.")
          + "\n")
    playtest(project, "This is a real game now: five apples to win, two bugs "
                      "trying to stop you.")

    # -- 10 ---------------------------------------------------------------
    lesson(10, "It is yours now",
           "You built every row of that. Give it a name and it is saved with "
           "your other games.")
    name = (ask(" Name your game", "mygame") or "mygame").strip()
    project["name"] = "".join(c for c in name if c.isalnum() or c in "-_ ") or "mygame"
    path = brain.save(project, brain.GAMES_DIR / (project["name"] + ".json"))

    print(CLEAR + "=" * 46)
    print(" Saved as %s.json" % project["name"])
    print("=" * 46 + "\n")
    print(wrap("Play it any time:") + "\n")
    print("   python3 spark.py play games/%s.json\n" % project["name"])
    print(wrap("Things worth trying next, all from the main menu:") + "\n")
    for idea in ("Give the bugs a 'shoot' row and see what happens.",
                 "Add a wall character, make it solid, count 10.",
                 "Change 'every 2 ticks' on the bug to 1 and regret it.",
                 "Give your hero 'WHEN health below 2 DO say run away'.",
                 "Open the same game in the drag-and-drop editor: "
                 "python3 spark.py edit"):
        print(bullet(idea))
    print()
    print(wrap("The tile list is in README.md, and MANUAL.md has every "
               "control and command.") + "\n")
    ask(" press enter to finish ")
    return str(path)
