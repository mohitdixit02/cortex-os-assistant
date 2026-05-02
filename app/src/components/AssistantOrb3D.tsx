"use client";

import { useEffect, useRef, memo } from "react";
import * as THREE from "three";

interface AIOrbProps {
  isListening: boolean;
  isSpeaking: boolean;
}

function AssistantOrb3D({ isListening, isSpeaking }: AIOrbProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null!);
  const stateRef = useRef(0);

  // Sync internal state with props
  useEffect(() => {
    if (isSpeaking) {
      stateRef.current = 2;
    } else if (isListening) {
      stateRef.current = 1;
    } else {
      stateRef.current = 0;
    }
    
    if (materialRef.current) {
      materialRef.current.uniforms.state.value = stateRef.current;
    }
  }, [isListening, isSpeaking]);

  useEffect(() => {
    const mountPoint = mountRef.current;
    if (!mountPoint) return;

    // To prevent duplicate canvases, clear the mount point
    mountPoint.innerHTML = '';

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
      75,
      mountPoint.clientWidth / mountPoint.clientHeight,
      0.1,
      100
    );
    camera.position.z = 3;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(
      mountPoint.clientWidth,
      mountPoint.clientHeight
    );
    renderer.setClearColor(0x000000, 0); // Transparent background
    mountPoint.appendChild(renderer.domElement);

    // 💡 Light
    const light = new THREE.PointLight(0xffffff, 1.5);
    light.position.set(3, 3, 3);
    scene.add(light);

    // 🟣 Perfect Sphere
    const geometry = new THREE.SphereGeometry(1, 128, 128);

    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        state: { value: stateRef.current },
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        uniform float time;
        uniform float state;

        void main() {
          vec3 purple = vec3(0.4, 0.0, 0.8);
          vec3 blue   = vec3(0.0, 0.4, 1.0);
          vec3 red    = vec3(1.0, 0.1, 0.3);

          float pulse = 0.5 + 0.5 * sin(time * 2.0);

          vec3 color;

          if (state == 0.0) {
            color = mix(purple, blue, vUv.y + pulse * 0.2);
          } else if (state == 1.0) {
            color = mix(blue, red, vUv.y + pulse * 0.4);
          } else {
            color = mix(red, purple, vUv.y + pulse * 0.6);
          }

          // glow effect
          float glow = pow(1.0 - vUv.y, 2.0);
          color += glow * 0.6;

          gl_FragColor = vec4(color, 1.0);
        }
      `,
    });

    materialRef.current = material;

    const sphere = new THREE.Mesh(geometry, material);
    scene.add(sphere);

    let animationId: number;

    const animate = (time: number) => {
      animationId = requestAnimationFrame(animate);

      const t = time * 0.001;
      material.uniforms.time.value = t;

      // 🔁 Smooth pulsating scale
      let scale = 1;
      const currentState = stateRef.current;

      if (currentState === 0) {
        scale = 1 + Math.sin(t * 1.5) * 0.02;
      } else if (currentState === 1) {
        scale = 1 + Math.sin(t * 3.0) * 0.05;
      } else {
        scale = 1 + Math.sin(t * 6.0) * 0.08;
      }

      sphere.scale.set(scale, scale, scale);

      // subtle rotation
      sphere.rotation.y += 0.003;

      renderer.render(scene, camera);
    };

    animate(0);

    const handleResize = () => {
      const width = mountPoint.clientWidth;
      const height = mountPoint.clientHeight;

      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", handleResize);

      geometry.dispose();
      material.dispose();
      renderer.dispose();

      if (mountPoint && renderer.domElement && mountPoint.contains(renderer.domElement)) {
        mountPoint.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        width: "400px",
        height: "400px",
        background: "transparent",
      }}
    />
  );
}

export default memo(AssistantOrb3D);
