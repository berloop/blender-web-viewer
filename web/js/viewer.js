/**
 * Blender Web Preview Viewer
 * Main JavaScript file for rendering and controlling the 3D scene
 */

// At the top of your viewer.js file, add this check
if (!window.OrbitControls && THREE.OrbitControls) {
  window.OrbitControls = THREE.OrbitControls;
}

if (!window.GLTFLoader && THREE.GLTFLoader) {
  window.GLTFLoader = THREE.GLTFLoader;
}

if (!window.DRACOLoader && THREE.DRACOLoader) {
  window.DRACOLoader = THREE.DRACOLoader;
}

window.addEventListener('DOMContentLoaded', function() {
  if (window.location.protocol === 'file:') {
    const warningDiv = document.createElement('div');
    warningDiv.style.position = 'fixed';
    warningDiv.style.top = '0';
    warningDiv.style.left = '0';
    warningDiv.style.width = '100%';
    warningDiv.style.backgroundColor = 'rgba(255, 50, 50, 0.9)';
    warningDiv.style.color = 'white';
    warningDiv.style.padding = '10px';
    warningDiv.style.zIndex = '9999';
    warningDiv.style.textAlign = 'center';
    warningDiv.innerHTML = 'This 3D viewer may not work when opened directly from your computer. ' +
                          'For best results: <br>1) Use a web server (like VS Code Live Server) ' +
                          'or <br>2) Upload these files to a web hosting service.';
    document.body.appendChild(warningDiv);
  }
});

// Global variables
let scene, camera, renderer, controls;
let mixer, clock, animationActions = [];
let grid, sceneInfo;
let isPlaying = false;
let animationDuration = 0;

// DOM elements
const viewer = document.getElementById("viewer");
const sceneTitle = document.getElementById("scene-title");
const sceneStats = document.getElementById("scene-stats");
const animationSlider = document.getElementById("animation-slider");
const animationTime = document.getElementById("animation-time");
const animationControls = document.getElementById("animation-controls");

// Initialize the viewer
function init() {
  // Create loading overlay
  const loadingOverlay = document.createElement("div");
  loadingOverlay.className = "loading-overlay";
  loadingOverlay.innerHTML = '<div class="loading-spinner"></div>';
  viewer.appendChild(loadingOverlay);

  // Initialize Three.js scene immediately without waiting for scene_info.json
  initScene();

  // Try to load scene info, but continue even if it fails
  fetch("scene_info.json")
    .then((response) => response.json())
    .then((data) => {
      console.log("Scene info loaded:", data);
      sceneInfo = data;
      sceneTitle.textContent = data.title;
      sceneStats.textContent = `Objects: ${data.objects}`;

      // Hide animation controls if there are no animations
      if (!data.has_animations) {
        animationControls.style.display = "none";
      }
    })
    .catch((error) => {
      console.log("Error loading scene info:", error);
      // Continue anyway
      sceneTitle.textContent = "Blender Scene";
      sceneStats.textContent = "No scene info available";
    })
    .finally(() => {
      // Load the model after scene is initialized, regardless of scene_info status
      loadModel();
    });
}

