## Animation AI Orb
Use the below code to create an animated AI orb that can be used in the assistant interface. This orb will have a pulsating effect and change colors based on different states (listening, processing, idle). You can integrate this and remove the existing orb.

```js
"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function AIOrb() {
  const mountRef = useRef(null);

  useEffect(() => {
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
      75,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      100
    );
    camera.position.z = 3;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(
      mountRef.current.clientWidth,
      mountRef.current.clientHeight
    );
    mountRef.current.appendChild(renderer.domElement);

    // 💡 Light
    const light = new THREE.PointLight(0xffffff, 1.5);
    light.position.set(3, 3, 3);
    scene.add(light);

    // 🟣 Perfect Sphere
    const geometry = new THREE.SphereGeometry(1, 128, 128);

    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        state: { value: 0 },
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

    const sphere = new THREE.Mesh(geometry, material);
    scene.add(sphere);

    let currentState = 0;

    const handleClick = () => {
      currentState = (currentState + 1) % 3;
      material.uniforms.state.value = currentState;
    };

    window.addEventListener("click", handleClick);

    let animationId;

    const animate = (time) => {
      animationId = requestAnimationFrame(animate);

      const t = time * 0.001;
      material.uniforms.time.value = t;

      // 🔁 Smooth pulsating scale
      let scale = 1;

      if (currentState === 0) {
        scale = 1 + Math.sin(t * 1.5) * 0.02;
      } else if (currentState === 1) {
        scale = 1 + Math.sin(t * 3.0) * 0.05;
      } else {
        scale = 1 + Math.sin(t * 6.0) * 0.08;
      }

      sphere.scale.set(scale, scale, scale);

      // subtle rotation (kept minimal)
      sphere.rotation.y += 0.003;

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      const width = mountRef.current.clientWidth;
      const height = mountRef.current.clientHeight;

      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("click", handleClick);

      geometry.dispose();
      material.dispose();
      renderer.dispose();

      mountRef.current.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        width: "100%",
        height: "100vh",
        background: "#0a0a0f",
      }}
    />
  );
}
```