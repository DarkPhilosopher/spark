// The 3D view's own chat -- checks the two pieces with real logic worth
// getting right computationally, since there's no server here to talk to
// for real: showNewChat()'s dedup (only new lines, never your own name
// twice) and runChatSaid()'s command dispatch (matching index.html's own
// /word parsing exactly, since this deliberately mirrors it).

const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "world3d.html"), "utf8");

const s = html.indexOf("let seenChat = 0;");
if (s < 0) throw new Error("marker not found: let seenChat = 0;");
const e = html.indexOf("\n\nfunction setupChat", s);
if (e < 0) throw new Error("end marker not found: function setupChat");
const src = html.slice(s, e);

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
};

// A minimal #chat-log: real enough for chatLine()'s own appendChild/
// scrollTop/removeChild (used by /forget), and easy to read back from.
class FakeLog {
  constructor() { this.children = []; this.scrollTop = 0; this.scrollHeight = 0; this._text = ""; }
  appendChild(c) { this.children.push(c); return c; }
  removeChild(c) { this.children = this.children.filter(x => x !== c); return c; }
  set textContent(v) { this.children = []; this._text = v; }
  get textContent() { return this._text; }
  get firstChild() { return this.children[0]; }
}
class FakeEl {
  constructor() { this.className = ""; this._text = ""; this.children = []; }
  appendChild(c) { this.children.push(c); return c; }
  // No .remove() here on purpose -- real page elements have one, this
  // fake doesn't, so /forget's own `target.remove ? ... : log.removeChild(...)`
  // exercises the removeChild fallback path in tests, which is exactly
  // what a plain object without DOM's own .remove() needs anyway.
  set textContent(v) { this._text = v; this.children = []; }
  get textContent() {
    return this._text || this.children.map(c => c.text || c.textContent || "").join("");
  }
}

// A real (if tiny) classList, backed by a Set -- unlike a plain object
// with add()/remove() no-ops, .contains() actually reflects what was
// last added/removed, and the SAME object comes back every time $ is
// asked for "#chat-modal" (a fresh literal each call couldn't remember
// anything between one $() and the next). That's enough to check
// openChat's real effect, not just that it doesn't throw.
class FakeModal {
  constructor() {
    const on = new Set();
    this.classList = {
      add: c => on.add(c), remove: c => on.delete(c), contains: c => on.has(c),
    };
  }
}

function load({failFetch = false} = {}) {
  const log = new FakeLog();
  const modal = new FakeModal();
  const $ = sel => (sel === "#chat-log" ? log
                   : sel === "#chat-modal" ? modal
                   : {value: "", focus() {}, classList: {add() {}, remove() {}}});
  const documentStub = {
    createElement: () => new FakeEl(),
    createTextNode: t => ({text: String(t)}),
  };
  const fetchCalls = [];
  // failFetch simulates a bad connection -- resolved, but !ok, same as the
  // real fetch call's own .catch(() => null) never even needs to fire for
  // an ordinary server-side rejection (only an actual network failure does).
  const fakeFetch = (url, opts) => {
    fetchCalls.push({url, opts});
    return Promise.resolve({ok: !failFetch});
  };
  const mod = {exports: {}};
  const body = src + `
    module.exports = {
      chatLine, showNewChat, runChatSaid, sendChatText, CHAT_COMMANDS,
      openChat,
      getSeenChat: () => seenChat, setSeenChat: v => { seenChat = v; },
      setLive: (v, snap) => { live = v; liveSnapshot = snap; },
      setProject: p => { project = p; },
      setWorld: w => { world = w; },
    };
  `;
  new Function("module", "$", "document", "authHeaders", "fetch", "live", "liveSnapshot", "project", "world", body)(
    mod, $, documentStub, () => ({}), fakeFetch, false, null, null, null);
  return {api: mod.exports, log, modal, fetchCalls};
}

// log.children are now page-wrapper elements (one per CHAT_PAGE_SIZE
// lines, each starting with its own "-- page N --" header line) rather
// than individual lines directly -- flatten both levels back into one
// list of rendered strings, in order, headers included (they're plain
// lines structurally, same as any other system message).
const readLine = el => {
  const who = el.children[0] && el.children[0].textContent;
  const rest = el.children.slice(1).map(c => c.text || "").join("");
  return who ? (who + rest) : el.textContent;
};
const rendered = log => {
  const out = [];
  for (const page of log.children) {
    for (const line of page.children) out.push(readLine(line));
  }
  return out;
};