// Initialize Three.js scene with BETTER LIGHTING
function initScene() {
  console.log("Initializing Three.js scene");

  // Create scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1a1a);

  // Create camera
  camera = new THREE.PerspectiveCamera(
    45,
    viewer.clientWidth / viewer.clientHeight,
    0.1,
    1000
  );
  camera.position.set(5, 5, 5);

  // Create renderer
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(viewer.clientWidth, viewer.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  viewer.appendChild(renderer.domElement);

  try {
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
  } catch (e) {
    console.error("Error creating orbit controls:", e);
    console.log("Attempting alternative orbit controls initialization");

    if (typeof OrbitControls !== "undefined") {
      controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
    } else {
      console.error("OrbitControls not available. Scene will be static.");
    }
  }

  // Add grid
  grid = new THREE.GridHelper(10, 10, 0x888888, 0x444444);
  scene.add(grid);

  // Make scene and renderer globally accessible for inspector
  window.scene = scene;
  window.renderer = renderer;

  // ENHANCED LIGHTING SETUP - LIT FROM ALL ANGLES
  
  // Brighter ambient light for overall illumination
  const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
  scene.add(ambientLight);

  // Main directional light (key light) - brighter
  const keyLight = new THREE.DirectionalLight(0xffffff, 1.5);
  keyLight.position.set(5, 10, 7.5);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.width = 2048;
  keyLight.shadow.mapSize.height = 2048;
  keyLight.shadow.camera.near = 0.1;
  keyLight.shadow.camera.far = 50;
  keyLight.shadow.camera.left = -10;
  keyLight.shadow.camera.right = 10;
  keyLight.shadow.camera.top = 10;
  keyLight.shadow.camera.bottom = -10;
  scene.add(keyLight);

  // Fill light from the left
  const fillLight = new THREE.DirectionalLight(0xffffff, 0.8);
  fillLight.position.set(-5, 5, 5);
  scene.add(fillLight);

  // Back light for rim lighting
  const backLight = new THREE.DirectionalLight(0xffffff, 0.6);
  backLight.position.set(0, 5, -5);
  scene.add(backLight);

  // Additional side lights for full coverage
  const leftLight = new THREE.DirectionalLight(0xffffff, 0.4);
  leftLight.position.set(-10, 3, 0);
  scene.add(leftLight);

  const rightLight = new THREE.DirectionalLight(0xffffff, 0.4);
  rightLight.position.set(10, 3, 0);
  scene.add(rightLight);

  // Store original light intensities for lighting control slider
  scene.traverse((child) => {
    if (child.isLight && child instanceof THREE.DirectionalLight) {
      child.userData.originalIntensity = child.intensity;
    }
  });

  // Store original ambient light intensity too
  ambientLight.userData.originalIntensity = ambientLight.intensity;

  // Clock for animations
  clock = new THREE.Clock();

  // Handle window resize
  window.addEventListener("resize", onWindowResize);

  // Start animation loop
  animate();

  console.log("Scene initialized with enhanced lighting");
}

// Load the GLTF model
function loadModel() {
  console.log("Attempting to load model from: scene.glb");

  const loader = new GLTFLoader();

  try {
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath("https://www.gstatic.com/draco/v1/decoders/");
    loader.setDRACOLoader(dracoLoader);
  } catch (e) {
    console.warn("Draco compression support not available:", e);
  }

  fetch("scene.glb")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      console.log(
        "scene.glb exists, file size:",
        response.headers.get("content-length"),
        "bytes"
      );
      
      // Update file size in model info
      const fileSize = response.headers.get("content-length");
      if (fileSize && window.setModelFileSize) {
        window.setModelFileSize(parseInt(fileSize));
      }
      
      return true;
    })
    .then(() => {
      loader.load(
        "scene.glb",
        function (gltf) {
          console.log("Model loaded successfully:", gltf);

          console.log("Scene contains:");
          gltf.scene.traverse(function (child) {
            if (child.isMesh) {
              console.log("- Mesh:", child.name);
              // Enable shadows for better lighting
              child.castShadow = true;
              child.receiveShadow = true;
            }
            if (child.isLight) {
              console.log("- Light:", child.name);
            }
            if (child.isCamera) {
              console.log("- Camera:", child.name);
            }
          });

          scene.add(gltf.scene);
          centerCameraOnModel(gltf.scene);

          // Update model information widget
          if (window.updateModelInfo) {
            window.updateModelInfo(gltf);
          }

          if (gltf.animations && gltf.animations.length > 0) {
            console.log("Model has animations:", gltf.animations.length);
            mixer = new THREE.AnimationMixer(gltf.scene);

            gltf.animations.forEach((clip) => {
              const action = mixer.clipAction(clip);
              animationActions.push(action);
            });

            animationDuration = gltf.animations[0].duration;
            animationSlider.max = animationDuration;
            updateAnimationTime(0);

            if (animationActions.length > 0) {
              animationActions[0].play();
              isPlaying = true;
            }
          } else {
            console.log("Model has no animations");
          }

          // Remove loading overlay
          const loadingOverlay = document.querySelector(".loading-overlay");
          if (loadingOverlay) {
            loadingOverlay.remove();
          }
        },
        function (xhr) {
          const percent = Math.floor((xhr.loaded / xhr.total) * 100);
          console.log(`Loading model: ${percent}% loaded`);
        },
        function (error) {
          console.error("Error loading model:", error);
          console.error("Error details:", error.message);

          alert("Error loading 3D model - check browser console for details");

          const loadingOverlay = document.querySelector(".loading-overlay");
          if (loadingOverlay) {
            loadingOverlay.remove();
          }
        }
      );
    })
    .catch((error) => {
      console.error("Error checking/loading scene.glb:", error);

      const loadingOverlay = document.querySelector(".loading-overlay");
      if (loadingOverlay) {
        loadingOverlay.remove();
      }

      const geometry = new THREE.BoxGeometry(1, 1, 1);
      const material = new THREE.MeshStandardMaterial({ color: 0xff0000 });
      const cube = new THREE.Mesh(geometry, material);
      scene.add(cube);

      const textDiv = document.createElement("div");
      textDiv.style.position = "absolute";
      textDiv.style.top = "50%";
      textDiv.style.left = "50%";
      textDiv.style.transform = "translate(-50%, -50%)";
      textDiv.style.color = "#ffffff";
      textDiv.style.background = "rgba(0,0,0,0.7)";
      textDiv.style.padding = "20px";
      textDiv.style.borderRadius = "5px";
      textDiv.innerHTML = "Error loading model. See console for details.";
      viewer.appendChild(textDiv);
    });
}

