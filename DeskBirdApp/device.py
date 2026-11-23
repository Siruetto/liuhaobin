"""设备网关: 为 ESP32 接入保留接口, 当前提供可运行的模拟设备。"""

import datetime
import threading


class DeviceHub:
    def __init__(self):
        self._lock = threading.Lock()
        self._devices = [
            {
                "id": "ESP32-A1",
                "name": "书桌音箱",
                "online": True,
                "last_seen": None,
                "last_delivery": None,
            },
            {
                "id": "ESP32-A2",
                "name": "宿舍音箱",
                "online": False,
                "last_seen": None,
                "last_delivery": None,
            },
        ]

    def list_devices(self):
        with self._lock:
            return [dict(device) for device in self._devices]

    def dispatch(self, content):
        """向在线设备发送提醒；离线设备降级为桌面提醒。"""
        sent = []
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            for device in self._devices:
                if device["online"]:
                    device["last_delivery"] = content
                    device["last_seen"] = now
                    sent.append(device["id"])
            offline_count = sum(1 for device in self._devices if not device["online"])
        return {"sent_to": sent, "offline_count": offline_count}
