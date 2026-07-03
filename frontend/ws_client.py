

import threading
import websocket
import json
import time
import os
from typing import Dict, Any, Optional

WS_URL = os.getenv("WS_URL", "ws://127.0.0.1:8000/ws/live")


class WSClient:
    

    _thread: Optional[threading.Thread] = None
    _running: bool = False
    latest_data: Dict[str, Any] = {}
    _lock = threading.Lock()

    @classmethod
    def start(cls):
        
        with cls._lock:
            if cls._running:
                return
            cls._running = True
            cls._thread = threading.Thread(target=cls._run_listener, daemon=True)
            cls._thread.start()

    @classmethod
    def stop(cls):
        
        with cls._lock:
            cls._running = False
            cls._thread = None

    @classmethod
    def _run_listener(cls):
        
        while cls._running:
            try:
                ws = websocket.WebSocket()
                ws.connect(WS_URL)
                
                while cls._running:
                    msg = ws.recv()
                    if msg:
                        data = json.loads(msg)
                        with cls._lock:
                            cls.latest_data = data
                    time.sleep(0.1)
                
                ws.close()
            except Exception:
                
                time.sleep(2.0)

    @classmethod
    def get_latest_data(cls) -> Dict[str, Any]:
        
        with cls._lock:
            return cls.latest_data.copy()