console.log("showNewChat: only new lines, never your own name twice");
{
  const {api, log} = load();
  api.setLive(true, {you: {name: "gabe"}, chat: [
    {n: 1, who: "gabe", text: "hi from me"},
    {n: 2, who: "ada", text: "hi back"},
  ]});
  // "1" real line plus the page header chatLine() always stamps in
  // front of the first line of a fresh page -- every count/index below
  // is +1 for that header, throughout this whole file.
  api.showNewChat();
  ok("my own line (already shown when sent) is skipped", rendered(log).length === 2, rendered(log));
  ok("someone else's line shows", rendered(log)[1].includes("hi back"), rendered(log));
  ok("seenChat advances to the highest n seen", api.getSeenChat() === 2);

  api.showNewChat();   // same snapshot again -- nothing new
  ok("polling the same snapshot again adds nothing", rendered(log).length === 2, rendered(log));

  api.setLive(true, {you: {name: "gabe"}, chat: [
    {n: 1, who: "gabe", text: "hi from me"},
    {n: 2, who: "ada", text: "hi back"},
    {n: 3, who: "ada", text: "you there?"},
  ]});
  api.showNewChat();
  ok("only the genuinely new line (n=3) gets added, not n=1/2 again",
     rendered(log).length === 3 && rendered(log)[2].includes("you there"), rendered(log));
}

console.log("\nshowNewChat: does nothing at all outside LIVE mode");
{
  const {api, log} = load();
  api.setLive(false, null);
  api.showNewChat();
  ok("no crash, and nothing rendered, with no live snapshot", log.children.length === 0);
}

console.log("\nrunChatSaid: commands dispatch, plain text is chat, unknown commands say so");
{
  const {api, log, fetchCalls} = load();
  api.setLive(true, {you: {name: "gabe"}, people: [{name: "ada", role: "guest"}], chat: []});

  api.runChatSaid("/who");
  ok("/who lists people from the snapshot", rendered(log).some(l => l.includes("ada")), rendered(log));

  api.runChatSaid("/nonsense");
  ok("an unknown command says so, doesn't crash or silently do nothing",
     rendered(log).some(l => l.includes("no such command")), rendered(log));

  api.runChatSaid("/clear");
  ok("/clear empties the log", log.children.length === 0);

  return api.runChatSaid("hello everyone").then(() => {
    ok("plain text (no leading /) is sent as chat, not treated as a command",
       fetchCalls.length === 1 && fetchCalls[0].url === "api/chat", fetchCalls);

    runSavedOfflineTests();
  });
}

function runSavedOfflineTests() {
  // A top-level console.log right before a function declaration like this
  // one never actually prints -- the earlier top-level `return` (inside
  // the .then() this function is eventually called from) truncates the
  // rest of the module's synchronous execution, skipping every bare
  // statement after it while still hoisting the function declarations
  // themselves. Harmless (every check below still runs and counts;
  // "passed"/"failed" stay accurate), but the header needs to be the
  // first line INSIDE the function to actually appear in the output.
  console.log("\nsendChatText: nothing typed is ever silently lost, live or not");
  {
    const {api, log} = load();
    api.setLive(false, null);
    api.runChatSaid("saved even offline");
    ok("a plain message with no server still lands in the log, not just an error",
       rendered(log).some(l => l.includes("saved even offline")), rendered(log));
    ok("...with a note that it wasn't actually sent anywhere",
       rendered(log).some(l => l.includes("not sent")), rendered(log));
  }
  {
    const {api, log} = load({failFetch: true});
    api.setLive(true, {you: {name: "gabe"}, chat: []});
    return api.runChatSaid("does this survive a bad connection").then(() => {
      ok("even a failed send still keeps the message in the log",
         rendered(log).some(l => l.includes("does this survive a bad connection")), rendered(log));
      ok("...and says it could not actually be delivered",
         rendered(log).some(l => l.includes("could not send")), rendered(log));
      runHelpTests();
    });
  }
}

