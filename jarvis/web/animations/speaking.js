// Speaking Animation State
class SpeakingAnimation {
    constructor(mesh, particles) {
        this.mesh = mesh;
        this.particles = particles;
        this.isActive = false;
    }

    start() {
        this.isActive = true;
        console.log('Speaking animation started');
    }

    stop() {
        this.isActive = false;
    }

    update(delta, elapsed, audioData) {
        if (!this.isActive) return;

        // Use audio data if available, otherwise simulate
        let amplitude = 0.5;
        if (audioData && audioData.length > 0) {
            // Calculate average amplitude from FFT data
            amplitude = audioData.reduce((a, b) => a + b, 0) / audioData.length;
        } else {
            // Simulate speech rhythm
            amplitude = (Math.sin(elapsed * 8.0) + 1.0) / 2.0;
        }

        // Lower face vibration based on audio
        const positions = this.mesh.geometry.attributes.position.array;
        const originalPositions = this.mesh.geometry.userData.originalPositions;

        if (originalPositions) {
            for (let i = 0; i < positions.length; i += 3) {
                const y = originalPositions[i + 1];

                // Apply more deformation to lower part (mouth region)
                if (y < 0) {
                    const mouthFactor = Math.abs(y) / 20.0;
                    const vibrate = amplitude * mouthFactor * 2.0;

                    positions[i] = originalPositions[i] + (Math.random() - 0.5) * vibrate;
                    positions[i + 1] = originalPositions[i + 1] + (Math.random() - 0.5) * vibrate;
                    positions[i + 2] = originalPositions[i + 2] + vibrate;
                } else {
                    // Upper part (eyes) just brighten slightly
                    positions[i] = originalPositions[i];
                    positions[i + 1] = originalPositions[i + 1];
                    positions[i + 2] = originalPositions[i + 2];
                }
            }
            this.mesh.geometry.attributes.position.needsUpdate = true;
        }

        // Pulse based on speech
        const scale = 1.0 + amplitude * 0.05;
        this.mesh.scale.set(scale, scale, scale);

        // Particle brightness sync
        this.particles.material.opacity = 0.7 + amplitude * 0.3;
        this.particles.material.size = 0.3 + amplitude * 0.2;
    }
}
