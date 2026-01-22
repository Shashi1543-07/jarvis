// IRON MAN JARVIS HUD CONTROLLER
class HUD {
    constructor() {
        this.termBuffer = [];
        this.maxTermLines = 5;
        this.initDateTimeDisplay();
        this.initSystemMonitor();
        this.hideInitializationText();
    }

    initDateTimeDisplay() {
        const updateDateTime = () => {
            const now = new Date();

            // Time
            const timeString = now.toLocaleTimeString('en-US', { hour12: false });
            document.getElementById('time-display').textContent = timeString;

            // Date
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            const dateString = now.toLocaleDateString('en-US', options);
            document.getElementById('date-display').textContent = dateString;

            // Day of year and year
            const start = new Date(now.getFullYear(), 0, 0);
            const diff = now - start;
            const oneDay = 1000 * 60 * 60 * 24;
            const dayOfYear = Math.floor(diff / oneDay);
            document.getElementById('day-year-display').textContent = `DAY ${dayOfYear.toString().padStart(3, '0')} | YEAR ${now.getFullYear()}`;
        };

        setInterval(updateDateTime, 1000);
        updateDateTime(); // Initial call
    }

    hideInitializationText() {
        setTimeout(() => {
            const initText = document.getElementById('initialization-text');
            if (initText) {
                initText.classList.remove('active');
            }
        }, 5000); // Hide after 5 seconds
    }

    initSystemMonitor() {
        // Now handled via Python Bridge
    }

    updateSystemStats(stats) {
        if (!stats) return;

        // Update CPU
        if (stats.cpu !== undefined) {
            this.updateBar('cpu-bar', stats.cpu);
            this.updateValue('cpu-value', `${stats.cpu}%`);
        }

        // Update RAM
        if (stats.ram !== undefined) {
            this.updateBar('ram-bar', stats.ram);
            this.updateValue('ram-value', `${stats.ram}%`);
        }

        // Update GPU (if available)
        if (stats.gpu !== undefined) {
            this.updateBar('gpu-bar', stats.gpu);
            this.updateValue('gpu-value', `${stats.gpu}%`);
        }

        // Update Network Status
        if (stats.network !== undefined) {
            document.getElementById('network-status').textContent = stats.network;
        }

        // Update Internet Speed (if available)
        if (stats.internetSpeed !== undefined) {
            document.getElementById('internet-speed').textContent = `${stats.internetSpeed} Mbps`;
        }

        // Update Battery (if available)
        if (stats.battery !== undefined) {
            this.updateBar('battery-bar', stats.battery);
            this.updateValue('battery-value', `${stats.battery}%`);
        }

        // Update Temperature (if available)
        if (stats.temperature !== undefined) {
            this.updateValue('temperature-value', `${stats.temperature}°C`);
        }

        // Update Core Temperature (if available)
        if (stats.coreTemp !== undefined) {
            this.updateValue('core-temp-value', `${stats.coreTemp}°C`);
        }
    }

    appendChat(speaker, text) {
        const history = document.getElementById('chat-history');
        if (!history) return;
        const msgDiv = document.createElement('div');
        msgDiv.className = speaker === 'user' ? 'msg-user' : 'msg-jarvis';
        const label = speaker === 'user' ? 'USER' : 'JARVIS';
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

    updateValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
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
            if (status === 'warning') el.style.color = '#FFA500';
            if (status === 'critical') el.style.color = '#FF0000';
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
            window.jarvisHUD.appendChat('user', text);
            input.value = '';
        } else if (text) {
            // Fallback for standalone browser mode
            window.jarvisHUD.appendChat('user', text);
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
        // Standalone browser mode - simulate some data
        console.log("Running in standalone browser mode");

        // Simulate initial system stats
        setTimeout(() => {
            window.jarvisHUD.updateSystemStats({
                cpu: 45,
                ram: 62,
                gpu: 38,
                network: 'ONLINE',
                internetSpeed: '125.4',
                battery: 87,
                temperature: 42,
                coreTemp: 48
            });
        }, 1000);

        // Simulate periodic updates
        setInterval(() => {
            const cpu = 30 + Math.floor(Math.random() * 40);
            const ram = 40 + Math.floor(Math.random() * 30);
            const gpu = 20 + Math.floor(Math.random() * 50);

            window.jarvisHUD.updateSystemStats({
                cpu: cpu,
                ram: ram,
                gpu: gpu,
                network: 'ONLINE',
                internetSpeed: (100 + Math.random() * 50).toFixed(1),
                battery: Math.max(20, 100 - Math.floor(Date.now() / 100000)),
                temperature: 38 + Math.floor(Math.random() * 10),
                coreTemp: 42 + Math.floor(Math.random() * 10)
            });
        }, 5000);
    }

    // Initial welcome message
    window.jarvisHUD.appendChat('jarvis', 'J.A.R.V.I.S. ARMOR SUITE ONLINE. ALL SYSTEMS NOMINAL.');
};
