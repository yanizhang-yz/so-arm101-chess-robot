# 5. Step 1 — find a square (paper → code)

This is the foundation everything else sits on. We'll figure it out on paper
first, then turn it into code. Grab a pen.

## The question

Before a robot can pick up the piece on **e2**, it needs to know *where e2 is* in
the real world — how far over, and how far up. Let's work it out.

## On paper

Sketch the board and mark one corner, **a1**, as our starting point ("zero"):

```
8  .  .  .  .  .  .  .  .
7  .  .  .  .  .  .  .  .
6  .  .  .  .  .  .  .  .
5  .  .  .  .  .  .  .  .
4  .  .  .  .  .  .  .  .
3  .  .  .  .  .  .  .  .
2  .  .  .  .  *  .  .  .     ← * is e2
1  O  .  .  .  .  .  .  .     ← O is a1, our starting corner (0, 0)
   a  b  c  d  e  f  g  h
```

**The key insight:** a chessboard is just a grid, and every square is the same
size. So if we know one corner and the size of a square, we can find *any* square
just by counting over and up.

We count *from* the a1 corner, starting at zero:

- Letters (going right): a = 0, b = 1, c = 2, d = 3, **e = 4**, f = 5, g = 6, h = 7
- Numbers (going up): rank 1 = 0, **rank 2 = 1**, rank 3 = 2, … rank 8 = 7

Say each square is **4 cm**. The rule is:

- how far **right** = (letter count) × 4 cm
- how far **up** = (number count) × 4 cm

**Let's do e2 together:** e is 4 steps over, rank 2 is 1 step up.
- right = 4 × 4 = **16 cm**
- up = 1 × 4 = **4 cm**

So **e2 is 16 cm right and 4 cm up from the a1 corner.** That's the spot the
gripper hovers over. We turned a chess name into a real location with counting and
one multiplication. ✨

### Your turn (the answer, since this is the manual)

Where is **d4**? d is the 4th letter → **3** steps over. Rank 4 → **3** steps up.
- right = 3 × 4 = **12 cm**
- up = 3 × 4 = **12 cm**

So d4 is **12 cm right, 12 cm up**. If that's what you got — you've got it. 🎉

## The second piece of paper: the pick-up routine

Once we can find a square, *picking up a piece is always the same little routine.*
Write it as a checklist:

1. move to **above** the square (a few cm up — call it "hover")
2. **open** the gripper
3. **lower** straight down onto the piece
4. **close** the gripper (grab)
5. **lift** back up to hover

Putting a piece down is the same in reverse: hover above the target, lower, open
(let go), lift. The important habit: **always come down from above and lift
before traveling**, so the arm never drags across the board and knocks pieces
over.

That's the whole design for Step 1: *a way to find any square*, plus *a fixed
routine to move a piece*.

## Now turn it into code

Here's the beautiful part — the code is almost word-for-word the paper.

**Finding a square** (this lives in [`src/chessbot/board.py`](../src/chessbot/board.py)).
Computers prefer **meters**, so 4 cm becomes `0.04`, and 16 cm becomes `0.16` —
same thing, different unit:

```python
FILES = "abcdefgh"

def square_center(square, square_size=0.04):     # square_size in meters (4 cm)
    file_letter = square[0]            # "e"
    rank_number = int(square[1])       # 2
    x = FILES.index(file_letter) * square_size    # 4 * 0.04 = 0.16  (16 cm right)
    y = (rank_number - 1) * square_size           # 1 * 0.04 = 0.04  (4 cm up)
    return (x, y)
```

`FILES.index("e")` is just the computer counting that "e" is the 4th letter (from
0) — exactly what you did by hand.

**The pretend arm** (in [`src/chessbot/arm.py`](../src/chessbot/arm.py)) just
prints:

```python
class MockArm:
    def goto(self, x, y, z):     print(f"   arm: go to {x}, {y}, height {z}")
    def open_gripper(self):      print("   arm: open")
    def close_gripper(self):     print("   arm: close")
```

**The routine** (in [`src/chessbot/motion.py`](../src/chessbot/motion.py)) is your
checklist, line for line:

```python
def pick_up(arm, x, y):
    arm.goto(x, y, HOVER)     # 1. above the square
    arm.open_gripper()        # 2. open
    arm.goto(x, y, DOWN)      # 3. lower onto the piece
    arm.close_gripper()       # 4. grab
    arm.goto(x, y, HOVER)     # 5. lift
```

That's it. Paper → code, with almost nothing lost in translation.

## See it run

```bash
.venv/bin/python stage1_demo.py --from e2 --to e4
```

Watch the printout and follow along with your checklist. You'll see it hover,
open, lower, close, lift, travel, and set the piece down. **You just built the
foundation of a chess robot.**

---
Back: [Home](Home.md) · Next: [Steps 2 & 3 — play a game →](06-step-2-and-3-play-a-game.md)