// Center camera on model
function centerCameraOnModel(model) {
  const boundingBox = new THREE.Box3().setFromObject(model);
  const center = new THREE.Vector3();
  boundingBox.getCenter(center);
  const size = new THREE.Vector3();
  boundingBox.getSize(size);

  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = camera.fov * (Math.PI / 180);
  let distance = maxDim / (2 * Math.tan(fov / 2));
  distance = Math.max(distance, 1);

  if (controls) {
    const direction = camera.position.clone().sub(controls.target).normalize();
    camera.position.copy(
      center.clone().add(direction.multiplyScalar(distance * 1.5))
    );
    controls.target.copy(center);
    controls.update();
  } else {
    camera.position.set(center.x, center.y + distance, center.z + distance);
    camera.lookAt(center);
  }
}

// Window resize handler
function onWindowResize() {
  camera.aspect = viewer.clientWidth / viewer.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(viewer.clientWidth, viewer.clientHeight);
}

// Animation loop
function animate() {
  requestAnimationFrame(animate);

  if (controls && controls.update) {
    controls.update();
  }

  if (mixer && isPlaying) {
    const delta = clock.getDelta();
    mixer.update(delta);

    if (animationDuration > 0) {
      const time = mixer.time % animationDuration;
      animationSlider.value = time;
      updateAnimationTime(time);
    }
  }

  renderer.render(scene, camera);
}

// Update animation time display
function updateAnimationTime(time) {
  if (animationDuration > 0) {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    const formattedTime = `${minutes}:${seconds.toString().padStart(2, "0")}`;

    const durationMinutes = Math.floor(animationDuration / 60);
    const durationSeconds = Math.floor(animationDuration % 60);
    const formattedDuration = `${durationMinutes}:${durationSeconds
      .toString()
      .padStart(2, "0")}`;

    animationTime.textContent = `${formattedTime} / ${formattedDuration}`;
  } else {
    animationTime.textContent = "0:00 / 0:00";
  }
}

// Set up event listeners
function setupEventListeners() {
  try {
    // Camera views
    document
      .getElementById("btn-reset-camera")
      .addEventListener("click", () => {
        if (scene.children.length > 0) {
          centerCameraOnModel(scene);
        }
      });

    document.getElementById("btn-top-view").addEventListener("click", () => {
      camera.position.set(0, 10, 0);
      if (controls) {
        controls.target.set(0, 0, 0);
        controls.update();
      } else {
        camera.lookAt(0, 0, 0);
      }
    });

    document.getElementById("btn-front-view").addEventListener("click", () => {
      camera.position.set(0, 0, 10);
      if (controls) {
        controls.target.set(0, 0, 0);
        controls.update();
      } else {
        camera.lookAt(0, 0, 0);
      }
    });

    document.getElementById("btn-side-view").addEventListener("click", () => {
      camera.position.set(10, 0, 0);
      if (controls) {
        controls.target.set(0, 0, 0);
        controls.update();
      } else {
        camera.lookAt(0, 0, 0);
      }
    });

    // Display toggles
    document
      .getElementById("toggle-wireframe")
      .addEventListener("change", (e) => {
        scene.traverse((child) => {
          if (child.isMesh) {
            child.material.wireframe = e.target.checked;
          }
        });
      });

    document.getElementById("toggle-grid").addEventListener("change", (e) => {
      grid.visible = e.target.checked;
    });

    document.getElementById("toggle-lights").addEventListener("change", (e) => {
      scene.traverse((child) => {
        if (child.isLight && !(child instanceof THREE.AmbientLight)) {
          child.visible = e.target.checked;
        }
      });
    });

    // Animation controls
    document.getElementById("btn-play").addEventListener("click", () => {
      if (mixer && animationActions.length > 0) {
        isPlaying = true;
        animationActions.forEach((action) => {
          action.paused = false;
          action.play();
        });
      }
    });

    document.getElementById("btn-pause").addEventListener("click", () => {
      if (mixer && animationActions.length > 0) {
        isPlaying = false;
        animationActions.forEach((action) => {
          action.paused = true;
        });
      }
    });

    document.getElementById("btn-stop").addEventListener("click", () => {
      if (mixer && animationActions.length > 0) {
        isPlaying = false;
        animationActions.forEach((action) => {
          action.stop();
        });
        mixer.setTime(0);
        updateAnimationTime(0);
      }
    });

    // Animation slider
    animationSlider.addEventListener("input", (e) => {
      if (mixer && animationActions.length > 0) {
        const time = parseFloat(e.target.value);
        mixer.setTime(time);
        updateAnimationTime(time);
      }
    });
  } catch (e) {
    console.error("Error setting up event listeners:", e);
  }
}

// Initialize the viewer when the page loads
window.addEventListener("load", () => {
  console.log("Window loaded, initializing viewer");
  init();
  setupEventListeners();
});