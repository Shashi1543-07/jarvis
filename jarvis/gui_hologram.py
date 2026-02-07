import sys
import os
import threading
import time
import psutil
import subprocess
import platform
import asyncio
import site
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtCore import QUrl, Qt, pyqtSlot, QMetaObject, Q_ARG, QObject, pyqtSignal, QThread

# Try to import websockets, assuming it was just installed
try:
    import websockets
except ImportError:
    print("CRITICAL: websockets library not found. Please run 'pip install websockets'")
    sys.exit(1)

# WebSocket Server running in a separate thread
class WSServer(QThread):
    # Signals to communicate back to the Main GUI thread
    on_command_received = pyqtSignal(str)
    
    def __init__(self, port=8765):
        super().__init__()
        self.port = port
        self.loop = None
        self.server = None
        self.clients = set()
        self.running = True

    def run(self):
        print(f"WSServer: Starting asyncio loop on port {self.port}")
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Async entry point to ensure loop is running when serve is called
        async def main_server():
            print("WSServer: Loop running, starting server...")
            async with websockets.serve(self.handler, "localhost", self.port):
                print("WSServer: Server serving forever")
                # Create a future strictly for keeping the loop running
                self._stop_future = asyncio.Future()
                await self._stop_future

        try:
            self.loop.run_until_complete(main_server())
        except asyncio.CancelledError:
            # Normal shutdown - don't print error
            pass
        except Exception as e:
            # Only log unexpected errors
            if "CancelledError" not in str(e):
                print(f"WSServer Loop Message: {e}")
        finally:
            # Cleanup any remaining tasks
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except:
                pass
            self.loop.close()
            print("WSServer: Loop closed")

    async def _async_shutdown(self):
        """Cleanup logic inside the loop"""
        print("WSServer: Closing all client connections...")
        if self.clients:
            close_tasks = [client.close() for client in list(self.clients)]
            await asyncio.gather(*close_tasks, return_exceptions=True)
            self.clients.clear()
        
        # Cancel all pending tasks except the current one
        pending = [t for t in asyncio.all_tasks(self.loop) if t is not asyncio.current_task(self.loop)]
        for task in pending:
            task.cancel()
        
        if pending:
            # Wait for tasks to be cancelled
            await asyncio.gather(*pending, return_exceptions=True)
            
        print("WSServer: Async shutdown complete.")

    def stop(self):
        self.running = False
        if self.loop and self.loop.is_running():
            # Schedule the async shutdown inside the loop
            self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self._shutdown_and_stop()))
        self.wait()

    async def _shutdown_and_stop(self):
        await self._async_shutdown()
        if hasattr(self, '_stop_future') and not self._stop_future.done():
            self._stop_future.set_result(True)
        self.loop.stop()


    async def handler(self, websocket):
        print("WSServer: New Client Connected")
        self.clients.add(websocket)
        try:
            async for message in websocket:
                # Handle incoming messages from JS
                data = json.loads(message)
                if data.get('type') == 'command':
                    cmd = data.get('content', '')
                    print(f"WSServer: Command received: {cmd}")
                    # Emit signal to main thread
                    self.on_command_received.emit(cmd)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            print("WSServer: Client Disconnected")
            self.clients.remove(websocket)

    def broadcast(self, message_dict):
        """Thread-safe broadcast method"""
        if self.loop and self.loop.is_running() and self.running:
            try:
                asyncio.run_coroutine_threadsafe(self._broadcast_async(message_dict), self.loop)
            except RuntimeError:
                # Loop might be closed during the check
                pass

    async def _broadcast_async(self, message_dict):
        if not self.clients:
            return
        
        message = json.dumps(message_dict)
        # Create list of tasks to send message to all clients
        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True
        )

    # Removed duplicate stop method

class SystemMonitorThread(QThread):
    # Emits stats directly to the WSServer
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def get_gpu_usage(self):
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return int(result.stdout.strip())
        except Exception:
            pass
        return 0

    def run(self):
        print("SystemMonitor: Started")
        while not self.stop_event.is_set():
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                gpu = self.get_gpu_usage()
                
                stats = {
                    "type": "stats",
                    "data": {
                        "cpu": cpu,
                        "ram": ram,
                        "gpu": gpu,
                        "network": "ONLINE" if psutil.net_if_stats() else "OFFLINE",
                        "internetSpeed": 100.0 # Sim
                    }
                }
                self.server.broadcast(stats)
                if self.stop_event.wait(1):
                    break
            except Exception as e:
                print(f"System Monitor Error: {e}")
                if self.stop_event.wait(5):
                    break

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        # Filter out some common spam if needed, but keeping logs for now
        print(f"js: {message} (line {line_number})")

class JarvisGUI(QMainWindow):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine

        # Window setup
        self.setWindowTitle("Jarvis AI - Iron Man Armor Suite")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: black;")

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. Start WebSocket Server
        self.ws_server = WSServer(port=8765)
        self.ws_server.start()
        
        # Connect command handling
        self.ws_server.on_command_received.connect(self.handle_gui_command)

        # 2. Hologram Area (WebEngine)
        self.web_view = QWebEngineView()
        self.custom_page = CustomWebEnginePage(self.web_view)
        self.web_view.setPage(self.custom_page)
        
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        
        # Remove QWebChannel references
        
        # Point to the NEW HUD index.html
        html_path = os.path.abspath("ui/jarvis-hud/index.html")
        url = QUrl.fromLocalFile(html_path)
        print(f"GUI: Loading HTML: {url.toString()}")
        self.web_view.setUrl(url)
        
        layout.addWidget(self.web_view)

        # 3. Start System Monitor
        self.monitor_thread = SystemMonitorThread(self.ws_server)
        self.monitor_thread.start()

        # 4. Engine Callbacks
        if self.engine:
            for state in self.engine.state_machine._valid_transitions.keys():
                self.engine.state_machine.register_callback(state, self.handle_state_transition)
            self.engine.on_text_update = self.update_text_from_engine
            self.engine.on_audio_level = self.update_audio_level_from_engine
            self.engine.on_latency_update = self.update_latency_from_engine
            self.engine.on_intent_detected = self.update_intent_from_engine
            print("GUI: Engine callbacks registered")

        self.current_state = "IDLE"

    # --- Engine Integration Methods ---

    def handle_state_transition(self, old_state, new_state):
        self.ws_server.broadcast({
            "type": "state",
            "data": new_state.value.lower()
        })

    def update_text_from_engine(self, speaker, text):
        self.ws_server.broadcast({
            "type": "chat",
            "sender": speaker.upper(),
            "message": text
        })

    def update_audio_level_from_engine(self, level):
        # Level is 0.0 to ~1.0+ (RMS)
        self.ws_server.broadcast({
            "type": "audio",
            "data": level
        })

    def update_latency_from_engine(self, latency_ms):
        self.ws_server.broadcast({
            "type": "latency",
            "data": latency_ms
        })

    def update_intent_from_engine(self, intent_name, confidence):
        self.ws_server.broadcast({
            "type": "intent",
            "intent": intent_name,
            "confidence": confidence
        })
        
    def handle_gui_command(self, cmd):
        """Handle text command from UI"""
        print(f"GUI: Executing command: {cmd}")
        # Here we could pass it to the engine as text input if implemented
        # For now, just log it
        
    def closeEvent(self, event):
        print("GUI: Closing...")
        self.ws_server.stop()
        self.monitor_thread.stop()
        self.monitor_thread.wait()
        event.accept()
