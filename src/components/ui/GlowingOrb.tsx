import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface GlowingOrbProps {
  position: [number, number, number];
  color: string;
  isActive: boolean;
  size?: number;
}

export const GlowingOrb = ({ position, color, isActive, size = 0.3 }: GlowingOrbProps) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  const colorObj = useMemo(() => new THREE.Color(color), [color]);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01;
      if (isActive) {
        const scale = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.1;
        meshRef.current.scale.setScalar(scale);
      }
    }
    if (glowRef.current) {
      const opacity = isActive ? 0.3 + Math.sin(state.clock.elapsedTime * 2) * 0.2 : 0.1;
      (glowRef.current.material as THREE.MeshBasicMaterial).opacity = opacity;
    }
  });

  return (
    <group position={position}>
      {/* Core orb */}
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[size, 2]} />
        <meshStandardMaterial
          color={colorObj}
          emissive={colorObj}
          emissiveIntensity={isActive ? 2 : 0.5}
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>

      {/* Glow effect */}
      <mesh ref={glowRef} scale={1.5}>
        <sphereGeometry args={[size, 16, 16]} />
        <meshBasicMaterial
          color={colorObj}
          transparent
          opacity={0.2}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Point light when active */}
      {isActive && (
        <pointLight color={color} intensity={2} distance={3} />
      )}
    </group>
  );
};
