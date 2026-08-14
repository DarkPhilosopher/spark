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

// Every screen must be a list of buttons, so that the formation is the same
// wherever you are -- that is the whole point of the redesign. These are read
// straight out of the source rather than run, because building them needs the
// rest of the page.
const SCREENS = ["homeScreen", "editScreen", "worldScreen", "gamesScreen",
                 "castScreen", "oneCharScreen", "brainScreen", "oneRowScreen",
                 "tilesScreen"];

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
                      note, classes, log, store,
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

console.log("every screen is buttons, not a page\n");
{
  for (const name of SCREENS)
    ok(name + " exists", new RegExp("function " + name + "\\b").test(src));
  // Each screen returns {name, items:[...]} -- if one ever returned markup
  // instead, the formation would break on that screen only, which is exactly
  // the thing the redesign was meant to end.
  for (const name of SCREENS) {
    const at = src.indexOf("function " + name);
    const body = src.slice(at, src.indexOf("\nfunction ", at + 10));
    ok(name + " returns items", /items\s*[:=]/.test(body), name);
  }
  ok("the six on the home screen are the ones asked for",
     ["play", "edit", "characters", "brain", "tiles", "save"].every(k =>
       new RegExp('item\\("' + k + '"').test(src)));
  ok("there is a back that pops one screen", /function deckPop\b/.test(src));
  ok("...and a way home", /function deckHome\b/.test(src));
  ok("the tile palette is a screen too, so it scrolls in formation",
     /function pickTileScreen\b/.test(src));
}

console.log("\nwhat the box understands");
{
  const d = harness();
  for (const key of ["play", "edit", "characters", "brain", "tiles", "save"])
    ok("/" + key + " is a command too", typeof d.COMMANDS[key] === "function");
  for (const key of ["help", "pin", "pins", "unpin", "swap", "clear", "who",
                     "back", "home"])
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

/* Actually build each screen, rather than only reading the source.
 *
 * This is the part that earns its keep: it is how the missing deckSave was
 * found. A screen that references something that no longer exists parses
 * perfectly and only falls over when somebody presses the button. */
function screens() {
  const project = {
    name: "probe", world: {width: 30, height: 14, wrap: false, speed: 6},
    tiles: [{name: "hunt", when: [{tile: "see", args: {}}],
             do: [{tile: "move", args: {}}]}],
    characters: [
      {kind: "hero", glyph: "@", color: "cyan", health: 3, count: 1,
       solid: false, role: "player",
       brain: [{when: [{tile: "always", args: {}}],
                do: [{tile: "move", args: {dir: "up"}}]}]},
      {kind: "apple", glyph: "o", color: "green", health: 1, count: 2,
       solid: false, role: "prop", brain: []},
    ],
  };
  const catalog = {
    colors: ["white", "red", "cyan"],
    sensors: [{id: "always", label: "always", params: []},
              {id: "combo", label: 'the tile called "{name}"', params: []}],
    actions: [{id: "move", label: "move {dir}", params: []},
              {id: "combo", label: 'the tile called "{name}"', params: []}],
  };
  const names = ["homeScreen", "editScreen", "worldScreen", "gamesScreen",
                 "castScreen", "oneCharScreen", "brainScreen", "oneRowScreen",
                 "tilesScreen"];
  const body = `
    ${src}
    module.exports = {${names.join(", ")}, deckPush, deckPop, deckHome,
                      renderDeck, stack};
  `;
  const nodes = {
    "#keys": {textContent: "", scrollTop: 0, append() {}},
    "#screen": {textContent: ""},
    "#backkey": {disabled: false},
    "#log": {children: [], append() {}, scrollTop: 0, scrollHeight: 0},
    "#deck": {classList: {add() {}, remove() {}, toggle() {},
                          contains: () => false}},
    "#page": {hidden: true},
    "#codepanel": {hidden: false, open: false},
  };
  const mod = {exports: {}};
  const args = {
    module: mod,
    $: sel => nodes[sel] || {textContent: "", hidden: false, append() {},
                             classList: {add() {}, remove() {}, toggle() {},
                                         contains: () => false}},
    el: (tag, cls, text) => ({tag, cls, text: text ?? "", append() {}}),
    document: {createTextNode: t => ({text: t}), querySelectorAll: () => []},
    localStorage: {getItem: () => null, setItem() {}, removeItem() {}},
    window: {scrollTo() {}}, location: {href: ""},
    project, catalog, store: {mode: "server", saveGame: async () => ({}),
                              deleteGame: async () => {}},
    chars: () => project.characters,
    cur: () => project.characters[0],
    myTiles: () => project.tiles,
    past: [], codeFiles: [], showEverything: true,
    charIdx: 0, rowIdx: 0, side: "when",
    amEditor: () => true,
    describe: (s, use) => use.tile,
    fitsHalf: () => true,
    ghConfig: () => null,
    note() {}, say() {}, renderAll() {}, renderRows() {}, paintUndo() {},
    remember() {}, undo() {}, addTile() {}, openParams() {}, foldRow() {},
    unfold() {}, openHostPanel() {}, openGitHubSettings() {},
    openGame: async () => {}, loadGames: async () => {},
    blankProject: n => ({name: n, characters: [], tiles: [], world: {}}),
    newChar: (k, g) => ({kind: k, glyph: g, brain: []}),
    startLive() {}, authHeaders: () => ({}), fetch: async () => ({ok: true}),
    btoa: s => Buffer.from(s, "binary").toString("base64"),
    unescape: s => s, encodeURIComponent: s => s,
    gameNames: ["probe", "chase"], liveSnap: null,
    me: {role: "owner", name: "host"},
  };
  new Function(...Object.keys(args), body)(...Object.values(args));
  return {api: mod.exports, names};
}

console.log("\nevery screen actually builds");
{
  const {api, names} = screens();
  for (const name of names) {
    let out = null, err = null;
    try { out = api[name](); } catch (e) { err = e.message; }
    ok(name + " builds without falling over", out && Array.isArray(out.items),
       err || JSON.stringify(out));
    if (out && out.items)
      ok("...and every button on it does something",
         out.items.filter(Boolean).every(i => typeof i.go === "function"),
         name);
  }
  const {api: a2} = screens();
  ok("home is the bottom of the stack, so back stops there",
     (a2.deckHome(), a2.stack.length === 1), a2.stack.length);
  a2.deckPush(a2.editScreen);
  ok("opening a screen pushes it", a2.stack.length === 2);
  a2.deckPop();
  ok("back pops it", a2.stack.length === 1);
  a2.deckPop();
  ok("back at the bottom does nothing", a2.stack.length === 1);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
})();
