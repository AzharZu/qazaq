// Lightweight mic waveform visualization for lesson word practice
(function() {
  const wave = document.getElementById("waveform");
  if (!wave) return;
  const bars = wave.querySelectorAll("span");
  const MicContext = window.AudioContext || window.webkitAudioContext;
  if (!MicContext || !navigator.mediaDevices?.getUserMedia) return;

  let analyser;
  let source;
  let raf;

  async function setup() {
    try {
      const ctx = new MicContext();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      analyser = ctx.createAnalyser();
      const input = ctx.createMediaStreamSource(stream);
      input.connect(analyser);
      source = stream;
      analyser.fftSize = 256;
      draw();
    } catch (e) {
      // silent fail
    }
  }

  function draw() {
    if (!analyser || !bars.length) return;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteTimeDomainData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
        sum += Math.abs(dataArray[i] - 128);
    }
    const avg = sum / dataArray.length;
    const normalized = Math.min(1, avg / 40);
    bars.forEach((bar, idx) => {
        const height = 8 + Math.sin((Date.now() / 200) + idx) * 6 + normalized * 40;
        bar.style.height = `${Math.max(8, height)}px`;
    });
    raf = requestAnimationFrame(draw);
  }

  setup();

  window.addEventListener("beforeunload", () => {
    if (raf) cancelAnimationFrame(raf);
    if (source) source.getTracks().forEach((t) => t.stop());
  });
})();
