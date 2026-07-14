/* The four friendly opponents. Pure logic, no DOM — index.html uses it in the
 * browser, and `node ai.test.js` exercises it headlessly.
 *
 * Levels: 1 Chick  = random legal move
 *         2 Bunny  = grabs the biggest capture it can see, else random
 *         3 Fox    = looks 2 moves ahead (alpha-beta, material + center)
 *         4 Owl    = looks 3 moves ahead
 * A little random jitter keeps games varied so kids don't see the same reply
 * every time.
 */
(function (root) {
  "use strict";

  const VAL = { p: 100, n: 300, b: 310, r: 500, q: 900, k: 0 };
  const CENTER = { d4: 12, e4: 12, d5: 12, e5: 12, c3: 6, f3: 6, c6: 6, f6: 6,
                   c4: 6, f4: 6, c5: 6, f5: 6 };
  const FILES = "abcdefgh";

  function randomOf(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

  function evaluate(game) {           // + is good for White
    let s = 0;
    game.board().forEach((row, y) => row.forEach((p, x) => {
      if (!p) return;
      const sq = FILES[x] + (8 - y);
      const v = VAL[p.type] + (p.type !== "k" && CENTER[sq] ? CENTER[sq] : 0);
      s += p.color === "w" ? v : -v;
    }));
    return s;
  }

  function search(game, depth, alpha, beta) {
    if (game.in_checkmate()) return game.turn() === "w" ? -99999 - depth : 99999 + depth;
    if (game.in_draw() || game.in_stalemate()) return 0;
    if (depth === 0) return evaluate(game);
    const moves = game.moves({ verbose: true });
    if (game.turn() === "w") {
      let bestScore = -Infinity;
      for (const m of moves) {
        game.move(m);
        bestScore = Math.max(bestScore, search(game, depth - 1, alpha, beta));
        game.undo();
        alpha = Math.max(alpha, bestScore);
        if (beta <= alpha) break;
      }
      return bestScore;
    }
    let bestScore = Infinity;
    for (const m of moves) {
      game.move(m);
      bestScore = Math.min(bestScore, search(game, depth - 1, alpha, beta));
      game.undo();
      beta = Math.min(beta, bestScore);
      if (beta <= alpha) break;
    }
    return bestScore;
  }

  function best(game, depth, jitter) {
    const j = jitter === undefined ? 14 : jitter;
    const moves = game.moves({ verbose: true });
    if (!moves.length) return null;
    const mine = game.turn();
    const scored = moves.map((m) => {
      game.move(m);
      const s = search(game, depth - 1, -Infinity, Infinity) + Math.random() * j;
      game.undo();
      return { m, s };
    });
    scored.sort((a, b) => (mine === "w" ? b.s - a.s : a.s - b.s));
    return scored[0].m;
  }

  function chooseMove(game, level) {
    const moves = game.moves({ verbose: true });
    if (!moves.length) return null;
    if (level === 1) return randomOf(moves);
    if (level === 2) {
      let bestMoves = [], bestVal = 0;
      for (const m of moves) {
        const v = m.captured ? VAL[m.captured] : 0;
        if (v > bestVal) { bestVal = v; bestMoves = [m]; }
        else if (v === bestVal) bestMoves.push(m);
      }
      return randomOf(bestMoves);
    }
    return best(game, level === 3 ? 2 : 3);
  }

  /* ---------- kid-words layer: describe moves, coach a finished game ------- */

  const KIDNAME = { p: "little pawn", n: "horsey", b: "bishop", r: "castle",
                    q: "queen", k: "king" };

  /* A short, speakable sentence about a verbose move (for the hint button). */
  function describe(m) {
    if (!m) return "Hmm, I don't see a move!";
    if (m.san.startsWith("O-O")) return "Try castling — your king hides behind his castle wall!";
    let s = `Try your ${KIDNAME[m.piece]}`;
    if (m.captured) s += ` — it can catch their ${KIDNAME[m.captured]}!`;
    else if (m.san.includes("#")) s += " — it wins the whole game!";
    else if (m.san.includes("+")) s += " — it attacks their king!";
    else s += ` — ${m.to} is a strong spot for it.`;
    return s;
  }

  /* After the game: 3-5 short, kid-level lines about how it went.
     The kid is always White. Uses material swings over each of the kid's
     rounds (their move + the reply) to find the best moment and the oops. */
  function coach(game) {
    const hist = game.history({ verbose: true });
    const lines = [];
    if (hist.length < 2) return ["That was quick! Let's play a longer one! 🐣"];

    // material eval after every ply: rewind this game to the start, then
    // replay it (chess.js objects are factory-made, so there's no constructor
    // to build a fresh one from) — the game ends back in the same state.
    for (let i = 0; i < hist.length; i++) game.undo();
    const evals = [0];
    for (const m of hist) { game.move(m); evals.push(evaluate(game)); }

    let best = null, worst = null, catches = 0, castled = false, promoted = false;
    for (let i = 0; i < hist.length; i += 2) {         // the kid's plies
      const m = hist[i];
      if (m.captured) catches++;
      if (m.san.startsWith("O-O")) castled = true;
      if (m.flags.includes("p")) promoted = true;
      const after = evals[Math.min(i + 2, evals.length - 1)];
      const swing = after - evals[i];
      const round = Math.floor(i / 2) + 1;
      const lost = hist[i + 1] && hist[i + 1].captured ? hist[i + 1].captured : null;
      if (!best || swing > best.swing) best = { m, swing, round };
      if (!worst || swing < worst.swing) worst = { m, swing, round, lost };
    }

    if (catches > 0) lines.push(`You caught ${catches} of my pieces! 🧺`);
    if (castled) lines.push("You castled — that keeps your king super safe! 🏰👑");
    if (promoted) lines.push("Your little pawn walked ALL the way and became a queen! 👑✨");
    if (best && best.swing >= 200) {
      const what = best.m.captured ? `caught my ${KIDNAME[best.m.captured]}` : "found a super spot";
      lines.push(`Your best move: round ${best.round}, when your ${KIDNAME[best.m.piece]} ${what}! 🌟`);
    }
    if (worst && worst.swing <= -250 && worst.lost) {
      lines.push(`One thing to watch: in round ${worst.round} I caught your ${KIDNAME[worst.lost]}. ` +
                 "Before you move, ask: is my piece safe there? 🔍");
    } else {
      lines.push("You kept your pieces safe — that's what champions do! 🛡️");
    }
    lines.push("Every game makes you stronger. Let's play again! 💪");
    return lines;
  }

  const KidAI = { evaluate, search, best, chooseMove, describe, coach, KIDNAME, VAL };
  if (typeof module !== "undefined" && module.exports) module.exports = KidAI;
  else root.KidAI = KidAI;
})(typeof window !== "undefined" ? window : globalThis);
