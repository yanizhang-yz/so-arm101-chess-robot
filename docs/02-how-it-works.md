# 2. How it works, in plain English

Let's break the robot into parts. Don't worry — you don't build them all at once.

## The four parts

Think of the robot like a little person playing chess:

- 🧠 **The Brain** — decides what move to play. We don't write this ourselves!
  A free program called **Stockfish** already plays chess better than any human
  on Earth. We just borrow it and politely ask it to play *gently* for a child.
- 🦾 **The Body** — the robot arm that physically picks up and moves pieces.
  This is the slow, finicky part, so we save it for last.
- 👀 **The Eyes** — a camera, so the robot can *see* which move your child made
  (added much later; until then, you just type her move in).
- 💬 **The Voice** — so it can talk, explain, and encourage (the coaching part,
  added at the very end).

## The secret that makes it all possible

Here's the trick we keep using, over and over:

> **Fake the hard part first. Make it real last.**

Instead of the real arm, we start with a **pretend arm**. The pretend arm doesn't
move anything — it just *prints a description* of what it would do:

```
   arm: go above e2
   arm: open the gripper
   arm: lower down
   arm: close (grab the piece)
   arm: lift up
   arm: go above e4
   arm: lower down
   arm: open (let go)
   arm: lift up
```

This sounds silly, but it's powerful. With the pretend arm, you can build and
*test the entire chess game on your laptop* — no robot, no wires, no waiting.
When the real arm finally arrives, it only has to do the same simple things the
pretend arm was doing (*go here, open, close*), so nothing else has to change.

Programmers have a name for a "pretend" stand-in like this: a **mock**. Now you
know a real bit of vocabulary. 😊

## Why we do it in this order

Building the brain and the pretend body first means:

- You're **never stuck** waiting on hardware.
- You get a **playable game early**, which keeps you motivated.
- When you add the real arm, the camera, or the voice, you add **one new thing at
  a time** — never a big scary pile of new things at once.

That rhythm — *one small piece, always runnable, fake the slow parts, connect
reality last* — is the whole method. Every stage in this guide follows it.

---
Back: [Home](Home.md) · Next: [What you need →](03-what-you-need.md)
