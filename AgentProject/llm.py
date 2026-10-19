"""OpenAI 兼容的 Chat Completions 客户端(只用标准库)。

用环境变量配置, 不把密钥写进代码:

* ``AGENT_API_KEY`` 或 ``OPENAI_API_KEY`` —— 密钥(必需)
* ``AGENT_BASE_URL`` —— 默认 ``https://api.openai.com/v1``;
  用阿里云百炼可以设成 ``https://dashscope.aliyuncs.com/compatible-mode/v1``
* ``AGENT_MODEL`` —— 默认 ``gpt-4o-mini``

只要服务端兼容 OpenAI 的 ``/chat/completions`` 和 function calling 就能用。
"""

import json
import os
import urllib.error
import urllib.request


class LLMError(Exception):
    """调用大模型失败。"""


def settings():
    """返回 (api_key, base_url, model)。"""
    key = os.environ.get("AGENT_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    base = (os.environ.get("AGENT_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("AGENT_MODEL") or "gpt-4o-mini"
    return key, base, model


def is_configured():
    """有没有配好密钥, 没配就走离线规则模式。"""
    return bool(settings()[0])


def chat(messages, tools=None, temperature=0.2, timeout=60):
    """调用一次 chat completions, 返回助手消息(可能带 tool_calls)。"""
    key, base, model = settings()
    if not key:
        raise LLMError("没有配置 API Key(设置 AGENT_API_KEY 或 OPENAI_API_KEY)")

    payload = {"model": model, "messages": messages, "temperature": temperature}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    request = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise LLMError("模型接口返回 {}: {}".format(exc.code, detail))
    except OSError as exc:
        raise LLMError("请求大模型失败: {}".format(exc))

    try:
        return data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        raise LLMError("模型接口返回的数据格式不对")
