// ADVANCED ARC REACTOR CONTROLLER WITH GSAP ANIMATION
let currentReactorState = 'idle';
let reactorAudioLevel = 0;
let rotationAnimation;

function initReactor() {
    console.log("Initializing Arc Reactor with GSAP...");
    const container = document.getElementById('arc-reactor-container');

    if (!container) {
        console.error("Arc Reactor container not found!");
        return;
    }

    // Initialize GSAP rotation animation
    const reactorImage = document.getElementById('arc-reactor-image');
    if (reactorImage) {
        // Create continuous rotation animation
        rotationAnimation = gsap.to(reactorImage, {
            rotation: 360,
            duration: 20, // Full rotation every 20 seconds in idle state
            repeat: -1,   // Infinite repeat
            ease: "none", // Linear rotation
            transformOrigin: "50% 50%", // Explicitly set to center
            paused: false
        });
    }

    // Set initial state
    setReactorState('idle');
}

window.setReactorState = function (state) {
    currentReactorState = state;
    const container = document.getElementById('arc-reactor-container');
    if (!container) return;

    // Remove all state classes
    container.classList.remove('idle', 'listening', 'thinking', 'speaking', 'warning', 'critical');

    // Add current state class
    container.classList.add(state);

    // Update rotation speed based on state
    updateRotationSpeed(state);
};

window.updateReactorAudio = function (data) {
    if (data && data.length > 0) {
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
            sum += Math.abs(data[i]);
        }
        reactorAudioLevel = sum / data.length;

        // Dynamic reaction to audio
        if (currentReactorState === 'speaking') {
            const scale = 1 + (reactorAudioLevel * 0.3);
            const reactorImage = document.getElementById('arc-reactor-image');
            if (reactorImage) {
                gsap.to(reactorImage, {
                    scale: scale,
                    duration: 0.1,
                    ease: "power2.out"
                });
            }
        }
    } else {
        reactorAudioLevel = 0;
        // Reset scale when not speaking
        const reactorImage = document.getElementById('arc-reactor-image');
        if (reactorImage) {
            gsap.to(reactorImage, {
                scale: 1,
                duration: 0.3,
                ease: "power2.out"
            });
        }
    }
};

function updateRotationSpeed(state) {
    if (!rotationAnimation) return;

    let duration;
    switch (state) {
        case 'listening':
            duration = 8; // Faster rotation when listening
            break;
        case 'thinking':
            duration = 4; // Even faster when thinking
            break;
        case 'speaking':
            duration = 6; // Moderate speed when speaking
            break;
        case 'warning':
        case 'critical':
            duration = 1; // Very fast when warning/critical
            break;
        default: // idle
            duration = 20; // Slow rotation when idle
    }

    // Update the animation duration to change rotation speed
    rotationAnimation.duration(duration);
}

// Observe for DOM readiness if not handled by hud.js
if (document.readyState === 'complete') {
    initReactor();
} else {
    window.addEventListener('load', initReactor);
}
