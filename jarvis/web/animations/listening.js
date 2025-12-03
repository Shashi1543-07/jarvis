// Listening Animation State
class ListeningAnimation {
    constructor(mesh, particles) {
        this.mesh = mesh;
        this.particles = particles;
        this.isActive = false;
        this.rippleTime = 0;
    }

    start() {
        this.isActive = true;
        this.rippleTime = 0;
        console.log('Listening animation started');

        // Brighten mesh
        gsap.to(this.mesh.material, {
            opacity: 1.0,
            duration: 0.5
        });

        gsap.to(this.particles.material, {
            opacity: 1.0,
            duration: 0.5
        });
    }

    stop() {
        this.isActive = false;
    }

    update(delta, elapsed, audioData) {
        if (!this.isActive) return;

        // Expand ripple effect
        this.rippleTime += delta;
        const ripple = Math.sin(this.rippleTime * 3.0) * 0.5;

        const positions = this.mesh.geometry.attributes.position.array;
        const originalPositions = this.mesh.geometry.userData.originalPositions;

        if (originalPositions) {
            for (let i = 0; i < positions.length; i += 3) {
                const x = originalPositions[i];
                const y = originalPositions[i + 1];
                const distance = Math.sqrt(x * x + y * y);
                const wave = Math.sin(distance * 0.2 - this.rippleTime * 5.0) * ripple;

                positions[i] = originalPositions[i] + x * wave * 0.05;
                positions[i + 1] = originalPositions[i + 1] + y * wave * 0.05;
                positions[i + 2] = originalPositions[i + 2] + wave * 0.1;
            }
            this.mesh.geometry.attributes.position.needsUpdate = true;
        }

        // Tilt toward center
        this.mesh.rotation.x = Math.sin(elapsed) * 0.02;
        this.mesh.rotation.y = Math.cos(elapsed) * 0.02;
    }
}
