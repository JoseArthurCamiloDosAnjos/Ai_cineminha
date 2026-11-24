import csv
import re
import requests
import unicodedata
import acoes
import catalogo
import api_filmes
from chatterbot import ChatBot, languages

bot = ChatBot(
    "Assistente",
    database_uri="sqlite:///assistente.sqlite3",
    language=languages.POR,
    # read_only evita que cada pergunta seja gravada no banco, o que
    # poluía o modelo e gerava respostas aleatórias/inconsistentes.
    read_only=True,
    # O BestMatch interrompe a busca no primeiro resultado >= threshold.
    # Com o padrão (0.7) ele pegava um parecido ("quero assistir uma
    # comedia") e ignorava o match exato da intenção. Com 1.0 ele só
    # para em igualdade perfeita e, caso contrário, usa o mais próximo.
    maximum_similarity_threshold=1.0,
)

LIMITE = 0.30

GENEROS_SOLTOS = {
    "terror": "terror",
    "comedia": "comedia",
    "acao": "acao",
    "drama": "drama",
    "romance": "romance",
    "suspense": "suspense",
    "animacao": "animacao",
    "ficcao_cientifica": "ficcao_cientifica",
    "fantasia": "fantasia",
    "aventura": "aventura",
    "misterio": "misterio",
    "documentario": "documentario",
    "policial": "policial",
    "guerra": "guerra",
    "musical": "musical",
    "faroeste": "faroeste",
}

RESPOSTA_PARA_INTENCAO = {}
with open("respostas.csv", encoding="utf-8-sig") as arquivo:
    leitor = csv.DictReader(arquivo)
    for linha in leitor:
        RESPOSTA_PARA_INTENCAO[linha["resposta"]] = linha["intencao"]


def intencao_da_resposta(resposta_template):
    intencao = RESPOSTA_PARA_INTENCAO.get(resposta_template)
    if intencao is not None:
        return intencao
    alvo = preparar_texto(resposta_template)
    for texto, intencao in RESPOSTA_PARA_INTENCAO.items():
        if preparar_texto(texto) == alvo:
            return intencao
    return None

CAMPOS_FILME = {
    "classificacao": "filme_classificacao",
    "elenco": "filme_elenco",
    "genero": "filme_genero",
    "final": "filme_final",
    "estreia": "filme_estreia",
    "disponibilidade": "filme_disponibilidade",
    "onde assistir": "filme_disponibilidade",
    "plataforma": "filme_disponibilidade",
    "assistir": "filme_disponibilidade",
    "disponivel": "filme_disponibilidade",
    "sinopse": "filme_historia",
    "historia": "filme_historia",
    "sobre": "filme_historia",
}


