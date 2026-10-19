"""一个极简的网页界面(只用标准库 http.server)。

启动::

    python web_ui.py                 # 默认 8000 端口
    python web_ui.py --port 9000 --offline

然后浏览器打开 http://127.0.0.1:8000 。
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from agent_core import Agent
from tools import LocalToolBox

PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>办公小助手</title>
<style>
  body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background:#f5f6f8; margin:0; }
  .wrap { max-width: 720px; margin: 40px auto; background:#fff; border-radius:12px;
          box-shadow:0 4px 20px rgba(0,0,0,.08); overflow:hidden; }
  header { padding:16px 20px; background:#1f2937; color:#fff; }
  header small { opacity:.7; margin-left:8px; }
  #log { height:420px; overflow-y:auto; padding:16px 20px; }
  .msg { margin:10px 0; display:flex; }
  .msg.user { justify-content:flex-end; }
  .bubble { max-width:75%; padding:10px 14px; border-radius:12px; white-space:pre-wrap; line-height:1.5; }
  .user .bubble { background:#2563eb; color:#fff; }
  .bot .bubble { background:#eef1f5; color:#111; }
  .actions { font-size:12px; color:#6b7280; margin-top:6px; }
  footer { display:flex; gap:8px; padding:12px 20px; border-top:1px solid #eee; }
  input { flex:1; padding:10px 12px; border:1px solid #ddd; border-radius:8px; font-size:14px; }
  button { padding:10px 18px; border:0; border-radius:8px; background:#2563eb; color:#fff; cursor:pointer; }
</style>
</head>
<body>
<div class="wrap">
  <header><strong>办公小助手</strong><small id="mode"></small></header>
  <div id="log"></div>
  <footer>
    <input id="text" placeholder="试试：帮我算一下 (3+5)*2" autocomplete="off">
    <button id="send">发送</button>
  </footer>
</div>
<script>
var log = document.getElementById('log');
function add(role, text, actions) {
  var wrap = document.createElement('div');
  wrap.className = 'msg ' + role;
  var bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  if (actions && actions.length) {
    var info = document.createElement('div');
    info.className = 'actions';
    info.textContent = '工具: ' + actions.map(function (a) {
      return a.tool + (a.ok ? ' ✓' : ' ✗');
    }).join(', ');
    bubble.appendChild(info);
  }
  wrap.appendChild(bubble);
  log.appendChild(wrap);
  log.scrollTop = log.scrollHeight;
}
function send() {
  var input = document.getElementById('text');
  var text = input.value.trim();
  if (!text) { return; }
  add('user', text);
  input.value = '';
  fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: text})
  }).then(function (r) { return r.json(); }).then(function (data) {
    add('bot', data.reply, data.actions);
  }).catch(function (e) { add('bot', '出错了: ' + e); });
}
document.getElementById('send').onclick = send;
document.getElementById('text').addEventListener('keydown', function (e) {
  if (e.key === 'Enter') { send(); }
});
fetch('/api/status').then(function (r) { return r.json(); }).then(function (d) {
  document.getElementById('mode').textContent = '模式: ' + d.mode;
});
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    agent = None

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", PAGE.encode("utf-8"))
        elif self.path == "/api/status":
            self._json({"mode": self.agent.mode})
        else:
            self._send(404, "text/plain; charset=utf-8", b"not found")

    def do_POST(self):
        if self.path != "/api/chat":
            self._send(404, "text/plain; charset=utf-8", b"not found")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            message = str(body.get("message") or "").strip()
        except (ValueError, UnicodeDecodeError):
            self._json({"reply": "请求格式不对", "actions": []}, status=400)
            return
        if not message:
            self._json({"reply": "说点什么吧", "actions": []}, status=400)
            return
        reply = self.agent.chat(message)
        self._json({"reply": reply["text"], "actions": reply["actions"]})

    def log_message(self, *args):
        pass  # 不想把每个请求都打到控制台

    def _json(self, payload, status=200):
        self._send(status, "application/json; charset=utf-8",
                   json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _send(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main(argv=None):
    parser = argparse.ArgumentParser(description="办公小助手的网页界面")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--offline", action="store_true", help="强制离线规则模式")
    parser.add_argument("--mcp", action="store_true", help="工具通过 MCP 子进程调用")
    args = parser.parse_args(argv)

    toolbox = LocalToolBox()
    if args.mcp:
        from mcp_client import MCPToolBox

        toolbox = MCPToolBox()
    Handler.agent = Agent(toolbox=toolbox, offline=True if args.offline else None)
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print("服务已启动: http://127.0.0.1:{}/  (模式: {})".format(
        args.port, Handler.agent.mode))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
