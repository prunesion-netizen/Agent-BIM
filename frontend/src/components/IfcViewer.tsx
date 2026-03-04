import { useState, useEffect, useRef, useCallback } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { IFCLoader } from "web-ifc-three";
import { IFCSPACE } from "web-ifc";
import { useAuth } from "../contexts/AuthProvider";

interface IfcInfo {
  filename: string;
  file_size_bytes: number;
  file_size_mb: number;
  uploaded_at: string | null;
  summary: Record<string, unknown> | null;
}

interface Props {
  projectId: number | null;
}

export default function IfcViewer({ projectId }: Props) {
  const { authFetch } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ifcInfo, setIfcInfo] = useState<IfcInfo | null>(null);
  const [wireframe, setWireframe] = useState(false);
  const [elementCount, setElementCount] = useState(0);
  const [modelLoaded, setModelLoaded] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const modelRef = useRef<THREE.Object3D | null>(null);
  const animFrameRef = useRef<number>(0);

  // Initialize Three.js scene
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f4f8);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(15, 15, 15);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lights
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambient);
    const directional = new THREE.DirectionalLight(0xffffff, 0.8);
    directional.position.set(10, 20, 10);
    directional.castShadow = true;
    scene.add(directional);

    // Grid
    const grid = new THREE.GridHelper(50, 50, 0xcccccc, 0xe0e0e0);
    scene.add(grid);

    // Axes
    const axes = new THREE.AxesHelper(5);
    scene.add(axes);

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;
    controlsRef.current = controls;

    // Animation loop
    const animate = () => {
      animFrameRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Resize handler
    const onResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(animFrameRef.current);
      controls.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      // Dispose geometries and materials
      scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh) {
          obj.geometry?.dispose();
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => m.dispose());
          } else {
            obj.material?.dispose();
          }
        }
      });
    };
  }, []);

  // Fetch IFC info when projectId changes
  useEffect(() => {
    setIfcInfo(null);
    setError(null);
    setModelLoaded(false);
    setElementCount(0);

    // Remove previous model from scene
    if (modelRef.current && sceneRef.current) {
      sceneRef.current.remove(modelRef.current);
      modelRef.current = null;
    }

    if (!projectId) return;

    authFetch(`/api/projects/${projectId}/ifc-info`)
      .then((res) => {
        if (res.status === 404) return null;
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (data) setIfcInfo(data);
      })
      .catch((err) => {
        console.warn("IFC info not available:", err);
      });
  }, [projectId]);

  // Zoom to fit model
  const zoomToFit = useCallback(() => {
    const model = modelRef.current;
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!model || !camera || !controls) return;

    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const distance = maxDim * 1.5;

    camera.position.set(
      center.x + distance,
      center.y + distance * 0.7,
      center.z + distance,
    );
    controls.target.copy(center);
    controls.update();
  }, []);

  // Load IFC model
  const loadModel = useCallback(async () => {
    if (!projectId || !sceneRef.current) return;

    setLoading(true);
    setError(null);

    try {
      const response = await authFetch(`/api/projects/${projectId}/ifc-file`);
      if (!response.ok) {
        throw new Error(
          response.status === 404
            ? "Fișierul IFC nu a fost găsit."
            : `Eroare descărcare: HTTP ${response.status}`,
        );
      }

      const buffer = await response.arrayBuffer();

      const loader = new IFCLoader();
      await loader.ifcManager.setWasmPath(
        "https://cdn.jsdelivr.net/npm/web-ifc@0.0.36/",
        true,
      );

      // Optimize: skip rendering IFCSPACE elements
      loader.ifcManager.parser.setupOptionalCategories({
        [IFCSPACE]: false,
      });

      await loader.ifcManager.applyWebIfcConfig({
        USE_FAST_BOOLS: true,
      });

      const model = await loader.ifcManager.parse(new Uint8Array(buffer));

      // Remove previous model
      if (modelRef.current) {
        sceneRef.current!.remove(modelRef.current);
      }

      sceneRef.current!.add(model);
      modelRef.current = model;

      // Count meshes
      let count = 0;
      model.traverse((child) => {
        if (child instanceof THREE.Mesh) count++;
      });
      setElementCount(count);
      setModelLoaded(true);

      zoomToFit();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la încărcarea modelului IFC.");
    } finally {
      setLoading(false);
    }
  }, [projectId, zoomToFit]);

  // Toggle wireframe
  const toggleWireframe = useCallback(() => {
    setWireframe((prev) => {
      const next = !prev;
      if (modelRef.current) {
        modelRef.current.traverse((child) => {
          if (child instanceof THREE.Mesh && child.material) {
            if (Array.isArray(child.material)) {
              child.material.forEach((m) => (m.wireframe = next));
            } else {
              child.material.wireframe = next;
            }
          }
        });
      }
      return next;
    });
  }, []);

  // Reset view
  const resetView = useCallback(() => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls) return;

    if (modelRef.current) {
      zoomToFit();
    } else {
      camera.position.set(15, 15, 15);
      controls.target.set(0, 0, 0);
      controls.update();
    }
  }, [zoomToFit]);

  return (
    <div className="viewer-container">
      <div className="section-header">
        <div className="section-icon">&#9635;</div>
        <div>
          <h2 className="section-title">Viewer 3D IFC</h2>
          <p className="section-subtitle">
            Vizualizare model IFC direct in browser
          </p>
        </div>
      </div>

      {!projectId && (
        <div className="viewer-alert viewer-alert-info">
          Selecteaza un proiect din meniul de sus pentru a vizualiza modelul IFC.
        </div>
      )}

      {projectId && ifcInfo && (
        <div className="viewer-info-bar">
          <div className="viewer-info-item">
            <span className="viewer-info-label">Fisier:</span>
            <span className="viewer-info-value">{ifcInfo.filename}</span>
          </div>
          <div className="viewer-info-item">
            <span className="viewer-info-label">Dimensiune:</span>
            <span className="viewer-info-value">{ifcInfo.file_size_mb} MB</span>
          </div>
          {elementCount > 0 && (
            <div className="viewer-info-item">
              <span className="viewer-info-label">Elemente 3D:</span>
              <span className="viewer-info-value">{elementCount}</span>
            </div>
          )}
        </div>
      )}

      {projectId && !ifcInfo && !error && (
        <div className="viewer-alert viewer-alert-info">
          Nu exista fisier IFC uploadat pentru acest proiect. Importa un fisier
          IFC din tab-ul "Verificare BEP".
        </div>
      )}

      {error && (
        <div className="viewer-alert viewer-alert-error">{error}</div>
      )}

      <div className="viewer-toolbar">
        <button
          className="viewer-toolbar-btn"
          onClick={loadModel}
          disabled={loading || !projectId || !ifcInfo}
        >
          {loading ? "Se incarca..." : modelLoaded ? "Reincarca Model" : "Incarca Model 3D"}
        </button>
        <button
          className="viewer-toolbar-btn"
          onClick={resetView}
          disabled={!modelLoaded}
        >
          Reset View
        </button>
        <button
          className={`viewer-toolbar-btn ${wireframe ? "active" : ""}`}
          onClick={toggleWireframe}
          disabled={!modelLoaded}
        >
          Wireframe
        </button>
        <button
          className="viewer-toolbar-btn"
          onClick={zoomToFit}
          disabled={!modelLoaded}
        >
          Zoom Complet
        </button>
      </div>

      <div className="viewer-canvas-wrapper">
        {loading && (
          <div className="viewer-loading-overlay">
            <div className="viewer-spinner" />
            <p>Se incarca modelul IFC...</p>
          </div>
        )}
        <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
      </div>
    </div>
  );
}
