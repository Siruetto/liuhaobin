const state = {
  lastEventId: 0,
  reminders: [],
  popupReminderId: null,
  recognition: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {"Content-Type": "application/json"},
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "请求失败");
  }
  return data;
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.add("hidden"), 2200);
}

function addMessage(role, text, actions = []) {
  const log = $("#chat-log");
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "我" : "鸟";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  bubble.appendChild(paragraph);
  const actionText = actions.map((item) => `${item.tool} ${item.ok ? "✓" : "✗"}`).join(" · ");
  if (actionText) {
    const line = document.createElement("div");
    line.className = "action-line";
    line.textContent = `工具: ${actionText}`;
    bubble.appendChild(line);
  }
  article.append(avatar, bubble);
  log.appendChild(article);
  log.scrollTop = log.scrollHeight;
}

async function sendMessage(text) {
  const message = (text || "").trim();
  if (!message) return;
  addMessage("user", message);
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({message}),
    });
    addMessage("bot", data.reply, data.actions);
    state.reminders = data.reminders || [];
    renderReminders();
  } catch (error) {
    addMessage("bot", `出错了：${error.message}`);
  }
}

function typeLabel(type) {
  return {once: "一次性", daily: "每天", interval: "间隔"}[type] || type;
}

function reminderCard(reminder, compact = true) {
  const card = document.createElement("article");
  card.className = "reminder";
  const head = document.createElement("header");
  const time = document.createElement("time");
  time.textContent = reminder.remind_at;
  const tag = document.createElement("span");
  tag.className = "type-tag";
  tag.textContent = typeLabel(reminder.repeat_type);
  head.append(time, tag);
  const content = document.createElement("p");
  content.textContent = reminder.content;
  card.append(head, content);
  if (compact) {
    const actions = document.createElement("div");
    actions.className = "reminder-actions";
    const done = document.createElement("button");
    done.textContent = "完成";
    done.onclick = () => updateReminder(reminder.reminder_id, "done");
    const snooze = document.createElement("button");
    snooze.textContent = "推迟 10 分钟";
    snooze.onclick = () => updateReminder(reminder.reminder_id, "snooze");
    actions.append(done, snooze);
    card.appendChild(actions);
  }
  return card;
}

function renderReminders() {
  const list = $("#reminder-list");
  const grid = $("#schedule-grid");
  list.replaceChildren();
  grid.replaceChildren();
  if (!state.reminders.length) {
    list.innerHTML = '<div class="empty">还没有提醒。试试对它说“提醒我明天 22:00 交作业”。</div>';
    grid.innerHTML = '<div class="empty">还没有提醒。</div>';
    $("#next-reminder").textContent = "还没有提醒";
    return;
  }
  state.reminders.forEach((reminder) => {
    list.appendChild(reminderCard(reminder));
    grid.appendChild(reminderCard(reminder, false));
  });
  $("#next-reminder").textContent = state.reminders[0].remind_at;
}

async function loadReminders() {
  const data = await api("/api/reminders?status=pending");
  state.reminders = data.reminders;
  renderReminders();
}

async function updateReminder(id, action) {
  await api(`/api/reminders/${id}`, {
    method: "PATCH",
    body: JSON.stringify({action, minutes: 10}),
  });
  $("#reminder-popup").classList.add("hidden");
  await loadReminders();
  showToast(action === "done" ? "已标记完成" : "已推迟 10 分钟");
}

async function loadStatus() {
  const data = await api("/api/status");
  $("#mode").textContent = data.mode === "offline" ? "离线模式" : "大模型模式";
  $("#agent-status").textContent = `${data.tools} 个工具在线`;
}

async function loadTools() {
  const data = await api("/api/tools");
  const names = {
    calculator: "四则运算",
    todo_add: "添加待办",
    todo_list: "查看待办",
    todo_done: "完成待办",
    file_write: "写文件",
    file_read: "读文件",
    file_list: "文件列表",
    weather: "天气查询",
    current_time: "当前时间",
    schedule_query: "课表查询",
  };
  const grid = $("#tool-grid");
  grid.replaceChildren();
  data.tools.forEach((item, index) => {
    const tool = item.function;
    const card = document.createElement("article");
    card.className = "tool-card";
    const number = document.createElement("span");
    number.textContent = `TOOL ${String(index + 1).padStart(2, "0")}`;
    const title = document.createElement("h3");
    title.textContent = names[tool.name] || tool.name;
    const description = document.createElement("p");
    description.textContent = tool.description;
    card.append(number, title, description);
    grid.appendChild(card);
  });
}

async function loadMemory() {
  const data = await api("/api/memory");
  const entries = Object.entries(data.facts);
  $("#memory-count").textContent = entries.length;
  const list = $("#memory-list");
  list.replaceChildren();
  if (!entries.length) {
    const empty = document.createElement("div");
    empty.className = "memory-item";
    empty.textContent = "还没有长期记忆。试试对她介绍自己。";
    list.appendChild(empty);
    return;
  }
  entries.forEach(([key, value]) => {
    const item = document.createElement("div");
    item.className = "memory-item";
    item.textContent = `${key}：${value}`;
    list.appendChild(item);
  });
}

