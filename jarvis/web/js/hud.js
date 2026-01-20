// HUD CONTROLLER
class HUD {
    constructor() {
        this.termBuffer = [];
        this.maxTermLines = 5;
        this.initClock();
        this.initSystemMonitor();
    }

    initClock() {
        const updateTime = () => {
            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', { hour12: false });
            const dateString = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

            document.getElementById('clock-time').innerText = timeString;
            document.getElementById('clock-date').innerText = dateString;
        };
        setInterval(updateTime, 1000);
        updateTime();
    }

    initSystemMonitor() {
        // Now handled via Python Bridge
    }

    updateSystemStats(stats) {
        if (!stats) return;
        this.updateBar('cpu-bar', stats.cpu);
        this.updateBar('ram-bar', stats.ram);

        // Update text labels if they existed, or add them dynamically
        // For now just bars are sufficient visual indicator
    }

    appendChat(speaker, text) {
        const history = document.getElementById('chat-history');
        if (!history) return;
        const msgDiv = document.createElement('div');
        msgDiv.className = speaker === 'user' ? 'msg-user' : 'msg-jarvis';
        const label = speaker === 'user' ? 'CMD' : 'SYS';
        msgDiv.innerHTML = `[${label}] ${text}`;
        history.appendChild(msgDiv);
        history.scrollTop = history.scrollHeight;
    }

    updateBar(elementId, percentage) {
        const bar = document.getElementById(elementId);
        if (bar) {
            bar.style.width = percentage + '%';
        }
    }

    setStatus(status) {
        const el = document.getElementById('status-text');
        if (el) {
            el.innerHTML = status.toUpperCase();
            if (status === 'listening') el.style.color = '#00ffaa';
            if (status === 'thinking') el.style.color = '#ffffff';
            if (status === 'speaking') el.style.color = '#00E5FF';
            if (status === 'idle') el.style.color = '#00E5FF';
        }
    }
}

// Global HUD instance
window.jarvisHUD = new HUD();

// Handle Input
function handleInput(event) {
    if (event.key === 'Enter') {
        const input = document.getElementById('command-input');
        const text = input.value;
        if (text && window.bridge) {
            // Send text back to Python? 
            // Currently gui_hologram doesn't have a slot for receiving text from JS
            // TODO: Add 'processCommand' slot in Python Bridge
            window.jarvisHUD.appendChat('user', text + " (Voice Input Recommended)");
            input.value = '';
        }
    }
}

// QWebChannel Integration
window.onload = function () {
    // Init Three.js Reactor
    initReactor();

    if (typeof QWebChannel !== 'undefined') {
        new QWebChannel(qt.webChannelTransport, function (channel) {
            window.bridge = channel.objects.bridge;

            // State Updates
            window.bridge.setState.connect(function (state) {
                window.jarvisHUD.setStatus(state);

                // Pass state to Reactor
                if (window.setReactorState) {
                    window.setReactorState(state);
                }
            });

            // Audio Data
            window.bridge.setAudioData.connect(function (audioData) {
                if (window.updateReactorAudio) {
                    window.updateReactorAudio(audioData);
                }
            });

            // Real System Stats
            window.bridge.systemStats.connect(function (stats) {
                window.jarvisHUD.updateSystemStats(stats);
            });

            // Chat Messages
            window.bridge.chatMessage.connect(function (speaker, text) {
                window.jarvisHUD.appendChat(speaker, text);
            });
        });
    } else {
        window.jarvisHUD.log("Running in generic browser mode", "WARN");
    }

    // Initial welcome message
    window.jarvisHUD.appendChat('jarvis', 'SYSTEMS ONLINE. READY.');
};
