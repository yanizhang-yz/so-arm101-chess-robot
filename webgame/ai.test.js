/* Headless checks for the kid AI:  node ai.test.js  */
"use strict";
const { Chess } = require("./chess.js");
const AI = require("./ai.js");

let failures = 0;
function check(name, cond) {
  console.log((cond ? "  ok  " : "  FAIL") + " - " + name);
  if (!cond) failures++;
}

// 1. Every level produces a legal move from the start position.
for (const level of [1, 2, 3, 4]) {
  const g = new Chess();
  const mv = AI.chooseMove(g, level);
  check(`level ${level} plays a legal opening move`, mv && g.move(mv) !== null);
}

// 2. Full games at each level never produce an illegal move and terminate.
for (const level of [1, 2, 3, 4]) {
  const g = new Chess();
  let plies = 0, ok = true;
  while (!g.game_over() && plies < 300) {
    const mv = AI.chooseMove(g, g.turn() === "w" ? 1 : level); // random vs level
    if (!mv || g.move(mv) === null) { ok = false; break; }
    plies++;
  }
  check(`level ${level} survives a full game (${plies} plies)`, ok);
}

// 3. The Fox (depth 2) takes an undefended queen.
{
  // Black queen hanging on d5; white queen on d2 sees it straight up the file.
  const g = new Chess("rnb1kbnr/ppp1pppp/8/3q4/8/8/PPPQPPPP/RNB1KBNR w KQkq - 0 1");
  const mv = AI.best(g, 2, 0);
  check("depth-2 grabs a hanging queen", mv && mv.to === "d5" && mv.captured === "q");
}

// 4. The Owl finds mate in one (Scholar's mate).
{
  const g = new Chess("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4");
  const mv = AI.best(g, 3, 0);
  g.move(mv);
  check("depth-3 finds mate in one", g.in_checkmate());
}

// 5. The Bunny prefers the biggest capture on the board.
{
  // Both a pawn (xb5? no) — white knight on d4 can take queen on e6 or pawn on c6.
  const g = new Chess("4k3/8/2p1q3/8/3N4/8/8/4K3 w - - 0 1");
  let tookQueen = 0;
  for (let i = 0; i < 20; i++) {
    const mv = AI.chooseMove(new Chess(g.fen()), 2);
    if (mv.captured === "q") tookQueen++;
  }
  check("greedy bunny always takes the queen over the pawn", tookQueen === 20);
}

// 6. Depth-3 stays fast enough for a snappy game (< 3s worst-ish case midgame).
{
  const g = new Chess("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3");
  const t0 = Date.now();
  AI.best(g, 3, 0);
  const ms = Date.now() - t0;
  check(`depth-3 midgame move under 3s (took ${ms} ms)`, ms < 3000);
}

console.log(failures ? `\n${failures} FAILURES` : "\nall good");
process.exit(failures ? 1 : 0);