def preparar_texto(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = "".join(c for c in texto if c.isalnum() or c.isspace())
    return texto


STOPWORDS_TITULO = {
    "qual", "quais", "onde", "como", "quando", "para", "por", "que", "este",
    "esta", "esse", "essa", "isso", "desse", "dessa", "deste", "desta",
    "filme", "filmes", "trailer", "video", "indicativa", "posso", "assistir",
    "historia", "sinopse", "elenco", "classificacao", "estreia",
    "disponibilidade", "disponivel", "genero", "final", "sobre", "tempo",
    "duracao", "horas", "hora", "idade", "minima", "significado",
    "plataforma", "plataformas", "e", "do", "da", "de", "em", "o", "a",
    "os", "as", "um", "uma", "meu", "minha", "esse", "essa",
}


def extrair_entidades(pergunta):
    texto = pergunta.lower()
    entidades = {"ator": None, "diretor": None, "titulo": None, "ano": None, "genero": None, "plataforma": None}

    padrao_ator = re.search(r"\b(?:com|ator|atriz|elenco|tem|quer\s+assistir\s+com)\s+(?:o\s+|a\s+|os\s+|as\s+)?([a-záãâêôõç\s]+?)(?:\s+(?:de|dirigido|lancado|ano|em|\?|$)|$)", texto)
    if padrao_ator:
        entidades["ator"] = padrao_ator.group(1).strip()

    padrao_diretor = re.search(r"\b(?:dirigid(?:o|a|os|as)\s+por|diretor|diretora|feita\s+por)\s+(?:o\s+|a\s+)?([a-záãâêôõç\s]+?)(?:\?|$)", texto)
    if padrao_diretor:
        entidades["diretor"] = padrao_diretor.group(1).strip()

    padrao_ano = re.search(r"\b(?:de|em|dos|ano)\s+(\d{4})", texto)
    if padrao_ano:
        entidades["ano"] = padrao_ano.group(1)

    padrao_titulo = re.search(r"\b(?:de|do|da|sobre|sinopse|elenco|classificacao|estreia|disponibilidade|genero|final|historia|qual\s+e|e\s+o|e\s+a)\s+(?:o\s+|a\s+|os\s+|as\s+|do\s+|da\s+)?([a-záãâêôõç0-9\s:]+?)(?:\?|$)", texto)
    if padrao_titulo:
        titulo = padrao_titulo.group(1).strip()
        prefixos = (
            "o ", "a ", "os ", "as ", "do ", "da ", "de ", "historia ", "sinopse ",
            "elenco ", "classificacao ", "estreia ", "disponibilidade ", "genero ",
            "final ", "sobre ", "esse ", "essa ", "este ", "esta ", "desse ", "dessa ",
            "deste ", "desta ", "isso ",
        )
        sufixos = (" filme", " desse", " dessa", " desse filme", " dessa filme", " dele", " dela")
        mudou = True
        while mudou:
            mudou = False
            for pref in prefixos:
                if titulo.startswith(pref):
                    titulo = titulo[len(pref):]
                    mudou = True
            for suf in sufixos:
                if titulo.endswith(suf):
                    titulo = titulo[: -len(suf)]
                    mudou = True
        titulo = titulo.strip()
        palavras_titulo = titulo.split()
        eh_ano = bool(re.fullmatch(r"\d{4}", titulo))
        so_stopwords = bool(palavras_titulo) and all(
            p in STOPWORDS_TITULO for p in palavras_titulo
        )
        if titulo and not eh_ano and not so_stopwords:
            entidades["titulo"] = titulo

    for genero in catalogo.GENEROS_MAP:
        if genero in texto:
            entidades["genero"] = genero
            break

    for plataforma in catalogo.PLATAFORMAS_MAP:
        if plataforma in texto:
            entidades["plataforma"] = catalogo.PLATAFORMAS_MAP[plataforma]
            break

    return entidades


def substituir_placeholders(resposta, entidades):
    if "{ator}" in resposta and entidades.get("ator"):
        resposta = resposta.replace("{ator}", entidades["ator"].title())
    if "{diretor}" in resposta and entidades.get("diretor"):
        resposta = resposta.replace("{diretor}", entidades["diretor"].title())
    if "{ano}" in resposta and entidades.get("ano"):
        resposta = resposta.replace("{ano}", entidades["ano"])
    if "{genero}" in resposta and entidades.get("genero"):
        resposta = resposta.replace("{genero}", entidades["genero"].replace("_", " ").title())
    if "{titulo}" in resposta and entidades.get("titulo"):
        resposta = resposta.replace("{titulo}", entidades["titulo"].title())
    if "{filme1}" in resposta and entidades.get("titulo"):
        resposta = resposta.replace("{filme1}", entidades["titulo"].title())
    return resposta


PERGUNTAS_PLACEHOLDER = (
    ("{filme2}", "E qual é o outro filme que você quer comparar? Ex.: \"comparar Matrix e Interestelar\""),
    ("{filme1}", "Qual filme você quer usar? Ex.: \"sinopse de Interestelar\""),
    ("{titulo}", "Qual é o título do filme?"),
    ("{ator}", "Qual ator ou atriz você quer dizer?"),
    ("{diretor}", "Qual diretor ou diretora você quer dizer?"),
    ("{ano}", "Qual ano você quer pesquisar?"),
    ("{genero}", "Qual gênero você quer dizer?"),
)


def resolver_placeholders(resposta):
    """Se algum placeholder sobrou sem valor, pergunta o dado que falta
    em vez de devolver texto com '{...}' para o usuário."""
    for placeholder, pergunta in PERGUNTAS_PLACEHOLDER:
        if placeholder in resposta:
            return pergunta
    return resposta


def detalhes_por_campo_tmdb(filme, campo):
    if campo == "filme_historia":
        return api_filmes.detalhes_texto(filme)
    if campo == "filme_elenco":
        atores = ", ".join(filme.get("atores", [])) if filme.get("atores") else "Não informado"
        return f"Elenco de **{filme['titulo']}**: {atores}."
    if campo == "filme_classificacao":
        return f"Classificação indicativa de **{filme['titulo']}**: {filme.get('classificacao', 'Não informada')}."
    if campo == "filme_estreia":
        return f"**{filme['titulo']}** estreou em {filme['ano']}."
    if campo == "filme_disponibilidade":
        return f"**{filme['titulo']}** — verifique sua plataforma de streaming preferida."
    if campo == "filme_genero":
        generos = ", ".join(filme.get("generos", [])) if filme.get("generos") else "Não informado"
        return f"**{filme['titulo']}** é do gênero {generos}."
    if campo == "filme_final":
        return f"O final de **{filme['titulo']}** envolve desfechos marcantes. Prefere uma explicação com spoilers?"
    return api_filmes.detalhes_texto(filme)


def detalhes_por_campo_catalogo(filme, campo):
    if campo == "filme_historia":
        return f"{catalogo.detalhes_filme(filme)}\n\nSinopse: {filme['sinopse']}"
    if campo == "filme_elenco":
        atores = ", ".join(filme["atores"])
        return f"Elenco de **{filme['titulo']}**: {atores}."
    if campo == "filme_classificacao":
        return f"Classificação indicativa de **{filme['titulo']}**: {filme['classificacao']}."
    if campo == "filme_estreia":
        return f"**{filme['titulo']}** estreou em {filme['ano']}."
    if campo == "filme_disponibilidade":
        return f"**{filme['titulo']}** está disponível na {filme['plataforma']}."
    if campo == "filme_genero":
        return f"**{filme['titulo']}** é do gênero {filme['genero'].replace('_', ' ').title()}."
    if campo == "filme_final":
        return f"O final de **{filme['titulo']}** envolve desfechos marcantes. Prefere uma explicação com spoilers?"
    return catalogo.detalhes_filme(filme)


def resposta_campo_filme(pergunta):
    texto = pergunta.lower()
    palavras = set(texto.split())

    if api_filmes.API_KEY:
        for campo, intencao in CAMPOS_FILME.items():
            campo_palavras = campo.split()
            if all(p in palavras for p in campo_palavras):
                for f in catalogo.FILMES:
                    if f["titulo"].lower() in texto:
                        tmdb = api_filmes.buscar_por_titulo(f["titulo"])
                        if tmdb:
                            return detalhes_por_campo_tmdb(tmdb, intencao)
                        break

    for f in catalogo.FILMES:
        if f["titulo"].lower() in texto:
            for campo, intencao in CAMPOS_FILME.items():
                campo_palavras = campo.split()
                if all(p in palavras for p in campo_palavras):
                    return detalhes_por_campo_catalogo(f, intencao)
    return None


def _recomendacao_tmdb(intencao, entidades):
    genero = entidades.get("genero")
    ator = entidades.get("ator")
    diretor = entidades.get("diretor")
    ano = entidades.get("ano")
    plataforma = entidades.get("plataforma")

    if intencao == "filme_ator" and ator:
        filmes = api_filmes.buscar_por_ator(ator)
        if filmes:
            return f"Filmes com {ator.title()}: " + api_filmes.formatar_lista(filmes)
        return f"Não encontrei filmes com {ator.title()} na TMDB."

    if intencao == "filme_diretora_diretor" and diretor:
        filmes = api_filmes.buscar_por_diretor(diretor)
        if filmes:
            return f"Filmes dirigidos por {diretor.title()}: " + api_filmes.formatar_lista(filmes)
        return f"Não encontrei filmes dirigidos por {diretor.title()} na TMDB."

    if intencao == "filme_ano" and ano:
        try:
            valor = int(ano)
        except ValueError:
            valor = None
        if valor:
            filmes = api_filmes.buscar_por_ano(valor)
            if filmes:
                return f"Filmes de {valor}: " + api_filmes.formatar_lista(filmes)
            return f"Não encontrei filmes de {valor} na TMDB."

    INTENCOES_GENERO = (
        "filme_comedia", "filme_acao", "filme_terror", "filme_romance", "filme_ficcao_cientifica",
        "filme_drama", "filme_animacao", "filme_fantasia", "filme_aventura", "filme_misterio",
        "filme_documentario", "filme_nacional", "filme_lancamento", "filme_classico",
        "filme_melhor_avaliado", "filme_recomendacao", "filme_suspense", "filme_policial",
        "filme_guerra", "filme_musical", "filme_biografia", "filme_esporte", "filme_faroeste",
        "filme_apocalipse", "filme_vampiro", "filme_dinossauro", "filme_espacial", "filme_familia",
        "filme_crianca", "filme_adolescente", "filme_curta", "filme_trilogia", "filme_sequencia",
        "filme_remake", "filme_premio", "filme_triste", "filme_positivo", "filme_inesperado",
        "filme_pouco_conhecido", "filme_dublado", "filme_legendado",
    )

    if genero and intencao in INTENCOES_GENERO:
        filmes = api_filmes.buscar_por_genero(genero)
        if filmes:
            return api_filmes.formatar_lista(filmes)
        return "Não encontrei filmes desse gênero na TMDB."

    if plataforma:
        populares = api_filmes.buscar_populares()
        filmes = [f for f in populares if plataforma.lower() in f.get("sinopse", "").lower() or True]
        if populares:
            return f"Filmes populares na TMDB (consulte disponibilidade na {plataforma}): " + api_filmes.formatar_lista(populares)
        return f"Não encontrei filmes para a {plataforma} na TMDB."

    INTENCOES_TITULO = ("filme_final", "filme_historia", "filme_elenco", "filme_classificacao", "filme_estreia", "filme_disponibilidade", "filme_genero")

    if entidades.get("titulo") and intencao in INTENCOES_TITULO:
        filme = api_filmes.buscar_por_titulo(entidades["titulo"])
        if filme:
            return detalhes_por_campo_tmdb(filme, intencao)
        return f"Não encontrei o filme '{entidades['titulo']}' na TMDB."

    return None


def resposta_recomendacao(intencao, entidades):
    if api_filmes.API_KEY:
        resultado = _recomendacao_tmdb(intencao, entidades)
        if resultado:
            return resultado

    if intencao == "filme_ator" and entidades.get("ator"):
        ator = entidades["ator"]
        filmes = catalogo.buscar_por_ator(ator)
        if filmes:
            return f"Filmes com {ator.title()}: " + catalogo.formatar_lista(filmes)
        return f"Não encontrei filmes com {ator.title()} no meu catálogo."

    if intencao == "filme_diretora_diretor" and entidades.get("diretor"):
        diretor = entidades["diretor"]
        filmes = catalogo.buscar_por_diretor(diretor)
        if filmes:
            return f"Filmes dirigidos por {diretor.title()}: " + catalogo.formatar_lista(filmes)
        return f"Não encontrei filmes dirigidos por {diretor.title()} no meu catálogo."

    if intencao == "filme_ano" and entidades.get("ano"):
        try:
            valor = int(entidades["ano"])
        except ValueError:
            valor = None
        if valor:
            filmes = catalogo.buscar_por_ano(valor)
            if filmes:
                return f"Filmes de {valor}: " + catalogo.formatar_lista(filmes)
            return f"Não encontrei filmes de {valor} no meu catálogo."

    INTENCOES_GENERO = (
        "filme_comedia", "filme_acao", "filme_terror", "filme_romance", "filme_ficcao_cientifica",
        "filme_drama", "filme_animacao", "filme_fantasia", "filme_aventura", "filme_misterio",
        "filme_documentario", "filme_nacional", "filme_lancamento", "filme_classico",
        "filme_melhor_avaliado", "filme_recomendacao", "filme_suspense", "filme_policial",
        "filme_guerra", "filme_musical", "filme_biografia", "filme_esporte", "filme_faroeste",
        "filme_apocalipse", "filme_vampiro", "filme_dinossauro", "filme_espacial", "filme_familia",
        "filme_crianca", "filme_adolescente", "filme_curta", "filme_trilogia", "filme_sequencia",
        "filme_remake", "filme_premio", "filme_triste", "filme_positivo", "filme_inesperado",
        "filme_pouco_conhecido", "filme_dublado", "filme_legendado",
    )

    genero = entidades.get("genero")
    if genero and intencao in INTENCOES_GENERO:
        filmes = catalogo.buscar_por_genero(genero)
        if filmes:
            return catalogo.formatar_lista(filmes)
        return "Não encontrei filmes desse gênero no meu catálogo."

    if entidades.get("plataforma"):
        plataforma = entidades["plataforma"]
        filmes = [f for f in catalogo.FILMES if f["plataforma"] == plataforma]
        if filmes:
            return f"Filmes disponíveis na {plataforma}: " + catalogo.formatar_lista(filmes)
        return f"Não encontrei filmes na {plataforma} no meu catálogo."

    INTENCOES_TITULO = ("filme_final", "filme_historia", "filme_elenco", "filme_classificacao", "filme_estreia", "filme_disponibilidade", "filme_genero")

    if entidades.get("titulo") and intencao in INTENCOES_TITULO:
        filme = catalogo.buscar_por_titulo(entidades["titulo"])
        if filme:
            return detalhes_por_campo_catalogo(filme, intencao)
        return f"Não encontrei o filme '{entidades['titulo']}' no meu catálogo."

    return None


def pesquisar(pergunta, confianca):
    try:
        resposta = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": pergunta,
                "format": "json",
                "no_html": 1,
                "kl": "br-pt",
                "kad": "pt_BR",
            },
            timeout=10,
        )
        dados = resposta.json()
        texto = dados.get("AbstractText") or dados.get("Answer") or ""
        if not texto:
            for topico in dados.get("RelatedTopics", []):
                if isinstance(topico, dict) and topico.get("Text"):
                    texto = topico["Text"]
                    break
        if texto:
            return texto
    except Exception:
        pass
    return (
        "Não tenho certeza sobre isso. Posso recomendar filmes, procurar "
        "trailers e dar informações de cinema. Tente algo como "
        "\"me indique um filme de comedia\" ou \"quero ver o trailer de Duna\"."
    )


