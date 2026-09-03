// Pull the storage layer out of index.html and drive it with fake
// fetch/localStorage, since there is no browser here to run it in.
const fs = require("fs");
const html = fs.readFileSync(require("path").join(__dirname,"..","index.html"), "utf8");
const src = html.slice(html.indexOf("const LS_GAME"),
                       html.indexOf("function openGitHubSettings"));

let calls = [];
const store_src = `
  ${src}
  module.exports = {store, ghConfig, b64};
`;

function harness(routes, ls) {
  calls = [];
  global.localStorage = Object.assign(ls || {}, {
    getItem(k){ return Object.prototype.hasOwnProperty.call(this,k) ? this[k] : null; },
    setItem(k,v){ this[k]=v; },
    removeItem(k){ delete this[k]; },
  });
  global.fetch = async (url, opts) => {
    calls.push({url, method:(opts&&opts.method)||"GET", body:opts&&opts.body});
    const hit = routes[url.split("?")[0]];
    if (hit === undefined) throw new Error("network");
    if (hit === 404) return {ok:false, status:404, json: async()=>({message:"nope"})};
    return {ok:true, status:200, json: async()=>hit};
  };
  global.btoa = s => Buffer.from(s, "binary").toString("base64");
  global.TextEncoder = require("util").TextEncoder;
  const mod = {exports:{}};
  new Function("module","localStorage","fetch","btoa","TextEncoder", store_src)
    (mod, global.localStorage, global.fetch, global.btoa, global.TextEncoder);
  return mod.exports;
}

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra ? "  -> " + extra : "")); }
};

(async () => {
console.log("mode detection");
{
  const {store} = harness({"api/tiles": {sensors:[1],actions:[]}});
  await store.init();
  ok("server API present -> server mode", store.mode === "server", store.mode);
}
{
  const {store} = harness({"tiles.json": {sensors:[1,2],actions:[]}});
  const cat = await store.init();               // api/tiles throws
  ok("no API -> static mode", store.mode === "static", store.mode);
  ok("falls back to tiles.json", cat.sensors.length === 2);
}
{
  const {store} = harness({});
  let threw = false;
  try { await store.init(); } catch (e) { threw = /tiles.json/.test(e.message); }
  ok("no tiles.json at all -> clear error", threw);
}

console.log("listing and loading");
{
  const {store} = harness({"tiles.json":{}, "games/index.json":["chase","maze"]},
                          {"spark:game:mine": "{}", "spark:game:chase": "{}"});
  await store.init();
  const names = await store.listGames();
  ok("merges shipped + browser games, deduped",
     JSON.stringify(names) === '["chase","maze","mine"]', JSON.stringify(names));
}
{
  const {store} = harness({"tiles.json":{}, "games/chase.json":{name:"shipped"}},
                          {"spark:game:chase": JSON.stringify({name:"edited"})});
  await store.init();
  const g = await store.loadGame("chase");
  ok("browser edit wins over shipped file", g.name === "edited", g.name);
}
{
  const {store} = harness({"tiles.json":{}, "games/chase.json":{name:"shipped"}});
  await store.init();
  const g = await store.loadGame("chase");
  ok("unedited game comes from the repo file", g.name === "shipped");
  ok("missing game returns null", (await store.loadGame("ghost")) === null);
}

console.log("saving");
{
  const {store} = harness({"tiles.json":{}, "games/index.json":[]});
  await store.init();
  const out = await store.saveGame({name:"my game", characters:[]});
  ok("no token -> browser only", out.where === "this browser", JSON.stringify(out));
  ok("written to localStorage",
     !!global.localStorage["spark:game:my game"]);
}
{
  const {store} = harness({"tiles.json":{}});
  await store.init();
  const out = await store.saveGame({name:"../../evil", characters:[]});
  ok("path characters stripped from the name", out.where && !!global.localStorage["spark:game:evil"],
     JSON.stringify(Object.keys(global.localStorage).filter(k=>k.startsWith("spark:game"))));
  const blank = await store.saveGame({name:"///"});
  ok("empty name refused", blank.error === "give the game a name");
}
{
  const gh = {owner:"me", repo:"spark", branch:"main", token:"ghp_x"};
  const {store} = harness({
    "tiles.json":{}, "games/index.json":["chase"],
    "https://api.github.com/repos/me/spark/contents/games/lava.json": {sha:"abc"},
    "https://api.github.com/repos/me/spark/contents/games/index.json": {sha:"def"},
  }, {"spark:github": JSON.stringify(gh)});
  await store.init();
  const out = await store.saveGame({name:"lava", characters:[{kind:"héro"}]});
  const puts = calls.filter(c => c.method === "PUT");
  ok("commits the game and the listing", puts.length === 2, puts.length);
  ok("reports both destinations", /this browser \+ me\/spark/.test(out.where), out.where);
  const body = JSON.parse(puts[0].body);
  ok("sends the existing sha so updates do not conflict", body.sha === "abc");
  const decoded = Buffer.from(body.content, "base64").toString("utf8");
  ok("content survives non-ascii round trip", JSON.parse(decoded).characters[0].kind === "héro",
     decoded.slice(0,60));
}
{
  const gh = {owner:"me", repo:"spark", token:"ghp_x"};
  const {store} = harness({"tiles.json":{}, "games/index.json":[]},
                          {"spark:github": JSON.stringify(gh)});
  await store.init();      // github contents URL missing -> fetch throws
  const out = await store.saveGame({name:"solo", characters:[]});
  ok("GitHub failure still saves locally and warns",
     out.where === "this browser" && /GitHub/.test(out.warn || ""), JSON.stringify(out));
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
})();
