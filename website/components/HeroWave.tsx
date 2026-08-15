"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * Die leuchtende Preiswelle im Hero — ein WebGL-Shader, der drei leicht
 * versetzte Sinuslinien in VoltSurfer-Grün/Cyan über Nacht-Navy zeichnet.
 * Füllt seinen Container (nicht den Viewport) und steht bei
 * prefers-reduced-motion still.
 */
export function HeroWave({ className = "" }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = canvas?.parentElement;
    if (!canvas || !container) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const vertexShader = `
      attribute vec3 position;
      void main() {
        gl_Position = vec4(position, 1.0);
      }
    `;

    // Basiert auf dem klassischen Neon-Linien-Shader (drei Farbkanäle mit
    // chromatischem Versatz), eingefärbt auf Markenfarben statt RGB.
    const fragmentShader = `
      precision highp float;
      uniform vec2 resolution;
      uniform float time;

      void main() {
        vec2 p = (gl_FragCoord.xy * 2.0 - resolution) / min(resolution.x, resolution.y);

        float d = length(p) * 0.06;

        float gx = p.x;
        float cx = p.x * (1.0 + d);
        float wx = p.x * (1.0 - d);

        // +0.52 schiebt die Welle ins untere Drittel, damit sie nicht
        // durch die Hero-Texte laeuft
        float g = 0.045 / abs(p.y + 0.52 + sin((gx + time) * 1.1) * 0.34);
        float c = 0.035 / abs(p.y + 0.52 + sin((cx + time) * 1.1) * 0.34);
        float w = 0.02  / abs(p.y + 0.52 + sin((wx + time) * 1.1) * 0.34);

        // Markenfarben: Elektro-Gruen, Cyan, ein Hauch Weiss fuer den Kern
        vec3 col = g * vec3(0.0, 0.898, 0.627)
                 + c * vec3(0.22, 0.741, 0.973)
                 + w * vec3(0.9, 0.98, 0.97);

        gl_FragColor = vec4(col, 1.0);
      }
    `;

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(new THREE.Color(0x0b1d33));

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, -1);
    const uniforms = {
      resolution: { value: [container.clientWidth, container.clientHeight] },
      time: { value: 0.6 },
    };

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.BufferAttribute(
        new Float32Array([-1, -1, 0, 1, -1, 0, -1, 1, 0, 1, -1, 0, -1, 1, 0, 1, 1, 0]),
        3,
      ),
    );
    const material = new THREE.RawShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms,
      side: THREE.DoubleSide,
    });
    scene.add(new THREE.Mesh(geometry, material));

    const resize = () => {
      renderer.setSize(container.clientWidth, container.clientHeight, false);
      uniforms.resolution.value = [
        container.clientWidth * renderer.getPixelRatio(),
        container.clientHeight * renderer.getPixelRatio(),
      ];
      renderer.render(scene, camera);
    };

    let animationId: number | null = null;
    const animate = () => {
      uniforms.time.value += 0.006;
      renderer.render(scene, camera);
      animationId = requestAnimationFrame(animate);
    };

    const observer = new ResizeObserver(resize);
    observer.observe(container);
    resize();
    if (!reduceMotion) animate();

    return () => {
      if (animationId !== null) cancelAnimationFrame(animationId);
      observer.disconnect();
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
    />
  );
}
