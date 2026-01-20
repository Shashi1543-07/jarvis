// ARC REACTOR VISUALIZATION (TEXTURE BASED)
let scene, camera, renderer;
let reactorGroup, coreMesh, rotatingRing, glowSprite;
let audioLevel = 0;
let currentState = 'IDLE';

function initReactor() {
    const container = document.getElementById('arc-reactor-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // SCENE
    scene = new THREE.Scene();

    // CAMERA
    camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.z = 20;

    // RENDERER
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // ARC REACTOR GROUP
    reactorGroup = new THREE.Group();
    scene.add(reactorGroup);

    const textureLoader = new THREE.TextureLoader();
    const reactorTexture = textureLoader.load('assets/glow.png');

    // 1. STATIC CORE (Base Image)
    const geometry = new THREE.PlaneGeometry(12, 12);
    const material = new THREE.MeshBasicMaterial({
        map: reactorTexture,
        transparent: true,
        opacity: 0.9,
        color: 0x00E5FF,
        blending: THREE.AdditiveBlending, // Makes black transparent
        depthWrite: false,
        side: THREE.DoubleSide
    });
    coreMesh = new THREE.Mesh(geometry, material);
    reactorGroup.add(coreMesh);

    // 2. ROTATING RING (Duplicate for layering effect)
    const ringMat = new THREE.MeshBasicMaterial({
        map: reactorTexture,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.DoubleSide
    });
    rotatingRing = new THREE.Mesh(geometry, ringMat);
    rotatingRing.position.z = 0.1;
    reactorGroup.add(rotatingRing);

    // 3. CORE GLOW PULSE
    const spriteMaterial = new THREE.SpriteMaterial({
        map: reactorTexture,
        color: 0x00FFFF,
        transparent: true,
        opacity: 0.4,
        blending: THREE.AdditiveBlending
    });
    glowSprite = new THREE.Sprite(spriteMaterial);
    glowSprite.scale.set(15, 15, 1);
    reactorGroup.add(glowSprite);

    // ANIMATION LOOP
    animateReactor();

    // RESIZE HANDLER
    window.addEventListener('resize', () => {
        const w = container.clientWidth;
        const h = container.clientHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
    });
}

function animateReactor() {
    requestAnimationFrame(animateReactor);

    const time = Date.now() * 0.001;

    // Rotation Logic (Monotonic)
    let rotationSpeed = 0.005;
    if (currentState === 'speaking') {
        rotationSpeed = 0.02 + (audioLevel * 0.05);
    } else if (currentState === 'thinking') {
        rotationSpeed = 0.1;
    }
    rotatingRing.rotation.z -= rotationSpeed;

    // React to State (Color & Scale)
    let targetScale = 1.0;
    let targetColor = new THREE.Color(0x00E5FF);

    if (currentState === 'speaking') {
        targetScale = 1.0 + (audioLevel * 0.3);
        targetColor.setHex(0x00FFFF);
    } else if (currentState === 'thinking') {
        targetColor.setHex(0xFFFFFF);
    } else if (currentState === 'listening') {
        targetColor.setHex(0x00FF00);
    }

    // Smooth Core Pulse
    const currentScale = coreMesh.scale.x;
    const lerpScale = THREE.MathUtils.lerp(currentScale, targetScale, 0.1);
    coreMesh.scale.set(lerpScale, lerpScale, lerpScale);

    // Smooth Glow Pulse
    const pulse = (Math.sin(time * 2) * 0.1) + 1;
    glowSprite.scale.set(15 * pulse, 15 * pulse, 1);

    // Update Colors
    coreMesh.material.color.lerp(targetColor, 0.05);

    renderer.render(scene, camera);
}

window.setReactorState = function (state) {
    currentState = state;
};

window.updateReactorAudio = function (data) {
    if (data && data.length > 0) {
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
            sum += Math.abs(data[i]);
        }
        audioLevel = sum / data.length;
    } else {
        audioLevel = 0;
    }
};
