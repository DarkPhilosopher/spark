// Pull the deck out of index.html and drive it with a stub DOM, since there is
// no browser here to run it in -- the same trick store.test.js uses.
//
// What is worth testing here is not the grid, which is CSS and has to be looked
// at, but the box you type in: which commands exist, what /pin makes of its
// argument, that an unknown command says so instead of being sent to everybody
// as chat, and that /swap side chat remembers which side it left things on.

const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");

const src = html.slice(html.indexOf("const LS_SWAP"),
                       html.indexOf("// ------------------------------------------- your own tiles, in Python"));

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra ? "  -> " + extra : "")); }
};

/* The smallest DOM the deck touches: a log it appends lines to, a #deck whose
   classList we can inspect, and localStorage. */
function harness(opts = {}) {
  const log = [];
  const classes = new Set();
  const nodes = {
    "#log": {
      children: [], textContent: "", scrollTop: 0, scrollHeight: 0,
      append(n) { this.children.push(n); log.push(n); },
      get firstChild() { return this.children[0]; },
      removeChild() { this.children.shift(); },
    },
    "#deck": {classList: {
      add: c => classes.add(c), remove: c => classes.delete(c),
      contains: c => classes.has(c),
      toggle: (c, on) => (on === undefined ? (classes.has(c) ? classes.delete(c)
                                                             : classes.add(c))
                                           : (on ? classes.add(c)
                                                 : classes.delete(c))),
    }},
    "#keys": {textContent: "", append() {}},
    "#page": {hidden: false},
    "#pagename": {textContent: ""},
  };
  nodes["#log"].firstChild = {remove() { nodes["#log"].children.shift(); }};

  const store = {};
  const globals = {
    $: sel => nodes[sel] || {textContent: "", append() {}, classList:
      {add() {}, remove() {}, toggle() {}, contains: () => false}},
    el: (tag, cls, text) => ({tag, cls, text: text ?? "",
                              append(...kids) {
                                for (const k of kids)
                                  this.text += (k && k.text !== undefined)
                                    ? k.text : String(k);
                              }}),
    document: {createTextNode: t => ({text: String(t)}),
               querySelectorAll: () => []},
    localStorage: {
      getItem: k => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = String(v); },
      removeItem: k => { delete store[k]; },
    },
    window: {scrollTo() {}},
    location: {href: ""},
    me: {name: "you", role: "owner"},
    project: {name: "g", characters: [], tiles: []},
    liveSnap: opts.snap || null,
    storeMode: opts.mode || "static",
    fetchCalls: [],
  };

  const body = `
    ${src}
    // things the deck leans on that live elsewhere in the page
    module.exports = {runSaid, COMMANDS, quoted, pinned: () => pinned,
                      DECK, note, classes, log, store,
                      swapped: () => classes.has("swapped")};
  `;
  const mod = {exports: {}};
  const store_obj = {mode: globals.storeMode, saveGame: async () => ({where: "x"})};
  new Function(
    "module", "$", "el", "document", "localStorage", "window", "location",
    "me", "project", "liveSnap", "store", "fetch", "authHeaders", "btoa",
    "unescape", "encodeURIComponent", "startLive", "loadGames", "say",
    "openPage", "closePage", "classes", "log",
    body)(
      mod, globals.$, globals.el, globals.document, globals.localStorage,
      globals.window, globals.location, globals.me, globals.project,
      globals.liveSnap, store_obj,
      async (url, o) => { globals.fetchCalls.push({url, o});
                          return {ok: true, json: async () => ({}) }; },
      () => ({}), s => Buffer.from(s, "binary").toString("base64"),
      s => s, s => s, () => {}, async () => {}, () => {},
      () => {}, () => {}, classesOf(classes), log);
  mod.exports.fetchCalls = globals.fetchCalls;
  mod.exports.storeBack = store;
  return mod.exports;
}
function classesOf(set) { return set; }

(async () => {

console.log("what the box understands\n");
{
  const d = harness();
  ok("the six buttons are the ones asked for",
     d.DECK.map(x => x.key).join(",") === "play,edit,characters,brain,tiles,save",
     d.DECK.map(x => x.key).join(","));
  for (const key of ["play", "edit", "characters", "brain", "tiles", "save"])
    ok("/" + key + " is a command too", typeof d.COMMANDS[key] === "function");
  for (const key of ["help", "pin", "pins", "unpin", "swap", "clear", "who"])
    ok("/" + key + " exists", typeof d.COMMANDS[key] === "function");
}

console.log("\n/pin takes its note with or without quotes");
{
  const d = harness();
  ok('quoted:   /pin "feed the bug"', d.quoted('"feed the bug"') === "feed the bug");
  ok("single:   /pin 'feed the bug'", d.quoted("'feed the bug'") === "feed the bug");
  ok("bare:     /pin feed the bug", d.quoted("feed the bug") === "feed the bug");
  ok("trimmed", d.quoted("   spaced   ") === "spaced");
  ok("empty stays empty", d.quoted("") === "");
}
{
  const d = harness();
  await d.runSaid('/pin "feed the bug first"');
  ok("pinning keeps it", d.pinned()[0] === "feed the bug first", d.pinned());
  await d.runSaid("/pin second one");
  ok("a second note", d.pinned().length === 2, d.pinned());
  ok("notes survive in localStorage",
     JSON.parse(d.storeBack["spark:pins"] || "[]").length === 2,
     d.storeBack["spark:pins"]);
  await d.runSaid("/unpin 1");
  ok("unpin removes the right one",
     d.pinned().length === 1 && d.pinned()[0] === "second one", d.pinned());
  await d.runSaid("/unpin 9");
  ok("unpin out of range is refused, not a crash", d.pinned().length === 1);
  await d.runSaid("/pin");
  ok("pinning nothing is refused", d.pinned().length === 1);
}

console.log("\n/swap side chat");
{
  const d = harness();
  ok("starts on the right", !d.swapped());
  await d.runSaid("/swap side chat");
  ok("swaps to the left", d.swapped());
  ok("...and remembers", d.storeBack["spark:chatside"] === "left");
  await d.runSaid("/swap side chat");
  ok("swaps back", !d.swapped());
  ok("...and remembers that too", d.storeBack["spark:chatside"] === "right");
  await d.runSaid("/swap side chat left");
  ok("naming a side goes there", d.swapped());
  await d.runSaid("/swap side chat left");
  ok("...and naming it again keeps it there", d.swapped());
  await d.runSaid("/swap nonsense");
  ok("a swap it does not understand is refused", d.swapped());
}

console.log("\nwhat is a command and what is chat");
{
  const d = harness({mode: "static"});
  await d.runSaid("/nosuchthing");
  const said = d.log.map(l => l.text).join(" | ");
  ok("an unknown command says so", /no such command/.test(said), said);
  ok("...and is NOT sent to everybody as chat",
     !/could not say/.test(said) && !/nobody to talk/.test(said), said);
}
{
  const d = harness({mode: "static"});
  await d.runSaid("hello everyone");
  const said = d.log.map(l => l.text).join(" | ");
  ok("plain words with no server say there is nobody to talk to",
     /nobody to talk to/.test(said), said);
}
{
  const d = harness();
  const before = d.log.length;
  await d.runSaid("   ");
  ok("an empty line does nothing at all", d.log.length === before);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
})();
