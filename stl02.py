import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="🎱 Ball Simulation", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 1rem 1rem 0 1rem; }
    h1 { font-family: 'Courier New', monospace; letter-spacing: 4px; color: #e0e8ff; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🎱 BALL COLLISION SIMULATION")

components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a14; font-family: 'Courier New', monospace; }
  canvas {
    display: block;
    border: 1px solid #2a2d50;
    border-radius: 8px;
    box-shadow: 0 0 40px rgba(80,120,255,0.15);
  }
  #ui {
    position: absolute; top: 18px; left: 18px;
    background: rgba(15,18,40,0.85);
    border: 1px solid #2a3060;
    border-radius: 10px;
    padding: 14px 18px;
    color: #a0aadd;
    font-size: 13px;
    line-height: 2;
    backdrop-filter: blur(6px);
    min-width: 200px;
  }
  #ui .val { color: #f0c040; font-weight: bold; }
  #ui .title { color: #c0d0ff; font-size: 14px; font-weight: bold; margin-bottom: 4px; letter-spacing: 2px; }
  #ui .hint { color: #505880; font-size: 11px; margin-top: 6px; line-height: 1.8; }
  #wrapper { position: relative; display: inline-block; }
</style>
</head>
<body>
<div id="wrapper">
  <canvas id="c"></canvas>
  <div id="ui">
    <div class="title">⚙ STATUS</div>
    <div>공 개수 : <span class="val" id="cnt">0</span></div>
    <div>FPS &nbsp;&nbsp;&nbsp;: <span class="val" id="fps">0</span></div>
    <div>중력 &nbsp;&nbsp;&nbsp;: <span class="val" id="grav">OFF</span></div>
    <div>트레일 : <span class="val" id="trail">ON</span></div>
    <div id="pauseLabel">상태 &nbsp;&nbsp;&nbsp;: <span class="val">▶ 실행중</span></div>
    <div class="hint">
      [SPACE] 일시정지<br>
      [R] 초기화<br>
      [G] 중력 토글<br>
      [T] 트레일 토글<br>
      [+] 공 추가 &nbsp;[-] 공 제거
    </div>
  </div>
</div>

<script>
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
const W = 980, H = 600;
canvas.width  = W;
canvas.height = H;

// ── 설정 ──────────────────────────────────────
const GRAVITY  = 0.25;
const DAMPING  = 0.82;
const FRICTION = 0.999;
const TRAIL_LEN = 20;
const MIN_R = 12, MAX_R = 34;
const INIT_COUNT = 24;

const PALETTE = [
  '#ff5050','#ff9020','#ffe030','#40dd50','#30d8d8',
  '#4080ff','#b050ff','#ff40c0','#ffffff','#50ffb0',
  '#ff8090','#30b8ff','#ffb030','#80ff40','#ff6090',
];

// ── 상태 ──────────────────────────────────────
let balls   = [];
let paused  = false;
let gravOn  = false;
let trailOn = true;
let lastT   = performance.now();
let fps     = 0;
let frameCount = 0;
let fpsTimer   = 0;

// ── Ball ──────────────────────────────────────
function randBall() {
  const r = MIN_R + Math.random() * (MAX_R - MIN_R);
  const speed = 2.5 + Math.random() * 4.5;
  const angle = Math.random() * Math.PI * 2;
  return {
    x: r + Math.random() * (W - r * 2),
    y: r + Math.random() * (H - r * 2),
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed,
    r,
    color: PALETTE[Math.floor(Math.random() * PALETTE.length)],
    trail: [],
    mass: Math.PI * r * r,
    phase: Math.random() * Math.PI * 2,
  };
}

function initBalls(n) {
  balls = [];
  for (let i = 0; i < n; i++) balls.push(randBall());
}

// ── 물리 ──────────────────────────────────────
function update(dt) {
  for (const b of balls) {
    if (trailOn) {
      b.trail.push({ x: b.x, y: b.y });
      if (b.trail.length > TRAIL_LEN) b.trail.shift();
    } else {
      b.trail = [];
    }

    if (gravOn) b.vy += GRAVITY;
    b.vx *= FRICTION;
    b.vy *= FRICTION;
    b.x  += b.vx;
    b.y  += b.vy;
    b.phase += 0.05;

    // 벽
    if (b.x - b.r < 0)   { b.x =  b.r;    b.vx =  Math.abs(b.vx) * DAMPING; }
    if (b.x + b.r > W)   { b.x =  W - b.r; b.vx = -Math.abs(b.vx) * DAMPING; }
    if (b.y - b.r < 0)   { b.y =  b.r;    b.vy =  Math.abs(b.vy) * DAMPING; }
    if (b.y + b.r > H)   { b.y =  H - b.r; b.vy = -Math.abs(b.vy) * DAMPING; }
  }

  // 공 간 충돌
  for (let i = 0; i < balls.length; i++) {
    for (let j = i + 1; j < balls.length; j++) {
      const a = balls[i], b = balls[j];
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.hypot(dx, dy);
      const minD = a.r + b.r;
      if (dist === 0 || dist >= minD) continue;

      const overlap = (minD - dist) / 2;
      const nx = dx / dist, ny = dy / dist;
      a.x -= nx * overlap; a.y -= ny * overlap;
      b.x += nx * overlap; b.y += ny * overlap;

      const dvx = a.vx - b.vx, dvy = a.vy - b.vy;
      const dot = dvx * nx + dvy * ny;
      if (dot >= 0) continue;

      const imp = 2 * dot / (a.mass + b.mass);
      a.vx -= imp * b.mass * nx; a.vy -= imp * b.mass * ny;
      b.vx += imp * a.mass * nx; b.vy += imp * a.mass * ny;
    }
  }
}