function runHelpTests() {
  console.log("\n/help: shows the loaded game's own instructions, when it has any");
  {
    const {api, log} = load();
    api.setProject({name: "outpost", help: "line one\nline two"});
    api.runChatSaid("/help");
    ok("both lines of the game's own help text show up",
       rendered(log).some(l => l.includes("line one")) &&
       rendered(log).some(l => l.includes("line two")), rendered(log));
    ok("the chat-command legend still shows too, after it",
       rendered(log).some(l => l.includes("/who")), rendered(log));
  }
  {
    const {api, log} = load();
    api.setProject({name: "chase"});   // no help field at all
    api.runChatSaid("/help");
    ok("a game with no help field just skips straight to the command legend",
       rendered(log)[1] === "Info:" && rendered(log).some(l => l.includes("/who")), rendered(log));
  }

  console.log("\n/help commands [description]: the reference on its own, grouped by type");
  {
    const {api, log} = load();
    api.setProject({name: "outpost", help: "some game text"});
    api.runChatSaid("/help commands");
    const out = rendered(log);
    ok("just the reference -- no game text, even though there is one to skip",
       out[1] === "Info:" && !out.some(l => l.includes("some game text")), out);
    ok("bare syntax only, no descriptions", !out.some(l => l.includes(" — ")), out);
    ok("grouped under headings, in a fixed order",
       out.indexOf("Actions:") > out.indexOf("Info:") &&
       out.indexOf("Log:") > out.indexOf("Actions:"), out);
  }
  {
    const {api, log} = load();
    api.runChatSaid("/help commands description");
    const out = rendered(log);
    ok("same reference, with what each one does this time",
       out[1] === "Info:" && out.some(l => l.includes(" — ")), out);
  }

  runMineTests();
}

function runMineTests() {
  console.log("\n/mine <x> <y>: gather from a known spot instead of walking up to it blind");
  const hero = () => ({kind: "hero", role: "player", alive: true, x: 5, y: 5, inventory: {}});
  const ore = (x, y) => ({kind: "ore", role: "prop", alive: true, x, y, inventory: {}});

  {
    const {api, log} = load();
    api.runChatSaid("/mine 5 5");
    ok("with no world running, says so rather than crashing",
       rendered(log)[1].includes("no game running"), rendered(log));
  }
  {
    const {api, log} = load();
    const h = hero();
    api.setWorld({things: [h, ore(6, 5)]});
    api.runChatSaid("/mine 6 5");
    ok("mining an adjacent, real ore spot works",
       rendered(log)[1].includes("mined 1 ore"), rendered(log));
    ok("...and it actually lands in the hero's own count", h.inventory.ore === 1);
  }
  {
    const {api, log} = load();
    api.setWorld({things: [{...hero(), x: 0, y: 0}, ore(6, 5)]});
    api.runChatSaid("/mine 6 5");
    ok("too far away refuses, doesn't teleport-mine across the map",
       rendered(log)[1].includes("too far"), rendered(log));
  }
  {
    const {api, log} = load();
    api.setWorld({things: [hero(), ore(6, 5)]});
    api.runChatSaid("/mine 5 6");   // adjacent, but nothing there
    ok("adjacent but nothing there says so", rendered(log)[1].includes("no ore at"), rendered(log));
  }
  {
    const {api, log} = load();
    api.setWorld({things: [hero()]});
    api.runChatSaid("/mine");
    ok("missing coordinates gives a usage line, not a crash",
       rendered(log)[1].includes("try: /mine"), rendered(log));
    api.runChatSaid("/mine x y");
    ok("non-numeric coordinates say so, not a crash",
       rendered(log)[2].includes("plain numbers"), rendered(log));
  }

  runAttackTests();
}

function runAttackTests() {
  console.log("\n/attack <x> <y>: hit a bandit at a known spot instead of walking up to it blind");
  const hero = (x, y) => ({kind: "hero", role: "player", alive: true, x, y, inventory: {}});
  const bandit = (x, y, health) => ({kind: "bandit", role: "prop", alive: true, x, y, health: health || 6});

  {
    const {api, log} = load();
    api.runChatSaid("/attack 5 5");
    ok("with no world running, says so rather than crashing",
       rendered(log)[1].includes("no game running"), rendered(log));
  }
  {
    const {api, log} = load();
    const b = bandit(6, 5);
    api.setWorld({things: [hero(5, 5), b]});
    api.runChatSaid("/attack 6 5");
    ok("attacking an adjacent bandit does 2 damage, the same touch already does",
       rendered(log)[1].includes("attacked") && b.health === 4, [rendered(log), b.health]);
    ok("it's still alive with health left", b.alive);
  }
  {
    const {api, log} = load();
    const b = bandit(6, 5, 2);
    api.setWorld({things: [hero(5, 5), b], remove(t) { t.alive = false; }});
    api.runChatSaid("/attack 6 5");
    ok("killing it outright removes it, same as ordinary contact damage",
       rendered(log)[1].includes("destroyed") && !b.alive, [rendered(log), b.alive]);
  }
  {
    const {api, log} = load();
    api.setWorld({things: [hero(0, 0), bandit(6, 5)]});
    api.runChatSaid("/attack 6 5");
    ok("too far away refuses", rendered(log)[1].includes("too far"), rendered(log));
  }
  {
    const {api, log} = load();
    api.setWorld({things: [hero(5, 5), bandit(6, 5)]});
    api.runChatSaid("/attack 5 6");   // adjacent, nothing there
    ok("adjacent but nothing there says so", rendered(log)[1].includes("no bandit at"), rendered(log));
  }

  runSquadTests();
}

