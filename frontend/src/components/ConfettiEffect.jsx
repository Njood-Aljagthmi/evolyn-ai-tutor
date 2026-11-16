import React, { useEffect, useRef } from "react";

export function ConfettiEffect() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Particle colors
    const colors = [
      "#7D82B0", // slate purple (brand)
      "#557F8C", // teal cyan (brand)
      "#34d399", // emerald green (success)
      "#facc15", // gold yellow (accent)
      "#f472b6", // pink
      "#a78bfa"  // purple
    ];

    const particles = [];
    const maxParticles = 120;
    let active = true;

    // Auto deactivate spawn after 3.5 seconds
    const stopTimer = setTimeout(() => {
      active = false;
    }, 3500);

    class Particle {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * -height - 20;
        this.size = Math.random() * 8 + 6;
        this.color = colors[Math.floor(Math.random() * colors.length)];
        this.speedY = Math.random() * 4 + 3;
        this.speedX = Math.random() * 2 - 1;
        this.rotation = Math.random() * 360;
        this.rotationSpeed = Math.random() * 3 - 1.5;
        this.shape = Math.random() > 0.5 ? "circle" : "rect";
      }

      update() {
        this.y += this.speedY;
        this.x += this.speedX;
        this.rotation += this.rotationSpeed;
      }

      draw() {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate((this.rotation * Math.PI) / 180);
        ctx.fillStyle = this.color;
        
        if (this.shape === "circle") {
          ctx.beginPath();
          ctx.arc(0, 0, this.size / 2, 0, 2 * Math.PI);
          ctx.fill();
        } else {
          ctx.fillRect(-this.size / 2, -this.size / 2, this.size, this.size);
        }
        ctx.restore();
      }
    }

    // Populate initial particles
    for (let i = 0; i < 50; i++) {
      particles.push(new Particle());
    }

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw and update existing particles
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.update();
        p.draw();

        // Remove particle if it goes off screen
        if (p.y > height) {
          if (active) {
            // Replace particle at the top if still active
            particles[i] = new Particle();
          } else {
            // Delete particle if active spawn is stopped
            particles.splice(i, 1);
          }
        }
      }

      // Add new particles if active and under maximum limit
      if (active && particles.length < maxParticles) {
        particles.push(new Particle());
      }

      // Loop animation if particles remain
      if (particles.length > 0) {
        animationFrameId = requestAnimationFrame(animate);
      } else {
        ctx.clearRect(0, 0, width, height);
      }
    };

    // Resize handler
    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    animate();

    return () => {
      clearTimeout(stopTimer);
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        pointerEvents: "none",
        zIndex: 99999,
        background: "transparent"
      }}
    />
  );
}

export default ConfettiEffect;
