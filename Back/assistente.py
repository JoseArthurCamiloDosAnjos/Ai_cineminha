import csv
import requests
import unicodedata
import acoes
from chatterbot import ChatBot, languages

bot = ChatBot("Assistente", database_uri="sqlite:///assistente.sqlite3", language=languages.POR)

LIMITE = 0.40


def preparar_texto(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = "".join(c for c in texto if c.isalnum() or c.isspace())
    return texto


def pesquisar(pergunta, confianca):
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
    return dados.get("AbstractText") or f"Não encontrei uma resposta. {confianca}"


def registrar(pergunta, confianca, resposta):
    with open("historico.csv", "a", encoding="utf-8", newline="") as arquivo:
        csv.writer(arquivo).writerow([pergunta, confianca, resposta])


def pipeline(pergunta):
    pergunta = preparar_texto(pergunta)
    resultado = bot.get_response(pergunta)
    if resultado.confidence >= LIMITE:
        if resultado.text == acoes.RESPOSTA_VIDEO:
            return acoes.abrir_video(pergunta)
        return resultado.text
    resposta = pesquisar(pergunta, resultado.confidence)
    registrar(pergunta, resultado.confidence, resposta)
    return resposta


if __name__ == "__main__":
    while True:
        pergunta = input("Você: ")
        if pergunta.lower() == "sair":
            break
        print(f"Assistente: {pipeline(pergunta)}")