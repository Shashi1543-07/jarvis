// Idle Animation State
class IdleAnimation {
    constructor(mesh, particles) {
        this.mesh = mesh;
        this.particles = particles;
        this.isActive = false;
    }

    start() {
        this.isActive = true;
        console.log('Idle animation started');
    }

    stop() {
        this.isActive = false;
    }

    update(delta, elapsed, audioData) {
        if (!this.isActive) return;

        // Gentle breathing effect
        const breathe = Math.sin(elapsed * 0.5) * 0.02 + 1.0;
        this.mesh.scale.y = breathe;

        // Slow rotation
        this.mesh.rotation.y = Math.sin(elapsed * 0.1) * 0.05;

        // Vertex pulse
        const positions = this.mesh.geometry.attributes.position.array;
        const originalPositions = this.mesh.geometry.userData.originalPositions;

        if (!originalPositions) {
            this.mesh.geometry.userData.originalPositions = Float32Array.from(positions);
        } else {
            for (let i = 0; i < positions.length; i += 3) {
                const pulse = Math.sin(elapsed * 2.0 + i * 0.1) * 0.1;
                positions[i] = originalPositions[i] + pulse;
                positions[i + 1] = originalPositions[i + 1] + pulse;
                positions[i + 2] = originalPositions[i + 2] + pulse;
            }
            this.mesh.geometry.attributes.position.needsUpdate = true;
        }

        // Particle glow pulse
        this.particles.material.opacity = 0.6 + Math.sin(elapsed * 2.0) * 0.2;
    }
}
