# 6. Steps 2 & 3 — the rules, and playing a whole game

In Step 1 the pretend arm moved one piece. Now we teach it real chess and let it
play a full game — still with the pretend arm, still no hardware.

## Step 2 — the awkward chess rules

Most moves are simple: pick a piece up, put it down. But chess has tricky cases:

- **Capturing** — you must first lift the *other* piece off the board, then move.
- **Castling** — two pieces move at once (the king and a rook).
- **En passant** and **promotion** — special pawn rules.

Here's the lesson, and it's a big one: **don't write the chess rulebook
yourself.** There's a free, trusted library called **python-chess** that already
knows every rule perfectly. We just *ask it questions* and translate the answers
into arm actions. For example:

```python
if board.is_capture(move):
    remove_the_piece_first(...)   # lift the captured piece off, then move
```

So instead of hundreds of lines of rules we might get wrong, we ask
python-chess "is this a capture?" and act on its answer. This logic lives in
[`src/chessbot/moves.py`](../src/chessbot/moves.py), and it turns *any* legal
chess move into our simple routine of pick-ups and put-downs.

## Step 3 — give it a brain

Now for the opponent. Remember, we don't write a chess player — we borrow
**Stockfish**, and turn its strength *way* down so a young child can win and have
fun. One setting does it:

```python
engine.configure({"Skill Level": 2})   # 0 = very gentle, 20 = world champion
```

This lives in [`src/chessbot/engine.py`](../src/chessbot/engine.py). (Later, for an
even more human-feeling opponent, you can swap in something called *Maia*, which
plays like a real beginner. Same idea, different brain.)

## Putting it together: the game loop

A game is just taking turns, forever, until someone wins. In plain words:

```
repeat:
    is the game over?  -> say who won, stop
    if it's your child's turn:
        she moves a piece by hand, you type what she did
    if it's the robot's turn:
        the brain picks a move
        the pretend arm plays it (pick up, put down)
```

That's the whole thing. The real version is in
[`src/chessbot/game.py`](../src/chessbot/game.py) (the rules and turns) and
[`play.py`](../play.py) (the part that talks to you).

## Play a full game right now

```bash
.venv/bin/python play.py
```

You'll see the board printed out. When it's your turn, type a move and press
Enter. You can type moves two ways — both work:

- the friendly way: `e4`, `Nf3`, `O-O` (castle)
- the spelled-out way: `e2e4`

Handy commands while you play:

- `hint` — the robot suggests a move for *you* (great for teaching!)
- `board` — print the board again
- `takeback` — undo the last round
- `resign` — give up this game

Want a gentler or tougher robot? Change its skill:

```bash
.venv/bin/python play.py --skill 0     # easiest
.venv/bin/python play.py --skill 6     # a bit tougher
```

## Celebrate 🎉

Stop and notice what you have: **a complete chess robot that plays a full game at
your child's level — and you haven't touched a single wire.** Everything from here
is about making the pretend arm *real*.

---
Back: [Home](Home.md) · Next: [Step 4 — the real arm →](07-step-4-the-real-arm.md)