async function loadDevices() {
  const data = await api("/api/devices");
  const list = $("#device-list");
  list.replaceChildren();
  data.devices.forEach((device) => {
    const card = document.createElement("div");
    card.className = `device ${device.online ? "online" : ""}`;
    const name = document.createElement("strong");
    name.textContent = `${device.name} · ${device.id}`;
    const state = document.createElement("span");
    state.textContent = device.online
      ? `在线${device.last_delivery ? ` · 最近送达：${device.last_delivery}` : ""}`
      : "离线 · 自动降级为桌面提醒";
    card.append(name, state);
    list.appendChild(card);
  });
}

function speak(text) {
  if (!("speechSynthesis" in window)) return;
  const utterance = new SpeechSynthesisUtterance(`报时鸟提醒你，${text}`);
  utterance.lang = "zh-CN";
  utterance.rate = 0.95;
  speechSynthesis.speak(utterance);
}

function showPopup(event) {
  state.popupReminderId = event.reminder_id;
  $("#popup-content").textContent = event.content;
  $("#reminder-popup").classList.remove("hidden");
  speak(event.content);
}

async function pollEvents() {
  try {
    const data = await api(`/api/events?after=${state.lastEventId}`);
    for (const event of data.events) {
      state.lastEventId = Math.max(state.lastEventId, event.id);
      showPopup(event);
      await loadReminders();
    }
  } catch (error) {
    $("#agent-status").textContent = "服务连接中断";
  }
}

function updateClock() {
  const now = new Date();
  $("#live-date").textContent = now.toLocaleDateString("zh-CN", {
    month: "long", day: "numeric", weekday: "long",
  });
  $("#live-time").textContent = now.toLocaleTimeString("zh-CN", {
    hour: "2-digit", minute: "2-digit",
  });
}

function setupVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    $("#voice-state").textContent = "当前浏览器不支持语音识别，请使用文字输入。";
    return;
  }
  state.recognition = new SpeechRecognition();
  state.recognition.lang = "zh-CN";
  state.recognition.interimResults = false;
  state.recognition.maxAlternatives = 1;
  state.recognition.onstart = () => {
    $("#mic").classList.add("listening");
    $("#voice-state").textContent = "正在听，请说一句话…";
  };
  state.recognition.onend = () => {
    $("#mic").classList.remove("listening");
  };
  state.recognition.onerror = () => {
    $("#voice-state").textContent = "语音识别失败，已保留文字输入。";
    $("#chat-input").focus();
  };
  state.recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    $("#voice-state").textContent = `识别到：${transcript}`;
    sendMessage(transcript);
  };
}

function openModal() {
  const now = new Date(Date.now() + 60 * 60 * 1000);
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
    .toISOString().slice(0, 16);
  $("#reminder-form").elements.remind_at.value = local;
  $("#reminder-modal").classList.remove("hidden");
}

function setupEvents() {
  $$(".nav").forEach((button) => {
    button.onclick = () => {
      $$(".nav").forEach((item) => item.classList.remove("active"));
      $$(".view").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      $(`#view-${button.dataset.view}`).classList.add("active");
      if (button.dataset.view === "memory") {
        loadMemory();
        loadDevices();
      }
    };
  });
  $$("[data-prompt]").forEach((button) => {
    button.onclick = () => sendMessage(button.dataset.prompt);
  });
  $("#chat-form").onsubmit = (event) => {
    event.preventDefault();
    const input = $("#chat-input");
    sendMessage(input.value);
    input.value = "";
  };
  $("#mic").onclick = () => {
    if (!state.recognition) {
      $("#voice-state").textContent = "当前浏览器不支持语音识别，请使用文字输入。";
      return;
    }
    state.recognition.start();
  };
  $("#open-modal").onclick = openModal;
  $("#open-modal-2").onclick = openModal;
  $("#close-modal").onclick = () => $("#reminder-modal").classList.add("hidden");
  $("#repeat-type").onchange = (event) => {
    $("#interval-field").classList.toggle("hidden", event.target.value !== "interval");
  };
  $("#reminder-form").onsubmit = async (event) => {
    event.preventDefault();
    const form = event.target;
    const data = Object.fromEntries(new FormData(form).entries());
    data.remind_at = data.remind_at.replace("T", " ");
    data.repeat_interval = Number(data.repeat_interval || 0);
    try {
      await api("/api/reminders", {
        method: "POST",
        body: JSON.stringify(data),
      });
      $("#reminder-modal").classList.add("hidden");
      form.reset();
      await loadReminders();
      showToast("提醒已保存");
    } catch (error) {
      showToast(error.message);
    }
  };
  $("#popup-done").onclick = () => updateReminder(state.popupReminderId, "done");
  $("#popup-snooze").onclick = () => updateReminder(state.popupReminderId, "snooze");
  $("#reset-memory").onclick = async () => {
    await api("/api/reset", {method: "POST", body: "{}"});
    await loadMemory();
    showToast("记忆已清空");
  };
}

async function init() {
  setupEvents();
  setupVoice();
  updateClock();
  setInterval(updateClock, 30000);
  await Promise.all([loadStatus(), loadReminders(), loadTools()]);
  setInterval(pollEvents, 1000);
}

init().catch((error) => showToast(`启动失败：${error.message}`));
