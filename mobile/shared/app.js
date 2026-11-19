"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const youtubePanel = $("youtubePanel");
  const queue = [];
  const youtubeHosts = new Set(["youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"]);
  const videoId = /^[A-Za-z0-9_-]{11}$/;
  const playlistId = /^[A-Za-z0-9_-]{10,80}$/;

  function safeUrl(raw, hosts) {
    if (typeof raw !== "string" || raw.length > 2048) throw new Error("Paste a valid share link.");
    const value = raw.trim();
    if (!value || /[\u0000-\u001f\u007f]/.test(value)) throw new Error("The link contains invalid characters.");
    let url;
    try { url = new URL(value); } catch (_) { throw new Error("That link is not valid."); }
    if (url.protocol !== "https:" || !hosts.has((url.hostname || "").toLowerCase()) ||
        url.username || url.password || (url.port && url.port !== "443")) {
      throw new Error("Use an official HTTPS link.");
    }
    return url;
  }

  function youtubeKind(raw) {
    const url = safeUrl(raw, youtubeHosts);
    const parts = url.pathname.split("/").filter(Boolean);
    if (url.hostname === "youtu.be") {
      if (parts[0] && videoId.test(parts[0])) return "Video";
      throw new Error("That shortened link has no valid video ID.");
    }
    if (parts.length === 1 && parts[0] === "watch") {
      if (videoId.test(url.searchParams.get("v") || "")) return "Video";
      throw new Error("That link has no valid video ID.");
    }
    if (parts.length === 2 && ["shorts", "live", "embed", "v"].includes(parts[0]) && videoId.test(parts[1])) return "Video";
    if (parts.length === 1 && parts[0] === "playlist" && playlistId.test(url.searchParams.get("list") || "")) return "Playlist";
    throw new Error("Use a YouTube video or playlist link.");
  }

  function showStatus(id, message, isError) {
    const node = $(id);
    node.textContent = message;
    node.style.color = isError ? "#ff9292" : "";
  }

  async function pasteInto(input, statusId) {
    try {
      if (!navigator.clipboard || !navigator.clipboard.readText) throw new Error("Clipboard access is not available here. Paste into the field instead.");
      input.value = (await navigator.clipboard.readText()).trim();
      input.focus();
    } catch (error) {
      showStatus(statusId, error.message || "Paste into the field instead.", true);
    }
  }

  function renderQueue() {
    $("queueCount").textContent = queue.length + (queue.length === 1 ? " ITEM" : " ITEMS");
    $("emptyState").classList.toggle("is-hidden", queue.length > 0);
    $("queueList").classList.toggle("is-hidden", queue.length === 0);
    $("clearQueue").disabled = queue.length === 0;
    const list = $("queueList");
    list.replaceChildren();
    queue.forEach((item) => {
      const li = document.createElement("li");
      const copy = document.createElement("div");
      const title = document.createElement("strong");
      const meta = document.createElement("small");
      const chip = document.createElement("span");
      title.textContent = item.kind + " · " + item.format;
      meta.textContent = item.source;
      chip.className = "queue-chip";
      chip.textContent = "PREVIEW";
      copy.append(title, meta);
      li.append(copy, chip);
      list.appendChild(li);
    });
  }

  $("pasteYoutube").addEventListener("click", () => pasteInto($("youtubeUrl"), "youtubeStatus"));

  $("addQueue").addEventListener("click", () => {
    try {
      const kind = youtubeKind($("youtubeUrl").value);
      if (!$("permission").checked) throw new Error("Confirm that the source permits this save.");
      if (kind === "Playlist" && !$("playlist").checked) throw new Error("Enable Full playlist for this link.");
      if (queue.length >= 50) throw new Error("The preview queue is full.");
      queue.push({kind, format: $("format").value, source: "YouTube"});
      renderQueue();
      $("youtubeUrl").value = "";
      showStatus("youtubeStatus", "Added to preview queue. Mobile downloads are not connected yet.", false);
    } catch (error) {
      showStatus("youtubeStatus", error.message, true);
    }
  });

  $("clearQueue").addEventListener("click", () => {
    queue.splice(0, queue.length);
    renderQueue();
    showStatus("youtubeStatus", "Preview queue cleared.", false);
  });

  renderQueue();
})();