function runSquadTests() {
  console.log("\n/recruit <x> <y> and /dismiss <x> <y>: the same as e/r, aimed at a spot");
  const hero = (x, y) => ({kind: "hero", role: "player", alive: true, x, y, inventory: {}});
  const worker = (x, y, leader) => ({kind: "worker", role: "prop", alive: true, x, y, leader: leader || null});
  const bandit = (x, y) => ({kind: "bandit", role: "prop", alive: true, x, y, health: 6});

  {
    const {api, log} = load();
    api.runChatSaid("/recruit 5 5");
    ok("with no world running, says so rather than crashing",
       rendered(log)[1].includes("no game running"), rendered(log));
  }
  {
    const {api, log} = load();
    const h = hero(5, 5), w = worker(6, 5);
    api.setWorld({things: [h, w]});
    api.runChatSaid("/recruit 6 5");
    ok("recruiting a bare worker (not just a companion) works",
       rendered(log)[1].includes("recruited the worker") && w.leader === h, [rendered(log), w.leader]);
  }
  {
    const {api, log} = load();
    api.setWorld({things: [hero(5, 5), worker(6, 5, "someone else already")]});
    api.runChatSaid("/recruit 6 5");
    ok("can't recruit something already led by someone",
       rendered(log)[1].includes("nothing recruitable"), rendered(log));
  }
  {
    const {api, log} = load();
    api.setWorld({things: [hero(0, 0), worker(6, 5)]});
    api.runChatSaid("/recruit 6 5");
    ok("too far away refuses", rendered(log)[1].includes("too far"), rendered(log));
  }
  {
    const {api, log} = load();
    api.setWorld({things: [hero(5, 5), bandit(6, 5)]});
    api.runChatSaid("/recruit 6 5");
    ok("a bandit is never recruitable, even bare and adjacent",
       rendered(log)[1].includes("nothing recruitable"), rendered(log));
  }
  {
    const {api, log} = load();
    const h = hero(5, 5), w = worker(6, 5, h);   // already led by the hero itself
    api.setWorld({things: [h, w]});
    api.runChatSaid("/dismiss 6 5");
    ok("dismissing a bought worker works, not just a companion",
       rendered(log)[1].includes("dismissed the worker") && w.leader === null, [rendered(log), w.leader]);
  }
  {
    const {api, log} = load();
    api.setWorld({things: [hero(5, 5), worker(6, 5)]});   // bare, not led by hero
    api.runChatSaid("/dismiss 6 5");
    ok("can't dismiss something that isn't yours",
       rendered(log)[1].includes("nothing of yours"), rendered(log));
  }
  {
    const {api, log} = load();
    const h = hero(0, 0);
    api.setWorld({things: [h, worker(6, 5, h)]});
    api.runChatSaid("/dismiss 6 5");
    ok("too far away refuses", rendered(log)[1].includes("too far"), rendered(log));
  }

  runRosterTests();
}

