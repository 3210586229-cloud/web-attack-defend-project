const canvas = document.querySelector(".particle-canvas");
const ctx = canvas.getContext("2d");

let width = 0;
let height = 0;
let streams = [];
let pulses = [];
let mouse = {
  x: width / 2,
  y: height / 2,
  active: false,
};

const streamCount = 120;
const pulseCount = 9;
const magnetRadius = 170;

function randomBetween(min, max) {
  return Math.random() * (max - min) + min;
}

function resizeCanvas() {
  const ratio = window.devicePixelRatio || 1;
  width = window.innerWidth;
  height = window.innerHeight;

  canvas.width = width * ratio;
  canvas.height = height * ratio;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
}

function createStream(resetAtBottom = false) {
  const size = randomBetween(1.5, 4.5);

  return {
    x: randomBetween(0, width),
    y: resetAtBottom ? height + randomBetween(20, 160) : randomBetween(0, height),
    baseX: randomBetween(0, width),
    size,
    speed: randomBetween(0.35, 1.35),
    drift: randomBetween(-0.18, 0.18),
    wave: randomBetween(0, Math.PI * 2),
    waveSpeed: randomBetween(0.006, 0.018),
    hue: randomBetween(188, 235),
    alpha: randomBetween(0.38, 0.86),
    shape: Math.random() > 0.72 ? "packet" : "dot",
    spin: randomBetween(-0.04, 0.04),
  };
}

function createPulse() {
  return {
    x: randomBetween(0, width),
    y: height + randomBetween(0, height),
    radius: randomBetween(18, 46),
    speed: randomBetween(0.18, 0.42),
    alpha: randomBetween(0.05, 0.14),
  };
}

function resetScene() {
  streams = [];
  pulses = [];

  for (let i = 0; i < streamCount; i += 1) {
    streams.push(createStream());
  }

  for (let i = 0; i < pulseCount; i += 1) {
    pulses.push(createPulse());
  }
}

function drawBackground() {
  const gradient = ctx.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, "#070816");
  gradient.addColorStop(0.48, "#14172d");
  gradient.addColorStop(1, "#080b1c");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);
}

function updatePulse(pulse) {
  pulse.y -= pulse.speed;
  pulse.radius += 0.012;

  if (pulse.y + pulse.radius < 0) {
    Object.assign(pulse, createPulse());
  }
}

function drawPulse(pulse) {
  const gradient = ctx.createRadialGradient(pulse.x, pulse.y, 0, pulse.x, pulse.y, pulse.radius);
  gradient.addColorStop(0, `rgba(70, 190, 255, ${pulse.alpha})`);
  gradient.addColorStop(0.5, `rgba(90, 120, 255, ${pulse.alpha * 0.45})`);
  gradient.addColorStop(1, "rgba(70, 190, 255, 0)");

  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(pulse.x, pulse.y, pulse.radius, 0, Math.PI * 2);
  ctx.fill();
}

function updateStream(stream) {
  stream.wave += stream.waveSpeed;
  stream.y -= stream.speed;
  stream.x += stream.drift + Math.sin(stream.wave) * 0.22;
  stream.hue += 0.08;

  if (stream.hue > 290) {
    stream.hue = 188;
  }

  if (stream.y < -30 || stream.x < -40 || stream.x > width + 40) {
    Object.assign(stream, createStream(true));
  }

  if (!mouse.active) {
    return;
  }

  const dx = stream.x - mouse.x;
  const dy = stream.y - mouse.y;
  const distance = Math.hypot(dx, dy);

  if (distance > 0 && distance < magnetRadius) {
    const force = (magnetRadius - distance) / magnetRadius;
    const angle = Math.atan2(dy, dx);
    const swirl = angle + Math.PI / 2;
    const pull = Math.sin(Date.now() * 0.003) * 0.6;

    stream.x += Math.cos(swirl) * force * 4.2 + Math.cos(angle) * force * pull;
    stream.y += Math.sin(swirl) * force * 4.2 + Math.sin(angle) * force * pull;
    stream.hue = 285 - force * 80;
    stream.alpha = Math.min(1, stream.alpha + force * 0.025);
  }
}

function drawStream(stream) {
  ctx.save();
  ctx.translate(stream.x, stream.y);
  ctx.rotate(stream.wave * stream.spin);

  ctx.shadowColor = `hsla(${stream.hue}, 95%, 66%, 0.75)`;
  ctx.shadowBlur = stream.shape === "packet" ? 16 : 10;
  ctx.fillStyle = `hsla(${stream.hue}, 95%, 68%, ${stream.alpha})`;

  if (stream.shape === "packet") {
    ctx.fillRect(-stream.size * 1.4, -stream.size, stream.size * 2.8, stream.size * 2);
  } else {
    ctx.beginPath();
    ctx.arc(0, 0, stream.size, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.restore();
}

function drawUploadTrails() {
  ctx.lineWidth = 1;

  for (let i = 0; i < streams.length; i += 9) {
    const stream = streams[i];
    const length = 28 + stream.speed * 22;
    const gradient = ctx.createLinearGradient(stream.x, stream.y + length, stream.x, stream.y);
    gradient.addColorStop(0, "rgba(80, 170, 255, 0)");
    gradient.addColorStop(1, `hsla(${stream.hue}, 95%, 68%, ${stream.alpha * 0.28})`);

    ctx.strokeStyle = gradient;
    ctx.beginPath();
    ctx.moveTo(stream.x, stream.y + length);
    ctx.lineTo(stream.x + stream.drift * 18, stream.y);
    ctx.stroke();
  }
}

function drawMouseField() {
  if (!mouse.active) {
    return;
  }

  const gradient = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, magnetRadius);
  gradient.addColorStop(0, "rgba(96, 165, 250, 0.12)");
  gradient.addColorStop(0.45, "rgba(168, 85, 247, 0.06)");
  gradient.addColorStop(1, "rgba(96, 165, 250, 0)");

  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(mouse.x, mouse.y, magnetRadius, 0, Math.PI * 2);
  ctx.fill();
}

function animate() {
  drawBackground();

  pulses.forEach((pulse) => {
    updatePulse(pulse);
    drawPulse(pulse);
  });

  drawMouseField();

  streams.forEach(updateStream);
  drawUploadTrails();
  streams.forEach(drawStream);

  requestAnimationFrame(animate);
}

window.addEventListener("resize", () => {
  resizeCanvas();
  resetScene();
});

window.addEventListener("mousemove", (event) => {
  mouse.x = event.clientX;
  mouse.y = event.clientY;
  mouse.active = true;
});

window.addEventListener("mouseleave", () => {
  mouse.active = false;
});

resizeCanvas();
resetScene();
animate();
