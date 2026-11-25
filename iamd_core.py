# ==================================================
# IAMD CORE — M11, M12, M13 (recortado para chat)
# ==================================================
from fractions import Fraction


class AlfabetoNumerico:
    LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    SEPARADOR_PALABRA = 0
    SEPARADOR_FRASE = -1
    NORMALIZACION = {
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "Ü": "U", "Ñ": "N", "À": "A", "È": "E", "Ì": "I",
        "Ò": "O", "Ù": "U", "Â": "A", "Ê": "E", "Ô": "O",
    }

    def __init__(self, patron="cubico"):
        self.patron = patron
        self._construir_tabla()

    def _f(self, n):
        if self.patron == "lineal":      return n
        if self.patron == "cuadratico":  return n * n
        if self.patron == "cubico":      return n * n * n
        if self.patron == "primos":      return self._primo(n)
        return n

    def _primo(self, n):
        count, num = 0, 1
        while count < n:
            num += 1
            if all(num % i != 0 for i in range(2, int(num**0.5) + 1)):
                count += 1
        return num

    def _construir_tabla(self):
        self.letra_a_num = {}
        self.num_a_letra = {}
        for i, letra in enumerate(self.LETRAS, start=1):
            v = self._f(i)
            self.letra_a_num[letra] = v
            self.num_a_letra[v] = letra

    def _normalizar(self, letra):
        letra = letra.upper()
        return self.NORMALIZACION.get(letra, letra)

    def codificar_letra(self, letra):
        return self.letra_a_num.get(self._normalizar(letra))

    def decodificar_numero(self, numero):
        return self.num_a_letra.get(numero)

    def codificar_palabra(self, palabra):
        out = []
        for l in palabra.upper():
            l = self._normalizar(l)
            if l in self.letra_a_num:
                out.append(self.letra_a_num[l])
        return out

    def decodificar_palabra(self, numeros):
        letras = [self.decodificar_numero(n) for n in numeros]
        if any(l is None for l in letras):
            return None
        return "".join(letras)

    def codificar_frase(self, frase):
        palabras = [p for p in frase.upper().split() if p]
        resultado = []
        for i, palabra in enumerate(palabras):
            resultado.extend(self.codificar_palabra(palabra))
            if i < len(palabras) - 1:
                resultado.append(self.SEPARADOR_PALABRA)
        return resultado

    def decodificar_frase(self, numeros):
        palabras, actual = [], []
        for n in numeros:
            if n == self.SEPARADOR_PALABRA:
                if actual:
                    palabras.append(self.decodificar_palabra(actual))
                    actual = []
            else:
                actual.append(n)
        if actual:
            palabras.append(self.decodificar_palabra(actual))
        if any(p is None for p in palabras):
            return None
        return " ".join(palabras)

    def demostrar_univocidad(self):
        valores = sorted(self.num_a_letra.keys())
        for i, a in enumerate(valores):
            for b in valores[i+1:]:
                if str(b).startswith(str(a)):
                    return False
        return True


class TraductorNumerico:
    DICCIONARIO = {
        "ES": {
            "YO": "I", "TU": "YOU", "EL": "HE", "ELLA": "SHE",
            "AMO": "LOVE", "AMA": "LOVES", "PERRO": "DOG", "GATO": "CAT",
            "CASA": "HOUSE", "AGUA": "WATER", "FUEGO": "FIRE",
            "TIERRA": "EARTH", "AIRE": "AIR", "HOLA": "HELLO",
            "MUNDO": "WORLD", "PAZ": "PEACE", "AMOR": "LOVE",
            "VIDA": "LIFE", "LUZ": "LIGHT", "SOL": "SUN", "LUNA": "MOON",
            "MI": "MY", "A": "TO", "BUENOS": "GOOD", "DIAS": "DAYS",
            "NOCHES": "NIGHTS", "COMO": "HOW", "ESTAS": "ARE",
            "GRACIAS": "THANKS", "ADIOS": "BYE", "SI": "YES",
            "BIEN": "WELL", "MAL": "BAD", "AMIGO": "FRIEND",
            "FAMILIA": "FAMILY", "TRABAJO": "WORK", "TIEMPO": "TIME",
            "COMER": "EAT", "BEBER": "DRINK", "DORMIR": "SLEEP",
        },
        "EN": {},
        "FR": {
            "YO": "JE", "TU": "TU", "AMOR": "AMOUR", "PERRO": "CHIEN",
            "GATO": "CHAT", "CASA": "MAISON", "AGUA": "EAU",
            "MUNDO": "MONDE", "PAZ": "PAIX", "VIDA": "VIE",
            "LUZ": "LUMIERE", "SOL": "SOLEIL", "LUNA": "LUNE",
            "HOLA": "BONJOUR", "GRACIAS": "MERCI", "ADIOS": "AU REVOIR",
        },
        "IT": {
            "YO": "IO", "AMOR": "AMORE", "PERRO": "CANE",
            "GATO": "GATTO", "CASA": "CASA", "AGUA": "ACQUA",
            "MUNDO": "MONDO", "PAZ": "PACE", "VIDA": "VITA",
            "LUZ": "LUCE", "SOL": "SOLE", "LUNA": "LUNA",
            "HOLA": "CIAO", "GRACIAS": "GRAZIE", "ADIOS": "ADDIO",
        },
        "DE": {
            "YO": "ICH", "AMOR": "LIEBE", "PERRO": "HUND",
            "GATO": "KATZE", "CASA": "HAUS", "AGUA": "WASSER",
            "MUNDO": "WELT", "PAZ": "FRIEDEN", "VIDA": "LEBEN",
            "LUZ": "LICHT", "SOL": "SONNE", "LUNA": "MOND",
            "HOLA": "HALLO", "GRACIAS": "DANKE", "ADIOS": "TSCHUSS",
        },
    }

    def __init__(self, alfabeto):
        self.alfabeto = alfabeto
        self._construir_inverso()

    def _construir_inverso(self):
        self.DICCIONARIO["EN"] = {v: k for k, v in self.DICCIONARIO["ES"].items()}

    def texto_a_numeros(self, texto):
        return self.alfabeto.codificar_frase(texto)

    def numeros_a_texto(self, numeros):
        return self.alfabeto.decodificar_frase(numeros)

    def traducir_a_idioma(self, texto_es, destino):
        if destino == "EN":
            return " ".join(
                self.DICCIONARIO["ES"].get(p.upper(), p)
                for p in texto_es.split()
            )
        dicc = self.DICCIONARIO.get(destino, {})
        return " ".join(dicc.get(p.upper(), p) for p in texto_es.split())