def registrar(pergunta, confianca, resposta):
    with open("historico.csv", "a", encoding="utf-8", newline="") as arquivo:
        csv.writer(arquivo).writerow([pergunta, confianca, resposta])


def resposta_genero_solto(pergunta):
    texto = pergunta.lower().strip()
    palavras = set(texto.split())
    for genero in GENEROS_SOLTOS:
        if genero in palavras:
            if api_filmes.API_KEY:
                filmes = api_filmes.buscar_por_genero(genero)
                if filmes:
                    return api_filmes.formatar_lista(filmes)
            filmes = catalogo.buscar_por_genero(genero)
            if filmes:
                return catalogo.formatar_lista(filmes)
    return None


def resposta_acao_video(pergunta_limpa):
    """Detecta pedidos explícitos de vídeo/trailer (ex.: 'quero ver o
    trailer de Duna', 'video de terror') e dispara a ação correspondente."""
    if acoes.detectar_acao_video(pergunta_limpa):
        return acoes.abrir_video(pergunta_limpa)
    return None


def pipeline(pergunta):
    pergunta_limpa = preparar_texto(pergunta)

    acao_video = resposta_acao_video(pergunta_limpa)
    if acao_video:
        return acao_video

    campo = resposta_campo_filme(pergunta_limpa)
    if campo:
        return campo

    genero = resposta_genero_solto(pergunta_limpa)
    if genero:
        return genero

    resultado = bot.get_response(pergunta_limpa)

    if resultado.confidence >= LIMITE:
        resposta_template = resultado.text
        intencao = intencao_da_resposta(resposta_template)

        if intencao is None:
            resposta = pesquisar(pergunta_limpa, resultado.confidence)
            registrar(pergunta_limpa, resultado.confidence, resposta)
            return resposta

        acao = acoes.ACOES.get(intencao)
        if acao:
            return acao(pergunta)

        entidades = extrair_entidades(pergunta_limpa)

        recomendacao = resposta_recomendacao(intencao, entidades)
        if recomendacao:
            return recomendacao

        resposta_final = substituir_placeholders(resposta_template, entidades)
        return resolver_placeholders(resposta_final)

    resposta = pesquisar(pergunta_limpa, resultado.confidence)
    registrar(pergunta_limpa, resultado.confidence, resposta)
    return resposta


if __name__ == "__main__":
    while True:
        pergunta = input("Você: ")
        if pergunta.lower() == "sair":
            break
        print(f"Assistente: {pipeline(pergunta)}")