function runRosterTests() {
  console.log("\n/units and /name: the roster -- everything yours, named and located");
  const thing = (kind, x, y, extra) =>
    Object.assign({kind, x, y, role: "prop", alive: true, leader: null, label: null, inventory: {}}, extra || {});
  const rosterWorld = () => {
    const hero = thing("hero", 1, 1, {role: "player"});
    const companion = thing("companion", 2, 2, {leader: hero});
    const stray = thing("companion", 3, 3);   // not led -- shouldn't show up
    const enemy = thing("bandit", 4, 4);
    const wall = thing("wall", 5, 5);
    const turret = thing("turret", 6, 6);
    return {things: [hero, companion, stray, enemy, wall, turret], hero, companion, stray, turret};
  };

  {
    const {api, log} = load();
    const w = rosterWorld();
    api.setWorld(w);
    api.runChatSaid("/units");
    const out = rendered(log);
    ok("lists the hero", out.some(l => l.includes("hero") && l.includes("(1, 1)")), out);
    ok("lists a recruited companion", out.some(l => l.includes("(2, 2)")), out);
    ok("does NOT list an unled companion", !out.some(l => l.includes("(3, 3)")), out);
    ok("does NOT list a bandit", !out.some(l => l.includes("bandit")), out);
    ok("lists a wall (structures are ours by kind, no leader needed)",
       out.some(l => l.includes("(5, 5)")), out);
    ok("lists a turret the same way", out.some(l => l.includes("(6, 6)")), out);
  }
  {
    const {api, log} = load();
    api.runChatSaid("/units");
    ok("with no world running, says so rather than crashing",
       rendered(log)[1].includes("no game running"), rendered(log));
  }
  {
    const {api, log} = load();
    const w = rosterWorld();
    api.setWorld(w);
    api.runChatSaid("/name 6 6 North Gate");
    ok("naming something of yours works", rendered(log)[1].includes("North Gate"), rendered(log));
    ok("...and the name actually sticks on the Thing", w.turret.label === "North Gate");
    api.runChatSaid("/units");
    ok("the custom name shows up in /units from then on",
       rendered(log).some(l => l.includes("North Gate")), rendered(log));

    api.runChatSaid("/name 3 3 Sneaky");   // the unled stray
    ok("can't name something that isn't yours",
       rendered(log)[rendered(log).length - 1].includes("nothing of yours"), rendered(log));

    api.runChatSaid("/name 6 6");
    ok("missing a name gives a usage line, not a crash",
       rendered(log)[rendered(log).length - 1].includes("try: /name"), rendered(log));
    api.runChatSaid("/name x y Bob");
    ok("non-numeric coordinates say so, not a crash",
       rendered(log)[rendered(log).length - 1].includes("plain numbers"), rendered(log));
  }

  runListTests();
}

function runListTests() {
  console.log("\n/list: every entity in the world, yours or not, with its properties");
  const thing = (kind, x, y, extra) =>
    Object.assign({kind, x, y, role: "prop", alive: true, leader: null, label: null,
                    health: 6, inventory: {}}, extra || {});
  {
    const {api, log} = load();
    api.runChatSaid("/list");
    ok("with no world running, says so rather than crashing",
       rendered(log)[1].includes("no game running"), rendered(log));
  }
  {
    const {api, log} = load();
    const h = thing("hero", 1, 1, {role: "player", health: 10});
    const stray = thing("companion", 3, 3);         // unled -- /units wouldn't show this
    const led = thing("worker", 2, 2, {leader: h, inventory: {ore: 3}});
    const bandit = thing("bandit", 9, 9, {health: 4});
    api.setWorld({things: [h, stray, led, bandit]});
    api.runChatSaid("/list");
    const out = rendered(log);
    ok("lists the hero", out.some(l => l.includes("hero") && l.includes("(1, 1)")), out);
    ok("lists an unled bystander too, unlike /units", out.some(l => l.includes("(3, 3)")), out);
    ok("lists a bandit too", out.some(l => l.includes("bandit") && l.includes("(9, 9)")), out);
    ok("shows health", out.some(l => l.includes("health 10")), out);
    ok("shows who's leading a led thing", out.some(l => l.includes("led by hero")), out);
    ok("shows a non-empty inventory", out.some(l => l.includes("carrying 3 ore")), out);
    ok("a plain thing with nothing extra shows neither 'led by' nor 'carrying'",
       out.find(l => l.includes("(9, 9)")) &&
       !out.find(l => l.includes("(9, 9)")).includes("led by") &&
       !out.find(l => l.includes("(9, 9)")).includes("carrying"), out);
  }
  {
    const {api, log} = load();
    api.setWorld({things: [{kind: "wall", x: 0, y: 0, role: "prop", alive: false,
                             leader: null, label: null, health: 5, inventory: {}}]});
    api.runChatSaid("/list");
    ok("a dead thing doesn't show up at all",
       rendered(log)[1].includes("nothing in the world at all"), rendered(log));
  }
  {
    const {api, log} = load();
    const h = thing("hero", 1, 1, {role: "player"});
    const named = thing("turret", 5, 5, {label: "North Gate"});
    api.setWorld({things: [h, named]});
    api.runChatSaid("/list");
    ok("a custom /name shows up here too, alongside its own kind",
       rendered(log).some(l => l.includes("North Gate (turret)")), rendered(log));
  }

  runPageTests();
}

