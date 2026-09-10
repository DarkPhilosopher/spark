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
// scrollTop/firstChild/200-line-trim, and easy to read back from.
class FakeLog {
  constructor() { this.children = []; this.scrollTop = 0; this.scrollHeight = 0; this._text = ""; }
  appendChild(c) { this.children.push(c); return c; }
  set textContent(v) { this.children = []; this._text = v; }
  get textContent() { return this._text; }
  get firstChild() { return this.children[0]; }
}
class FakeEl {
  constructor() { this.className = ""; this._text = ""; this.children = []; }
  appendChild(c) { this.children.push(c); return c; }
  set textContent(v) { this._text = v; this.children = []; }
  get textContent() {
    return this._text || this.children.map(c => c.text || c.textContent || "").join("");
  }
}

function load() {
  const log = new FakeLog();
  const $ = sel => (sel === "#chat-log" ? log
                   : {value: "", focus() {}, classList: {add() {}, remove() {}}});
  const documentStub = {
    createElement: () => new FakeEl(),
    createTextNode: t => ({text: String(t)}),
  };
  const fetchCalls = [];
  const fakeFetch = (url, opts) => { fetchCalls.push({url, opts}); return Promise.resolve({ok: true}); };
  const mod = {exports: {}};
  const body = src + `
    module.exports = {
      chatLine, showNewChat, runChatSaid, sendChatText, CHAT_COMMANDS,
      getSeenChat: () => seenChat, setSeenChat: v => { seenChat = v; },
      setLive: (v, snap) => { live = v; liveSnapshot = snap; },
      setProject: p => { project = p; },
    };
  `;
  new Function("module", "$", "document", "authHeaders", "fetch", "live", "liveSnapshot", "project", body)(
    mod, $, documentStub, () => ({}), fakeFetch, false, null, null);
  return {api: mod.exports, log, fetchCalls};
}

const rendered = log => log.children.map(el => {
  const who = el.children[0] && el.children[0].textContent;
  const rest = el.children.slice(1).map(c => c.text || "").join("");
  return who ? (who + rest) : el.textContent;
});

console.log("showNewChat: only new lines, never your own name twice");
{
  const {api, log} = load();
  api.setLive(true, {you: {name: "gabe"}, chat: [
    {n: 1, who: "gabe", text: "hi from me"},
    {n: 2, who: "ada", text: "hi back"},
  ]});
  api.showNewChat();
  ok("my own line (already shown when sent) is skipped", rendered(log).length === 1, rendered(log));
  ok("someone else's line shows", rendered(log)[0].includes("hi back"), rendered(log));
  ok("seenChat advances to the highest n seen", api.getSeenChat() === 2);

  api.showNewChat();   // same snapshot again -- nothing new
  ok("polling the same snapshot again adds nothing", rendered(log).length === 1, rendered(log));

  api.setLive(true, {you: {name: "gabe"}, chat: [
    {n: 1, who: "gabe", text: "hi from me"},
    {n: 2, who: "ada", text: "hi back"},
    {n: 3, who: "ada", text: "you there?"},
  ]});
  api.showNewChat();
  ok("only the genuinely new line (n=3) gets added, not n=1/2 again",
     rendered(log).length === 2 && rendered(log)[1].includes("you there"), rendered(log));
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

    runHelpTests();
  });
}

console.log("\n/help: shows the loaded game's own instructions, when it has any");
function runHelpTests() {
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
       rendered(log)[0].includes("/who"), rendered(log));
  }

  console.log("\n" + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}
