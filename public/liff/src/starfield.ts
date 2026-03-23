/**
 * 星空キャンバスアニメーション
 */

interface Star {
  x: number;
  y: number;
  r: number;
  speed: number;
}

let stars: Star[] = [];
let canvas: HTMLCanvasElement;
let ctx: CanvasRenderingContext2D;

function resize(): void {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function createStars(): void {
  stars = [];
  for (let i = 0; i < 120; i++) {
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.5,
      speed: Math.random() * 0.3 + 0.1,
    });
  }
}

function animate(): void {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = 'white';
  stars.forEach(star => {
    ctx.beginPath();
    ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
    ctx.fill();
    star.y += star.speed;
    if (star.y > canvas.height) {
      star.y = 0;
      star.x = Math.random() * canvas.width;
    }
  });
  requestAnimationFrame(animate);
}

/** 星空アニメーションを初期化・開始 */
export function initStarfield(): void {
  const el = document.getElementById('starfield') as HTMLCanvasElement | null;
  if (!el) return;
  canvas = el;
  const context = canvas.getContext('2d');
  if (!context) return;
  ctx = context;
  window.addEventListener('resize', resize);
  resize();
  createStars();
  animate();
}