// ── 렌더링 ────────────────────────────────────
function hexToRgb(hex) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `${r},${g},${b}`;
}

function drawBackground() {
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, '#0a0a16');
  grad.addColorStop(1, '#0e1228');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);

  // 그리드
  ctx.strokeStyle = 'rgba(40,44,80,0.4)';
  ctx.lineWidth = 0.5;
  for (let x = 0; x < W; x += 70) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
  }
  for (let y = 0; y < H; y += 70) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }

  // 테두리
  ctx.strokeStyle = 'rgba(60,70,140,0.8)';
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, W - 2, H - 2);
}

function drawBall(b) {
  const rgb = hexToRgb(b.color);

  // 트레일
  if (trailOn && b.trail.length > 1) {
    for (let i = 1; i < b.trail.length; i++) {
      const t = i / b.trail.length;
      const r = Math.max(2, b.r * 0.5 * t);
      const alpha = t * t * 0.6;
      ctx.beginPath();
      ctx.arc(b.trail[i].x, b.trail[i].y, r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${rgb},${alpha})`;
      ctx.fill();
    }
  }

  // 그림자
  ctx.beginPath();
  ctx.ellipse(b.x, b.y + b.r - 2, b.r * 1.6, b.r * 0.4, 0, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(0,0,0,0.25)';
  ctx.fill();

  // 글로우
  const glowR = b.r + 8 + Math.sin(b.phase) * 4;
  const glowGrad = ctx.createRadialGradient(b.x, b.y, b.r * 0.5, b.x, b.y, glowR);
  glowGrad.addColorStop(0, `rgba(${rgb},0.25)`);
  glowGrad.addColorStop(1, `rgba(${rgb},0)`);
  ctx.beginPath();
  ctx.arc(b.x, b.y, glowR, 0, Math.PI * 2);
  ctx.fillStyle = glowGrad;
  ctx.fill();

  // 본체
  const bodyGrad = ctx.createRadialGradient(
    b.x - b.r * 0.3, b.y - b.r * 0.3, b.r * 0.1,
    b.x, b.y, b.r
  );
  bodyGrad.addColorStop(0, `rgba(${rgb},1)`);
  bodyGrad.addColorStop(0.6, b.color);
  bodyGrad.addColorStop(1, `rgba(${Math.max(0,parseInt(b.color.slice(1,3),16)-60)},${Math.max(0,parseInt(b.color.slice(3,5),16)-60)},${Math.max(0,parseInt(b.color.slice(5,7),16)-60)},1)`);
  ctx.beginPath();
  ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
  ctx.fillStyle = bodyGrad;
  ctx.fill();

  // 하이라이트
  const hlR = b.r * 0.35;
  const hlGrad = ctx.createRadialGradient(
    b.x - b.r * 0.3, b.y - b.r * 0.35, 0,
    b.x - b.r * 0.3, b.y - b.r * 0.35, hlR
  );
  hlGrad.addColorStop(0, 'rgba(255,255,255,0.55)');
  hlGrad.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.beginPath();
  ctx.arc(b.x - b.r * 0.3, b.y - b.r * 0.35, hlR, 0, Math.PI * 2);
  ctx.fillStyle = hlGrad;
  ctx.fill();
}

// ── HUD 업데이트 ──────────────────────────────
function updateHUD(now) {
  frameCount++;
  fpsTimer += now - lastT;
  if (fpsTimer >= 500) {
    fps = Math.round(frameCount / fpsTimer * 1000);
    frameCount = 0; fpsTimer = 0;
  }
  document.getElementById('cnt').textContent  = balls.length;
  document.getElementById('fps').textContent  = fps;
  document.getElementById('grav').textContent = gravOn  ? 'ON ↓' : 'OFF';
  document.getElementById('trail').textContent= trailOn ? 'ON'   : 'OFF';
  document.getElementById('pauseLabel').innerHTML =
    paused
      ? '상태 &nbsp;&nbsp;&nbsp;: <span class="val">⏸ 일시정지</span>'
      : '상태 &nbsp;&nbsp;&nbsp;: <span class="val">▶ 실행중</span>';
}

// ── 메인 루프 ─────────────────────────────────
function loop(now) {
  const dt = now - lastT;
  lastT = now;

  if (!paused) update(dt);

  drawBackground();
  for (const b of balls) drawBall(b);

  updateHUD(now);
  requestAnimationFrame(loop);
}

// ── 키보드 ────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.code === 'Space')       { e.preventDefault(); paused = !paused; }
  else if (e.key === 'r' || e.key === 'R') initBalls(INIT_COUNT);
  else if (e.key === 'g' || e.key === 'G') gravOn  = !gravOn;
  else if (e.key === 't' || e.key === 'T') trailOn = !trailOn;
  else if (e.key === '+' || e.key === '=') for (let i=0;i<3;i++) balls.push(randBall());
  else if (e.key === '-')       for (let i=0;i<Math.min(3,balls.length-1);i++) balls.pop();
});

// ── 시작 ──────────────────────────────────────
initBalls(INIT_COUNT);
requestAnimationFrame(loop);
</script>
</body>
</html>
""", height=640, scrolling=False)