function runPageTests() {
  console.log("\nchatLine: consistent, paginated history -- no more silent 200-line trim");
  {
    const {api, log} = load();
    for (let i = 0; i < 25; i++) api.chatLine("", "line " + i);
    ok("nothing is ever silently dropped -- all 25 lines plus 3 page headers survive",
       rendered(log).length === 28, rendered(log).length);
    ok("a new page starts automatically every 10 lines -- 3 pages for 25 lines",
       log.children.length === 3, log.children.length);
    ok("each page is titled by its own number",
       rendered(log)[0] === "-- page 1 --" && rendered(log)[11] === "-- page 2 --", rendered(log));
  }

  console.log("\n/log [n]: jump to a numbered page instead of replacing the view");
  {
    const {api, log} = load();
    api.runChatSaid("/log");
    ok("nothing logged yet, says so", rendered(log)[1].includes("nothing logged yet"), rendered(log));
  }
  {
    const {api, log} = load();
    for (let i = 0; i < 25; i++) api.chatLine("", "line " + i);
    const before = rendered(log).length;
    api.runChatSaid("/log 2");
    ok("a valid page number scrolls silently -- no new line added",
       rendered(log).length === before, rendered(log));
    api.runChatSaid("/log 99");
    ok("an out-of-range page says so", rendered(log)[rendered(log).length - 1].includes("no page 99"), rendered(log));
    api.runChatSaid("/log x");
    ok("a non-numeric page says so, not a crash",
       rendered(log)[rendered(log).length - 1].includes("plain number"), rendered(log));
  }

  console.log("\n/forget <n>: removes one page's own lines for good");
  {
    const {api, log} = load();
    for (let i = 0; i < 25; i++) api.chatLine("", "line " + i);
    ok("starts as 3 pages", log.children.length === 3);
    api.runChatSaid("/forget 2");
    ok("that page's own wrapper is actually gone", log.children.length === 2, log.children.length);
    ok("its own confirmation names the page and how many lines",
       rendered(log)[rendered(log).length - 1].includes("page 2 forgotten (10 lines removed)"),
       rendered(log));
    ok("page 1's own lines are untouched", rendered(log).some(l => l === "line 0"), rendered(log));
    ok("page 3's own lines are untouched, and its number was NOT shifted down to 2",
       rendered(log).some(l => l === "-- page 3 --"), rendered(log));

    api.runChatSaid("/forget 2");   // already gone
    ok("forgetting an already-forgotten page says so, doesn't crash",
       rendered(log)[rendered(log).length - 1].includes("already forgotten"), rendered(log));

    api.runChatSaid("/forget 99");
    ok("forgetting a page number that never existed says so",
       rendered(log)[rendered(log).length - 1].includes("no page 99"), rendered(log));
  }
  {
    const {api, log} = load();
    api.chatLine("", "one line");
    api.runChatSaid("/forget 1");   // forgets the CURRENTLY OPEN page
    api.chatLine("", "after forgetting the open page");
    ok("writing again after forgetting the only (open) page starts a fresh page 2, not a crash",
       rendered(log).some(l => l === "-- page 2 --") &&
       rendered(log).some(l => l === "after forgetting the open page"), rendered(log));
  }
  {
    const {api, log} = load();
    api.chatLine("", "before clear");
    api.runChatSaid("/clear");
    api.chatLine("", "after clear");
    ok("writing again after /clear lands in a fresh page (page numbering keeps climbing, never reused)",
       rendered(log).some(l => l === "-- page 2 --") &&
       rendered(log).some(l => l === "after clear") &&
       !rendered(log).some(l => l === "before clear"), rendered(log));
  }

  console.log("\nopenChat: the chat panel opens by default, and stays open -- there is no closing it");
  {
    const {api, modal} = load();
    api.openChat(false);
    ok("openChat actually marks the modal open", modal.classList.contains("on"));
  }
  {
    const {api, modal, fetchCalls} = load();
    api.openChat(false);
    api.setLive(true, {you: {name: "gabe"}, chat: []});
    api.runChatSaid("hello everyone");
    ok("sending an ordinary (no leading /) message does NOT close the panel",
       modal.classList.contains("on"));
    ok("...and it actually got sent, slash-free, to the others",
       fetchCalls.length === 1 && JSON.parse(fetchCalls[0].opts.body).text === "hello everyone",
       fetchCalls);
  }

  console.log("\n" + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}
