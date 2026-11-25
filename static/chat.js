const socket = io();
let miNombre = "", miIdioma = "ES", miPatron = "cubico", miSala = "general";

function entrar() {
  miNombre = document.getElementById("nombre").value.trim() || "Anonimo";
  miSala   = document.getElementById("sala").value.trim()   || "general";
  miIdioma = document.getElementById("idioma").value;
  miPatron = document.getElementById("patron").value;

  socket.emit("entrar", {
    nombre: miNombre, sala: miSala, idioma: miIdioma, patron: miPatron
  });

  document.getElementById("login").classList.add("oculto");
  document.getElementById("chat").classList.remove("oculto");
  document.getElementById("nombreSala").textContent = "#" + miSala;
  document.getElementById("badgePatron").textContent =
    miPatron === "cubico" ? "n³" : miPatron === "cuadratico" ? "n²" : "n";
}

function enviar() {
  const input = document.getElementById("entrada");
  const texto = input.value.trim();
  if (!texto) return;
  socket.emit("mensaje", { texto });
  input.value = "";
}

document.addEventListener("keydown", e => {
  if (e.key === "Enter" && !document.getElementById("chat").classList.contains("oculto")) {
    enviar();
  }
});

socket.on("bienvenida", data => {
  agregarSistema(`Conectado a #${data.sala} · idioma ${data.idioma} · patrón ${data.patron}`);
  if (data.historial && data.historial.length) {
    agregarSistema(`— ${data.historial.length} mensajes en el historial —`);
    data.historial.forEach(pkt => {
      const burbuja = crearBurbuja(pkt.emisor, "…", pkt.numeros.join(" "), "", pkt.emisor === miNombre);
      window._pendientes = window._pendientes || {};
      window._pendientes[pkt.id] = burbuja;
      socket.emit("descifrar_y_traducir", {
        id: pkt.id, numeros: pkt.numeros, patron: pkt.patron,
        idioma_origen: pkt.idioma_origen
      });
    });
  }
});

socket.on("sistema", data => agregarSistema(data.msg));

socket.on("mensaje_cifrado", pkt => {
  const esPropio = pkt.emisor === miNombre;
  const burbuja = crearBurbuja(
    pkt.emisor, "…", pkt.numeros.join(" "), "", esPropio
  );
  window._pendientes = window._pendientes || {};
  window._pendientes[pkt.id] = burbuja;

  socket.emit("descifrar_y_traducir", {
    id: pkt.id, numeros: pkt.numeros, patron: pkt.patron,
    idioma_origen: pkt.idioma_origen
  });
});

socket.on("mensaje_descifrado", data => {
  const burbuja = (window._pendientes && window._pendientes[data.id]) || window._ultimaBurbuja;
  if (!burbuja) return;
  burbuja.querySelector(".texto").textContent = data.texto_recuperado;
  const trad = burbuja.querySelector(".traduccion");
  if (data.traduccion !== data.texto_recuperado) {
    trad.textContent = `→ ${data.idioma_destino}: ${data.traduccion}`;
    trad.style.display = "block";
  }
  if (window._pendientes) delete window._pendientes[data.id];
});

socket.on("error_descifrado", data => agregarSistema("⚠ " + data.msg));

function crearBurbuja(emisor, texto, cifrado, traduccion, propio) {
  const div = document.createElement("div");
  div.className = "msg " + (propio ? "propio" : "ajeno");
  div.innerHTML = `
    <div class="emisor">${emisor}</div>
    <div class="texto">${texto}</div>
    <div class="cifrado">${cifrado}</div>
    <div class="traduccion" style="display:none">${traduccion}</div>
  `;
  document.getElementById("mensajes").appendChild(div);
  document.getElementById("mensajes").scrollTop = 1e9;
  return div;
}

function agregarSistema(txt) {
  const div = document.createElement("div");
  div.className = "msg sistema";
  div.textContent = txt;
  document.getElementById("mensajes").appendChild(div);
  document.getElementById("mensajes").scrollTop = 1e9;
}