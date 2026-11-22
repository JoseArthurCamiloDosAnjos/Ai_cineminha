import csv
from chatterbot import ChatBot, languages
from chatterbot.trainers import ListTrainer

bot = ChatBot("Cineminha", database_uri="sqlite:///assistente.sqlite3", language=languages.POR)

treinador = ListTrainer(bot)

with open("intencoes.csv", encoding="utf-8-sig") as arquivo:
    leitor = csv.DictReader(arquivo)
    perguntas = {}
    for linha in leitor:
        intencao = linha["intencao"]
        pergunta = linha["pergunta"]
        if intencao not in perguntas:
            perguntas[intencao] = []
        perguntas[intencao].append(pergunta)

with open("respostas.csv", encoding="utf-8-sig") as arquivo:
    leitor = csv.DictReader(arquivo)
    respostas = {}
    for linha in leitor:
        intencao = linha["intencao"]
        resposta = linha["resposta"]
        if intencao not in respostas:
            respostas[intencao] = []
        respostas[intencao].append(resposta)

for intencao in perguntas:
    for pergunta in perguntas[intencao]:
        for resposta in respostas.get(intencao, []):
            treinador.train([pergunta, resposta])

print("Treinamento concluído.")
