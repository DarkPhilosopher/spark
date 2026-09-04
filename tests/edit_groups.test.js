// The button editor's list groups every editable button/bubble/slot under
// a numbered "button group 00N" heading (see EDIT_GROUPS/renderEditList()
// in world3d.html) instead of one flat list of everything on the page.
// What's worth checking computationally is the classification itself --
// does every uid actually in use end up in the group a person would
// expect, and does an unrecognised one fall into "other" rather than
// silently vanishing or crashing.

const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "world3d.html"), "utf8");

const s = html.indexOf("const EDIT_GROUPS = [");
if (s < 0) throw new Error("marker not found: const EDIT_GROUPS = [");
const e = html.indexOf("\n\nfunction renderEditList", s);
if (e < 0) throw new Error("end marker not found: function renderEditList");
const src = html.slice(s, e);

const mod = {exports: {}};
new Function("module", src + "\nmodule.exports = {EDIT_GROUPS};")(mod);
const {EDIT_GROUPS} = mod.exports;

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
};

// Same lookup renderEditList() itself does: the index of the first group
// whose match() accepts this uid, or -1 for "other".
const groupOf = uid => EDIT_GROUPS.findIndex(g => g.match(uid));
const nameOf = uid => { const i = groupOf(uid); return i < 0 ? "other" : EDIT_GROUPS[i].name; };

console.log("every real uid in the app lands in the group a person would expect");
{
  const cases = [
    ["up", "pad (move)"], ["left", "pad (move)"], ["right", "pad (move)"], ["down", "pad (move)"],
    ["e", "pad (actions)"], ["f", "pad (actions)"], ["space", "pad (actions)"],
    ["s", "pad (actions)"], ["w", "pad (actions)"],
    ["restart", "top bar"], ["recentre", "top bar"], ["fullscreen", "top bar"], ["mode", "top bar"],
    ["save", "top bar"], ["save-as", "top bar"], ["backpack-toggle", "top bar"],
    ["properties-toggle", "top bar"],
    ["drawer:left:add", "button drawer"], ["drawer:left:remove", "button drawer"],
    ["drawer:left:bub7f3ac21", "button drawer"],
    ["quickbar:0", "quickbar"], ["quickbar:6", "quickbar"],
  ];
  for (const [uid, expected] of cases) ok(uid + " -> " + expected, nameOf(uid) === expected, nameOf(uid));
}

console.log("\nan unrecognised uid falls into \"other\" rather than a wrong group or a crash");
{
  ok("a made-up uid matches nothing", groupOf("something-nobody-registered") < 0);
  ok("edit-toggle itself isn't editable, so it isn't in any group either",
     groupOf("edit-toggle") < 0);
}

console.log("\nno two groups claim the same uid (every button ends up in exactly one)");
{
  const sample = ["up", "left", "right", "down", "e", "f", "space", "s", "w",
                   "restart", "recentre", "fullscreen", "mode", "save", "save-as",
                   "backpack-toggle", "properties-toggle"];
  for (const uid of sample) {
    const matches = EDIT_GROUPS.filter(g => g.match(uid)).length;
    ok(uid + " matches exactly one group, not zero or several", matches === 1, matches);
  }
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
