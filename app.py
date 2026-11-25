# ==================================================
# IAMD CHAT — Servidor Flask + SocketIO (Preparado para la nube)
# ==================================================
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from iamd_core import AlfabetoNumerico, TraductorNumerico
import database as db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("IAMD_SECRET", "iamd-secreto")

# async_mode="threading" es vital para que los mensajes viajen bien en local y en la nube
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

db.init_db()

ALFABETOS = {
    "cubico":     AlfabetoNumerico("cubico"),
    "lineal":     AlfabetoNumerico("lineal"),
    "cuadratico": AlfabetoNumerico("cuadratico"),
}
TRADUCTOR = TraductorNumerico(ALFABETOS["cubico"])

USUARIOS = {}


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.route("/api/historial/<sala>")
def api_historial(sala):
    desde = int(request.args.get("desde", 0))
    msgs = db.historial_sala(sala, limite=100, desde_id=desde)
    return jsonify({"mensajes": msgs, "total": db.contar_mensajes(sala)})


@app.route("/api/tabla/<patron>")
def api_tabla(patron):
    alf = ALFABETOS.get(patron, ALFABETOS["cubico"])
    return jsonify({
        "patron": patron,
        "letra_a_num": list(alf.letra_a_num.items()),
        "univoco": alf.demostrar_univocidad(),
    })


@socketio.on("entrar")
def entrar(data):
    nombre = (data.get("nombre") or "Anonimo").strip()[:24]
    sala   = (data.get("sala") or "general").strip()[:24]
    idioma = (data.get("idioma") or "ES").upper()
    patron = data.get("patron") or "cubico"

    USUARIOS[request.sid] = {
        "nombre": nombre, "sala": sala, "idioma": idioma, "patron": patron
    }
    db.registrar_usuario(nombre, sala, idioma, patron)
    join_room(sala)

    historial = db.historial_sala(sala, limite=50)
    emit("bienvenida", {
        "sala": sala, "idioma": idioma, "patron": patron,
        "historial": historial,
    })
    emit("sistema", {"msg": f"{nombre} se ha unido a #{sala}"}, to=sala)


@socketio.on("mensaje")
def mensaje(data):
    info = USUARIOS.get(request.sid)
    if not info:
        return
    texto = (data.get("texto") or "").strip()
    if not texto:
        return

    alfabeto = ALFABETOS.get(info["patron"], ALFABETOS["cubico"])
    numeros = alfabeto.codificar_frase(texto)
    if not numeros:
        emit("error_descifrado",
             {"msg": "El texto no contiene letras codificables"})
        return

    msg_id = db.guardar_mensaje(
        sala=info["sala"], emisor=info["nombre"],
        idioma_origen=info["idioma"], patron=info["patron"],
        numeros=numeros,
    )
    db.actualizar_visto(info["nombre"], info["sala"])

    paquete = {
        "id": msg_id,
        "emisor": info["nombre"],
        "sala": info["sala"],
        "idioma_origen": info["idioma"],
        "patron": info["patron"],
        "numeros": numeros,
    }
    emit("mensaje_cifrado", paquete, to=info["sala"])


@socketio.on("descifrar_y_traducir")
def descifrar_y_traducir(data):
    info = USUARIOS.get(request.sid)
    if not info:
        return
    msg_id = data.get("id")
    numeros = data.get("numeros") or []
    patron = data.get("patron", "cubico")
    idioma_origen = data.get("idioma_origen", "ES")
    idioma_destino = info["idioma"]

    if msg_id:
        cache = db.obtener_traduccion(msg_id, idioma_destino)
        if cache:
            emit("mensaje_descifrado", {
                "id": msg_id,
                "numeros": numeros,
                "texto_recuperado": cache,
                "traduccion": cache,
                "idioma_destino": idioma_destino,
                "cache": True,
            })
            return

    alfabeto = ALFABETOS.get(patron, ALFABETOS["cubico"])
    texto = alfabeto.decodificar_frase(numeros)
    if texto is None:
        emit("error_descifrado", {"msg": "Secuencia no decodificable"})
        return

    if idioma_origen == idioma_destino:
        traduccion = texto
    else:
        # AQUÍ ESTÁ EL CAMBIO: Usamos traducir_auto (Google Translate) en vez del diccionario
        traduccion = TRADUCTOR.traducir_auto(texto, origen=idioma_origen, destino=idioma_destino)

    if msg_id:
        db.guardar_traduccion(msg_id, idioma_destino, traduccion)

    emit("mensaje_descifrado", {
        "id": msg_id,
        "numeros": numeros,
        "texto_recuperado": texto,
        "traduccion": traduccion,
        "idioma_destino": idioma_destino,
        "univoco": all(
            alfabeto.decodificar_numero(n) is not None
            for n in numeros if n != alfabeto.SEPARADOR_PALABRA
        ),
        "cache": False,
    })


@socketio.on("disconnect")
def desconectar():
    info = USUARIOS.pop(request.sid, None)
    if info:
        emit("sistema", {"msg": f"{info['nombre']} salió"}, to=info["sala"])


# ==================================================
# CONFIGURACIÓN DE ARRANQUE (Local y Nube)
# ==================================================
if __name__ == "__main__":
    # Render asigna un puerto dinámico a través de la variable PORT.
    port = int(os.environ.get("PORT", 5000))
    
    print("=" * 60)
    print(f"  IAMD CHAT — Servidor iniciado en el puerto {port}")
    print("=" * 60)
    
    # debug=False es IMPORTANTE para producción (Render)
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)