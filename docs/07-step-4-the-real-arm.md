# 7. Step 4 — connecting the real arm

This is the moment the robot becomes real. It's also the **fiddliest** part of the
whole project, so take it slowly and don't expect it to be perfect on the first
try. That's normal.

> 🛠️ **Want just the commands, in order?** See the
> [Hardware Setup Checklist](hardware-setup-checklist.md) — but read the safety
> section right below first.

## Safety first

Please read this before the arm ever moves on its own. The arm is small, but it
has real motors and it moves near a child.

- **Turn-based only.** The robot moves *only* on its own turn, and your child
  keeps her hands clear while it does. Never both reaching at once.
- **Go slow.** Keep the arm's movements gentle and slow, especially while you're
  still learning its quirks.
- **Have an off-switch within reach.** Know how to cut its power instantly — a
  power strip with a switch is perfect.
- **Mount it on the robot's side.** Position the arm so it can't reach across into
  your child's space.
- **A grown-up always watches.** Every single time.

The 12V version of the arm has real strength — respect it, and you'll be fine.

## Why the rest of your project doesn't change

Remember the pretend arm? It only ever did three things: *go to a spot, open,
close.* The real arm does those same three things. So **none of your game code
changes** — you just swap the pretend arm for the real one. That's the payoff of
building it the way we did.

## The new work (only the hardware bits)

You'll do these once, when you're ready. Full commands are in the project's main
[README](../README.md#going-to-hardware-so-arm101-pro-12v); here's the plain-English map:

1. **Install the robot toolkit.** A one-time install of *LeRobot* (the software
   that talks to the arm). It's bigger than the earlier installs, so it takes a
   few minutes.
2. **Find the arm's "address."** When you plug the arm into USB, the computer
   gives it a name (a *port*). A little command (`find_port`) tells you what it
   is, and you write it into a settings file.
3. **Calibrate the arm.** A guided routine where you move the arm to a few
   positions so it learns its own joints. Follow the on-screen prompts.
4. **Tell it where the board is.** You gently move the gripper to a few squares
   (the corners) and the computer records where they are. From that, it works out
   how to reach *every* square. (This is `scripts/calibrate_board.py`.)
5. **Tune the grip.** Adjust how wide the gripper opens and how firmly it closes,
   so it holds a piece without crushing or dropping it.

Then you run the *same* game as before, with one extra word — `--hardware`:

```bash
.venv/bin/python play.py --hardware
```

…and the real arm plays its moves.

## When it's wobbly (it will be, at first)

Cheap hobby motors aren't perfectly precise, so expect some trial and error:

- Make the squares a bit bigger and the pieces easy to grab.
- A board with a little felt or slight dishing helps pieces settle into place.
- If a grab misses, just nudge your calibration numbers and try again.

Patience here pays off. Once it's dialed in, watching the arm make its first real
move is genuinely magical. 🪄

---
Back: [Home](Home.md) · Next: [What's next →](08-whats-next.md)
