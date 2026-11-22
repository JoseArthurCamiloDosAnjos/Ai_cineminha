import re
import webbrowser
from urllib.parse import quote_plus
import requests

RESPOSTA_VIDEO = "Abrindo o YouTube"

def abrir_video(texto):
    busca = re.search(r"video(?: de)?(?:\s+(.*))?$", texto)
    termo = (busca.group(1) or "").strip() if busca else ""
    if not termo:
        return "Qual video você quer ver?"
    webbrowser.open("https://www.youtube.com/results?search_query=" + quote_plus(termo))
    return f"Abrindo o YouTube com a pesquisa: {termo}"

def buscar_filme(texto):
    busca = re.search(r"")