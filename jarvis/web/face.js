// Main face rendering and animation controller
let scene, camera, renderer, faceMesh, particles, rings;
let clock = new THREE.Clock();
let currentState = 'idle';
let audioData = [];

// Color palette
const COLORS = {
    idle: 0x00E5FF,
    listening: 0x00FFF6,
    thinking: 0x4DA6FF,
    speaking: 0x00E5FF,
    speakingAccent: 0xFFDA6F,
    alert: 0xFF4655
};

function initFace() {
    // Scene setup
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.002);
    
    // Camera
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 50;
    
    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    document.getElementById('canvas-container').appendChild(renderer.domElement);
    
    // Lights
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);
    
    const pointLight = new THREE.PointLight(0x00E5FF, 1, 100);
    pointLight.position.set(0, 0, 30);
    scene.add(pointLight);
    
    // Create face mesh
    createFaceMesh();
    
    // Create background elements
    createParticleNebula();
    createHologramRings();
    
    // Create animation controller
    window.faceController = new FaceController(faceMesh);
    
    // Handle window resize
    window.addEventListener('resize', onWindowResize, false);
    
    // Start animation loop
    animate();
}

function createFaceMesh() {
    // Generate face geometry
    const geometry = generateFaceGeometry();
    
    // Create wireframe material
    const material = new THREE.MeshBasicMaterial({
        color: COLORS.idle,
        wireframe: true,
        transparent: true,
        opacity: 0.8
    });
    
    faceMesh = new THREE.Mesh(geometry, material);
    scene.add(faceMesh);
    
    // Add vertex particles
    createVertexParticles(geometry);
}

function generateFaceGeometry() {
    const vertices = [];
    const indices = [];
    
    // Create oval face shape
    const segmentsH = 20;
    const segmentsV = 30;
    const radiusH = 15;
    const radiusV = 20;
    
    for (let i = 0; i <= segmentsV; i++) {
        const v = i / segmentsV;
        const theta = v * Math.PI;
        
        for (let j = 0; j <= segmentsH; j++) {
            const u = j / segmentsH;
            const phi = u * Math.PI * 2;
            
            const x = radiusH * Math.sin(theta) * Math.cos(phi);
            const y = radiusV * Math.cos(theta);
            const z = radiusH * Math.sin(theta) * Math.sin(phi) * 0.3;
            
            // Add slight randomness for organic feel
            const noise = (Math.random() - 0.5) * 0.5;
            vertices.push(x + noise, y + noise, z + noise);
        }
    }
    
    // Create triangles
    for (let i = 0; i < segmentsV; i++) {
        for (let j = 0; j < segmentsH; j++) {
            const a = i * (segmentsH + 1) + j;
            const b = a + segmentsH + 1;
            const c = a + 1;
            const d = b + 1;
            
            indices.push(a, b, c);
            indices.push(b, d, c);
        }
    }
    
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    
    return geometry;
}

function createVertexParticles(geometry) {
    const positions = geometry.attributes.position.array;
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    
    const particleMaterial = new THREE.PointsMaterial({
        color: COLORS.idle,
        size: 0.3,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });
    
    particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);
}

function createParticleNebula() {
    const particleCount = 1000;
    const positions = new Float32Array(particleCount * 3);
    
    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 100;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 100;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 50 - 20;
    }
    
    const nebulaGeometry = new THREE.BufferGeometry();
    nebulaGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const nebulaMaterial = new THREE.PointsMaterial({
        color: 0x00E5FF,
        size: 0.1,
        transparent: true,
        opacity: 0.3,
        blending: THREE.AdditiveBlending
    });
    
    const nebula = new THREE.Points(nebulaGeometry, nebulaMaterial);
    scene.add(nebula);
}

function createHologramRings() {
    rings = new THREE.Group();
    
    for (let i = 0; i < 3; i++) {
        const radius = 25 + i * 5;
        const geometry = new THREE.RingGeometry(radius, radius + 0.1, 64);
        const material = new THREE.MeshBasicMaterial({
            color: COLORS.idle,
            transparent: true,
            opacity: 0.2 - i * 0.05,
            side: THREE.DoubleSide
        });
        
        const ring = new THREE.Mesh(geometry, material);
        ring.rotation.x = Math.PI / 2;
        ring.userData.speed = (i + 1) * 0.1;
        rings.add(ring);
    }
    
    scene.add(rings);
}

function animate() {
    requestAnimationFrame(animate);
    
    const delta = clock.getDelta();
    const elapsed = clock.getElapsedTime();
    
    // Update face controller
    if (window.faceController) {
        window.faceController.update(delta, elapsed, audioData);
    }
    
    // Rotate rings
    if (rings) {
        rings.children.forEach(ring => {
            ring.rotation.z += ring.userData.speed * delta;
        });
    }
    
    renderer.render(scene, camera);
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

// Face Animation Controller
class FaceController {
    constructor(mesh) {
        this.mesh = mesh;
        this.particles = particles;
        this.state = 'idle';
        this.animations = {
            idle: new IdleAnimation(mesh, particles),
            listening: new ListeningAnimation(mesh, particles),
            thinking: new ThinkingAnimation(mesh, particles),
            speaking: new SpeakingAnimation(mesh, particles)
        };
        
        this.animations[this.state].start();
    }
    
    setState(newState) {
        if (this.state !== newState) {
            this.animations[this.state].stop();
            this.state = newState;
            this.animations[newState].start();
            
            // Update colors
            const color = COLORS[newState] || COLORS.idle;
            gsap.to(this.mesh.material.color, {
                r: ((color >> 16) & 255) / 255,
                g: ((color >> 8) & 255) / 255,
                b: (color & 255) / 255,
                duration: 0.5
            });
            
            gsap.to(this.particles.material.color, {
                r: ((color >> 16) & 255) / 255,
                g: ((color >> 8) & 255) / 255,
                b: (color & 255) / 255,
                duration: 0.5
            });
        }
    }
    
    setAudioData(data) {
        audioData = data;
    }
    
    update(delta, elapsed, audioData) {
        if (this.animations[this.state]) {
            this.animations[this.state].update(delta, elapsed, audioData);
        }
    }
}
