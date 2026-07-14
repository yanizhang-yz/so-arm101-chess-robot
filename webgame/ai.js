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

  const KidAI = { evaluate, search, best, chooseMove, VAL };
  if (typeof module !== "undefined" && module.exports) module.exports = KidAI;
  else root.KidAI = KidAI;
})(typeof window !== "undefined" ? window : globalThis);
