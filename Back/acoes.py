import re
import unicodedata
import webbrowser
from urllib.parse import quote_plus

PALAVRAS_VIDEO_FORTE = (
    "video", "videos", "trailer", "trailers", "teaser", "teasers",
)

PALAVRAS_VIDEO_FRACA = (
    "clipe", "clipes", "cena", "cenas", "previa", "bastidores",
    "entrevista", "entrevistas", "making of",
)

PALAVRAS_VIDEO = PALAVRAS_VIDEO_FORTE + PALAVRAS_VIDEO_FRACA

VERBOS_ACAO = (
    "ver", "assistir", "mostra", "mostre", "mostrar", "procure", "procurar",
    "pesquise", "pesquisar", "busque", "buscar", "ache", "achar", "abrir",
    "quero", "mande", "coloque", "roda", "rodar", "toca", "tocar", "youtube",
)

FILLERS_INICIO = (
    "de", "do", "da", "dos", "das", "em", "sobre", "com", "para",
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "esse", "essa", "este", "esta", "isso",
    "desse", "dessa", "deste", "desta",
    "seu", "sua", "seus", "suas",
    "filme", "promocional", "oficial", "completo",
    "dublado", "legendado",
)

FILLERS_FIM = (
    "oficial", "completo", "dublado", "legendado",
    "do youtube", "no youtube", "do cinema",
)

GENEROS_BUSCA = (
    "acao", "comedia", "terror", "romance", "drama", "suspense",
    "animacao", "ficcao cientifica", "fantasia", "aventura", "misterio",
    "documentario", "policial", "guerra", "musical", "faroeste",
    "nacional", "classico", "lancamento",
)

PADRAO_KEYWORD = (
    r"\b(trailers?|teasers?|videos?|clipe|clipes|cenas?|previa|"
    r"bastidores|entrevistas?|making of)\b"
)


def _normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = "".join(c if c.isalnum() or c.isspace() else " " for c in texto)
    return re.sub(r"\s+", " ", texto)


def _remover_fillers(texto, fillers, final=False):
    mudou = True
    while mudou:
        mudou = False
        texto = texto.strip()
        for filler in fillers:
            if " " in filler:
                padrao = re.escape(filler)
            else:
                padrao = r"\b" + re.escape(filler)
            if final:
                novo = re.sub(r"\s+" + padrao + r"$", "", texto)
            else:
                novo = re.sub(r"^" + padrao + r"\s+", "", texto)
            if novo != texto:
                texto = novo
                mudou = True
                break
    if not final and texto in fillers:
        return ""
    return texto.strip()


def detectar_acao_video(texto):
    """True quando o pedido é realmente uma busca de vídeo/trailer.

    Palavras fortes (trailer, video, teaser) sempre disparam a ação;
    palavras fracas (cena, bastidores...) só dislam se houver verbo de ação
    ('quero ver', 'mostre', 'procure'...), evitando gatilhos falsos
    como 'esse filme tem cenas de violência'.
    """
    t = _normalizar(texto)
    if not t:
        return False

    m = re.search(PADRAO_KEYWORD, t)
    if not m:
        return False

    palavra = m.group(1).rstrip("s")
    if palavra in ("trailer", "teaser", "video"):
        return True

    palavras = set(t.split())
    return any(verbo in palavras for verbo in VERBOS_ACAO)


def extrair_termo_video(texto):
    """Extrai a palavra-chave e o termo de busca de pedidos como
    'trailer de Duna', 'video sobre X', 'cenas do filme X'."""
    t = _normalizar(texto)
    if not t:
        return "", ""

    m = re.search(PADRAO_KEYWORD, t)
    if not m:
        return "", ""

    palavra = m.group(1)
    resto = t[m.end():]
    resto = _remover_fillers(resto, FILLERS_INICIO)
    resto = _remover_fillers(resto, FILLERS_FIM, final=True)
    return palavra, resto


def montar_busca(palavra, termo):
    """Monta a query de busca amigável para o YouTube."""
    termo = termo.strip()
    if not termo:
        return ""

    if termo in GENEROS_BUSCA:
        return f"trailer filme {termo}"

    palavras_termo = set(termo.split())
    if palavras_termo & set(PALAVRAS_VIDEO):
        return termo

    if palavra:
        return f"{palavra} {termo}"
    return termo


def abrir_video(texto):
    palavra, termo = extrair_termo_video(texto)
    busca = montar_busca(palavra, termo)

    if not busca:
        return (
            "Qual video você quer ver? Ex.: "
            "\"quero ver o trailer de Duna\" ou \"trailers de ação\""
        )

    url = "https://www.youtube.com/results?search_query=" + quote_plus(busca)
    webbrowser.open(url)
    return f"Abrindo o YouTube com a pesquisa: {busca}"


ACOES = {
    "video": abrir_video,
}
