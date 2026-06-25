# 8. What's next — eyes and a voice

By now you have a real robot arm playing chess with your child. The last two
additions are what make it feel like a *coach*. Both use the exact same trick you
already know: **fake it first, make it real later.**

## Eyes — so it sees her move

Right now, when your child moves, *you* type her move in. The camera removes that
chore: a webcam looks down at the board, and after she moves, the computer
notices **which squares changed** and figures out what she played.

Here's the lovely shortcut: the computer already knows the full position, so the
camera doesn't need to recognize *what* each piece is — only *which squares became
empty or filled*. That's a much simpler problem than it sounds.

And you guessed it — you build it the safe way: first a **pretend camera** that
just hands back a move you typed, so all the game wiring works; then swap in the
real webcam. Same pattern as the arm.

## A voice — so it talks and coaches

This is the part you dreamed of: the robot encouraging your child, explaining
ideas, answering "what if I move here?" — like the Duolingo chess coach.

It comes together from three friendly pieces:

- **Ears:** turn her spoken words into text (so she can just *talk*).
- **A coach:** send the board position and her question to **Claude**, and have it
  reply warmly, at a five-year-old's level.
- **A mouth:** turn Claude's reply into a spoken voice.

One important rule we follow: **let Stockfish do the chess thinking, and let
Claude do the talking.** Chess engines are perfect at calculating; the AI coach is
wonderful at explaining and encouraging. Each does what it's best at, and together
they feel like a patient human teacher.

## The rhythm never changes

Notice that every single stage — the arm, the eyes, the voice — followed the same
gentle rhythm:

> one small piece at a time · always keep it runnable · fake the hard part first ·
> connect reality last

That's not just how you built a chess robot. That's how thoughtful people build
*any* big, intimidating thing: by making it small, safe, and never-stuck. You
didn't just build a toy — you learned how to build. 💛

---
Back: [Home](Home.md) · Next: [Glossary & help →](09-glossary-and-help.md)
