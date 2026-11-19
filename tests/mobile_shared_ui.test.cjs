const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class FakeElement {
  constructor(id = "") {
    this.id = id;
    this.value = "";
    this.checked = false;
    this.disabled = false;
    this.textContent = "";
    this.style = {};
    this.dataset = {};
    this.attributes = {};
    this.listeners = new Map();
    this.children = [];
    const classes = new Set();
    this.classList = {
      add: (name) => classes.add(name),
      contains: (name) => classes.has(name),
      toggle: (name, force) => {
        const enabled = force === undefined ? !classes.has(name) : Boolean(force);
        if (enabled) classes.add(name);
        else classes.delete(name);
        return enabled;
      },
    };
  }

  addEventListener(name, callback) {
    this.listeners.set(name, callback);
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
  }

  append(...children) {
    this.children.push(...children);
  }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  replaceChildren(...children) {
    this.children = [...children];
  }

  focus() {}

  async click() {
    if (this.disabled) return;
    const callback = this.listeners.get("click");
    assert.ok(callback, `button #${this.id} has no click handler`);
    return callback({ target: this });
  }
}

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "mobile/shared/index.html"), "utf8");
const source = fs.readFileSync(path.join(root, "mobile/shared/app.js"), "utf8");
assert.doesNotMatch(html, /spotify/i);
const elements = new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(([, id]) => [id, new FakeElement(id)]));
const requiredIds = [
  "youtubePanel", "youtubeUrl", "pasteYoutube", "addQueue", "clearQueue", "format", "playlist",
  "permission", "queueCount", "emptyState", "queueList", "youtubeStatus",
];
for (const id of requiredIds) assert.ok(elements.has(id), `shared HTML is missing #${id}`);
elements.get("queueList").classList.add("is-hidden");
elements.get("format").value = "MP3";
elements.get("clearQueue").disabled = true;

let clipboardText = "";
let clipboardError = false;
const context = {
  document: {
    getElementById: (id) => elements.get(id) || null,
    createElement: () => new FakeElement(),
  },
  navigator: { clipboard: { readText: async () => {
    if (clipboardError) throw new Error("Clipboard unavailable");
    return clipboardText;
  } } },
  URL,
  console,
};
vm.runInNewContext(source, context, { filename: "mobile/shared/app.js" });

const $ = (id) => elements.get(id);
const status = (id) => $(id).textContent;
const buttonIds = [...html.matchAll(/<button\b[^>]*\bid="([^"]+)"/g)].map(([, id]) => id);
for (const id of buttonIds) assert.ok($(id).listeners.has("click"), `button #${id} is not wired`);

async function main() {
  clipboardError = true;
  await $("pasteYoutube").click();
  assert.match(status("youtubeStatus"), /Clipboard unavailable/);
  clipboardError = false;
  clipboardText = " https://youtu.be/BaW_jenozKc ";
  await $("pasteYoutube").click();
  assert.equal($("youtubeUrl").value, "https://youtu.be/BaW_jenozKc");
  $("youtubeUrl").value = "bad link";
  await $("addQueue").click();
  assert.match(status("youtubeStatus"), /not valid/i);
  $("youtubeUrl").value = "https://youtu.be/BaW_jenozKc";
  await $("addQueue").click();
  assert.match(status("youtubeStatus"), /confirm/i);
  $("permission").checked = true;
  await $("addQueue").click();
  assert.match(status("youtubeStatus"), /Added to preview queue/);
  assert.equal($("queueCount").textContent, "1 ITEM");
  assert.equal($("queueList").children.length, 1);
  assert.match($("queueList").children[0].children[0].children[0].textContent, /Video · MP3/);

  $("youtubeUrl").value = "https://www.youtube.com/playlist?list=PL1234567890";
  await $("addQueue").click();
  assert.match(status("youtubeStatus"), /Enable Full playlist/i);
  $("playlist").checked = true;
  await $("addQueue").click();
  assert.equal($("queueCount").textContent, "2 ITEMS");

  for (let index = 0; index < 48; index += 1) {
    $("youtubeUrl").value = "https://youtu.be/BaW_jenozKc";
    await $("addQueue").click();
  }
  assert.equal($("queueCount").textContent, "50 ITEMS");
  $("youtubeUrl").value = "https://youtu.be/BaW_jenozKc";
  await $("addQueue").click();
  assert.match(status("youtubeStatus"), /queue is full/i);

  await $("clearQueue").click();
  assert.equal($("queueCount").textContent, "0 ITEMS");
  assert.equal($("queueList").children.length, 0);
  assert.equal($("clearQueue").disabled, true);
  assert.match(status("youtubeStatus"), /cleared/i);
  console.log(`Passed shared mobile UI interactions for ${buttonIds.length} buttons.`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
