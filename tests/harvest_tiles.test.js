// give_item/has_item/harvestable -- the JS twin of engine/tiles.py's own
// give_item/has_item/harvestable, checked here against the exact same
// cases tests/check_harvest.py runs against the Python engine. Not the
// same mechanism as check_engines.py's shared snapshot/parity harness
// (deliberately not extended for this -- see the long comment at the top
// of check_harvest.py for why), but the same goal: catching either
// engine quietly drifting from what the other one does.

const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "world3d.html"), "utf8");

const s = html.indexOf("const num = ");
if (s < 0) throw new Error("marker not found: const num = ");
const e = html.indexOf("// ==== SPARK-ENGINE-END ====", s);
if (e < 0) throw new Error("end marker not found: SPARK-ENGINE-END");
const src = html.slice(s, e);

const mod = {exports: {}};
new Function("module", src + "\nmodule.exports = {Thing, SENSORS, ACTIONS};")(mod);
const {Thing, SENSORS, ACTIONS} = mod.exports;

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
};

const thing = (kind) => new Thing(kind, 0, 0, {glyph: kind[0], color: "white"});
const give = (obj, world, target, item, amount, it) =>
  ACTIONS.give_item(obj, world, {target, item, amount}, it);

console.log("give_item: builds up, and can take away, a Thing's own count");
{
  const hero = thing("hero"), world = {};
  give(hero, world, "self", "gold", 3);
  ok("a fresh item starts from zero and counts up", hero.inventory.gold === 3, hero.inventory);

  give(hero, world, "self", "gold", 4);
  ok("giving the same item again adds to what's already there", hero.inventory.gold === 7, hero.inventory);

  give(hero, world, "self", "gold", -2);
  ok("a negative amount takes some away", hero.inventory.gold === 5, hero.inventory);

  give(hero, world, "self", "gold", -99);
  ok("taking away more than there is stops at zero, not negative", hero.inventory.gold === 0, hero.inventory);

  give(hero, world, "self", "silver", 1);
  ok("different items keep their own separate counts",
     hero.inventory.gold === 0 && hero.inventory.silver === 1, hero.inventory);

  const fresh = thing("hero");
  give(fresh, world, "self", "  ", 5);
  ok("a blank item name gives nothing, doesn't crash", Object.keys(fresh.inventory).length === 0, fresh.inventory);
}

console.log("\nhas_item: reads a Thing's own count, never world memory");
{
  const hero = thing("hero"), world = {};
  ok("an item nobody's ever been given at all reads as zero, not missing",
     SENSORS.has_item(hero, world, {item: "gold", amount: 1}) === false);

  give(hero, world, "self", "gold", 5);
  ok("has_item sees a count given the very same call",
     SENSORS.has_item(hero, world, {item: "gold", amount: 5}) === true);
  ok("has_item with too few of the item stays false",
     SENSORS.has_item(hero, world, {item: "gold", amount: 6}) === false);

  const hero2 = thing("hero"), chest = thing("chest"), world2 = {};
  give(hero2, world2, "it", "gold", 10, chest);
  ok("give_item(it, ...) gives to the touched object, not the toucher",
     chest.inventory.gold === 10 && !hero2.inventory.gold, [hero2.inventory, chest.inventory]);
}

console.log("\nharvestable: stamps config onto a Thing, nothing more");
{
  const hero = thing("hero"), world = {};
  ACTIONS.harvestable(hero, world, {target: "self", item: "wood", amount: 2, seconds: 3, flashes: 5});
  ok("harvest config lands exactly as given",
     JSON.stringify(hero.harvest) === JSON.stringify({item: "wood", amount: 2, seconds: 3, flashes: 5}),
     hero.harvest);

  const hero2 = thing("hero");
  ACTIONS.harvestable(hero2, world, {target: "self", item: "wood", amount: 0, seconds: 0, flashes: 0});
  ok("amount/seconds/flashes can never be stamped as zero or negative -- floored at 1",
     JSON.stringify(hero2.harvest) === JSON.stringify({item: "wood", amount: 1, seconds: 1, flashes: 1}),
     hero2.harvest);

  const hero3 = thing("hero");
  ACTIONS.harvestable(hero3, world, {target: "self", item: "  ", amount: 1, seconds: 1, flashes: 1});
  ok("a blank item name falls back to the word \"item\", not empty", hero3.harvest.item === "item", hero3.harvest);

  const hero4 = thing("hero");
  ACTIONS.harvestable(hero4, world, {target: "self", item: "wood", amount: 1, seconds: 5, flashes: 4});
  ACTIONS.harvestable(hero4, world, {target: "self", item: "stone", amount: 9, seconds: 1, flashes: 1});
  ok("calling harvestable again replaces the config, last call wins", hero4.harvest.item === "stone", hero4.harvest);

  const hero5 = thing("hero"), rock = thing("rock");
  ACTIONS.harvestable(hero5, world, {target: "it", item: "ore", amount: 1, seconds: 1, flashes: 1}, rock);
  ok("target:it marks the touched object, not the toucher",
     rock.harvest && rock.harvest.item === "ore" && !hero5.harvest, [hero5.harvest, rock.harvest]);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
