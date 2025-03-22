//Lanzar texto a voz
function hablar(txt) {
    if (txt) {
        console.log(txt)
        let sintetizador = window.speechSynthesis;
        if (!sintetizador) {
          alert("¡La API de síntesis de voz no está soportada en este navegador!");
          return;
        }
        let declaracion = new SpeechSynthesisUtterance(txt);
        declaracion.lang = "es-ES"; // Establece el idioma del texto a hablar
        declaracion.pitch = 500;

        sintetizador.speak(declaracion);
    }
};