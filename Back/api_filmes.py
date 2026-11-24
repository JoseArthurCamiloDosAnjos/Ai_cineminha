import os
import requests


def _carregar_env():
    variaveis = {}
    caminho = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                variaveis[chave.strip()] = valor.strip()
    return variaveis


_ENV = _carregar_env()
API_KEY = _ENV.get("TMDB_API_KEY") or os.getenv("TMDB_API_KEY")
BASE_URL = _ENV.get("TMDB_BASE_URL") or os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
IMAGE_BASE = _ENV.get("TMDB_IMAGE_BASE") or os.getenv("TMDB_IMAGE_BASE", "https://image.tmdb.org/t/p/w500")
LANGUAGE = _ENV.get("TMDB_LANGUAGE") or os.getenv("TMDB_LANGUAGE", "pt-BR")

TIMEOUT = 10


def _get(endpoint, params=None):
    if not API_KEY:
        return None
    parametros = {"api_key": API_KEY, "language": LANGUAGE}
    if params:
        parametros.update(params)
    try:
        resposta = requests.get(f"{BASE_URL}{endpoint}", params=parametros, timeout=TIMEOUT)
        if resposta.status_code != 200:
            return None
        return resposta.json()
    except Exception:
        return None


GENEROS_TMDB = {
    "acao": 28,
    "comedia": 35,
    "terror": 27,
    "romance": 10749,
    "ficcao_cientifica": 878,
    "drama": 18,
    "animacao": 16,
    "fantasia": 14,
    "aventura": 12,
    "misterio": 9648,
    "documentario": 99,
    "suspense": 53,
    "policial": 80,
    "guerra": 10752,
    "musical": 10402,
    "faroeste": 37,
}


def _buscar_pessoa(nome):
    dados = _get("/search/person", {"query": nome})
    if not dados or not dados.get("results"):
        return None
    return dados["results"][0]


def buscar_por_genero(genero, limite=8):
    chave = genero.lower().strip()
    genero_id = GENEROS_TMDB.get(chave)
    if not genero_id:
        return []
    dados = _get("/discover/movie", {
        "with_genres": genero_id,
        "sort_by": "popularity.desc",
        "page": 1,
    })
    if not dados or not dados.get("results"):
        return []
    return [formatar_filme(f) for f in dados["results"][:limite]]


def buscar_por_ator(ator, limite=8):
    pessoa = _buscar_pessoa(ator)
    if not pessoa:
        return []
    dados = _get("/discover/movie", {
        "with_cast": str(pessoa["id"]),
        "sort_by": "popularity.desc",
        "page": 1,
    })
    if not dados or not dados.get("results"):
        return []
    return [formatar_filme(f) for f in dados["results"][:limite]]


def buscar_por_diretor(diretor, limite=8):
    pessoa = _buscar_pessoa(diretor)
    if not pessoa:
        return []
    dados = _get("/discover/movie", {
        "with_crew": str(pessoa["id"]),
        "sort_by": "popularity.desc",
        "page": 1,
    })
    if not dados or not dados.get("results"):
        return []
    return [formatar_filme(f) for f in dados["results"][:limite]]


def buscar_por_ano(ano, limite=8):
    try:
        valor = int(ano)
    except (ValueError, TypeError):
        return []
    dados = _get("/discover/movie", {
        "primary_release_year": str(valor),
        "sort_by": "popularity.desc",
        "page": 1,
    })
    if not dados or not dados.get("results"):
        return []
    return [formatar_filme(f) for f in dados["results"][:limite]]


def buscar_por_titulo(titulo):
    dados = _get("/search/movie", {"query": titulo})
    if not dados or not dados.get("results"):
        return None
    resultado = dados["results"][0]
    return detalhes_filme(resultado["id"])


def detalhes_filme(filme_id):
    dados = _get(f"/movie/{filme_id}")
    if not dados:
        return None
    return formatar_filme_detalhado(dados)


def buscar_populares(limite=8):
    dados = _get("/movie/popular", {"page": 1})
    if not dados or not dados.get("results"):
        return []
    return [formatar_filme(f) for f in dados["results"][:limite]]


def formatar_filme(f):
    return {
        "titulo": f.get("title", "Sem título"),
        "ano": (f.get("release_date") or "")[:4] or "Desconhecido",
        "nota": f.get("vote_average", 0),
        "sinopse": f.get("overview") or "Sem sinopse disponível.",
        "poster": f"{IMAGE_BASE}{f['poster_path']}" if f.get("poster_path") else None,
        "generos": [g["name"] for g in f.get("genres", [])],
    }


def formatar_filme_detalhado(dados):
    generos = [g["name"] for g in dados.get("genres", [])]
    atores = []
    creditos = _get(f"/movie/{dados['id']}/credits")
    if creditos and creditos.get("cast"):
        atores = [c["name"] for c in creditos["cast"][:5]]
    diretor = ""
    if creditos and creditos.get("crew"):
        for c in creditos["crew"]:
            if c.get("job") == "Director":
                diretor = c["name"]
                break
    return {
        "titulo": dados.get("title", "Sem título"),
        "ano": (dados.get("release_date") or "")[:4] or "Desconhecido",
        "nota": dados.get("vote_average", 0),
        "sinopse": dados.get("overview") or "Sem sinopse disponível.",
        "poster": f"{IMAGE_BASE}{dados['poster_path']}" if dados.get("poster_path") else None,
        "generos": generos,
        "diretor": diretor or "Não informado",
        "atores": atores,
        "classificacao": dados.get("certification") or "Não informada",
        "duracao": dados.get("runtime") or "Não informada",
    }


def formatar_lista(filmes, limite=5):
    if not filmes:
        return "Não encontrei filmes nessa categoria."
    nomes = [f["titulo"] for f in filmes[:limite]]
    return "Sugestões: " + ", ".join(nomes) + "."


def detalhes_texto(filme):
    atores = ", ".join(filme.get("atores", [])) if filme.get("atores") else ""
    generos = ", ".join(filme.get("generos", [])) if filme.get("generos") else ""
    texto = (
        f"**{filme['titulo']}** ({filme['ano']})\n"
        f"Nota: {filme.get('nota', 'N/A')}/10\n"
    )
    if generos:
        texto += f"Gênero: {generos}\n"
    if filme.get("diretor"):
        texto += f"Diretor: {filme['diretor']}\n"
    if atores:
        texto += f"Elenco: {atores}\n"
    texto += f"\n{filme['sinopse']}"
    return texto
