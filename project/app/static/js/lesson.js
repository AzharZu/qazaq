function startPronunciation(targetWord, resultElementId) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Бұл браузерде дауыс тану қолжетімді емес.");
    return;
  }

  const recognition = new SpeechRecognition();
  const preferred = ["kk-KZ", "ru-RU", "tr-TR"];
  const browserLangs = (navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language]).map(
    (l) => (l || "").toLowerCase()
  );
  const selectedLang =
    preferred.find((lang) => browserLangs.some((b) => b.startsWith(lang.toLowerCase().split("-")[0]))) || preferred[0];
  recognition.lang = selectedLang;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = function (event) {
    const said = event.results[0][0].transcript.toLowerCase().trim();
    const target = (targetWord || "").toLowerCase().trim();
    const el = document.getElementById(resultElementId);
    if (!el) return;

    if (said.includes(target)) {
      el.innerText = "✔ Дұрысқа жақын айттың: " + said;
      el.className = "text-success small";
    } else {
      el.innerText = "❌ Дұрыс емес. Сен: " + said + " | Керегі: " + target;
      el.className = "text-danger small";
    }
  };

  recognition.onerror = function (event) {
    console.error(event.error);
    alert("Дауыс тануда қате кетті: " + event.error);
  };

  recognition.start();
}
