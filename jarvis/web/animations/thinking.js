// Thinking Animation State
class ThinkingAnimation {
    constructor(mesh, particles) {
        this.mesh = mesh;
        this.particles = particles;
        this.isActive = false;
    }

    start() {
        this.isActive = true;
        console.log('Thinking animation started');
    }

    stop() {
        this.isActive = false;
    }

    update(delta, elapsed, audioData) {
        if (!this.isActive) return;

        // Rotate mesh sections
        this.mesh.rotation.y += delta * 0.5;
        this.mesh.rotation.z = Math.sin(elapsed * 2.0) * 0.1;

        // Glow intensity cycle
        const glowCycle = (Math.sin(elapsed * 2.0) + 1.0) / 2.0;
        this.mesh.material.opacity = 0.6 + glowCycle * 0.4;

        // Vertex deformation with data flow effect
        const positions = this.mesh.geometry.attributes.position.array;
        const originalPositions = this.mesh.geometry.userData.originalPositions;

        if (originalPositions) {
            for (let i = 0; i < positions.length; i += 3) {
                const wave = Math.sin(elapsed * 3.0 + i * 0.05) * 0.3;
                const flow = Math.cos(elapsed * 2.0 + i * 0.1) * 0.2;

                positions[i] = originalPositions[i] + wave;
                positions[i + 1] = originalPositions[i + 1] + flow;
                positions[i + 2] = originalPositions[i + 2] + wave * 0.5;
            }
            this.mesh.geometry.attributes.position.needsUpdate = true;
        }

        // Particle flow
        this.particles.rotation.y -= delta * 0.3;
        this.particles.material.size = 0.3 + Math.sin(elapsed * 3.0) * 0.1;
    }
}
