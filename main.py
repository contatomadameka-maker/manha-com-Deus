from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import anthropic, json, os, httpx
from pathlib import Path
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
FRONTEND_PATH = Path(__file__).parent / "frontend"

# Versículos curados por dia do ano (30 versículos rotativos)
VERSICULOS = [
    {"texto": "Porque sou eu que conheço os planos que tenho para vocês, planos de fazê-los prosperar e não de causar dano, planos de dar a vocês esperança e um futuro.", "ref": "Jeremias 29:11"},
    {"texto": "O Senhor é o meu pastor e nada me faltará.", "ref": "Salmos 23:1"},
    {"texto": "Tudo posso naquele que me fortalece.", "ref": "Filipenses 4:13"},
    {"texto": "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna.", "ref": "João 3:16"},
    {"texto": "Confie no Senhor de todo o seu coração e não se apoie em seu próprio entendimento.", "ref": "Provérbios 3:5"},
    {"texto": "Mas os que esperam no Senhor renovarão as suas forças. Voarão alto como águias.", "ref": "Isaías 40:31"},
    {"texto": "Não temas, porque eu sou contigo; não te assombres, porque eu sou teu Deus.", "ref": "Isaías 41:10"},
    {"texto": "Busquem, pois, em primeiro lugar o Reino de Deus e a sua justiça, e todas estas coisas lhes serão acrescentadas.", "ref": "Mateus 6:33"},
    {"texto": "O amor é paciente, o amor é bondoso. Não inveja, não se vangloria, não se orgulha.", "ref": "1 Coríntios 13:4"},
    {"texto": "Posso fazer tudo isso por meio daquele que me fortalece.", "ref": "Filipenses 4:13"},
    {"texto": "Lançando sobre ele toda a vossa ansiedade, porque ele tem cuidado de vós.", "ref": "1 Pedro 5:7"},
    {"texto": "O Senhor é a minha luz e a minha salvação; a quem temerei?", "ref": "Salmos 27:1"},
    {"texto": "Alegrai-vos sempre no Senhor. Outra vez digo: Alegrai-vos!", "ref": "Filipenses 4:4"},
    {"texto": "Sede fortes e corajosos. Não temais nem vos assusteis, porque o Senhor, nosso Deus, é quem vai convosco.", "ref": "Deuteronômio 31:6"},
    {"texto": "A fé é a certeza daquilo que esperamos e a prova das coisas que não vemos.", "ref": "Hebreus 11:1"},
    {"texto": "Deus é o nosso refúgio e a nossa força, socorro bem presente nas tribulações.", "ref": "Salmos 46:1"},
    {"texto": "Porque eu sei os planos que tenho para você, diz o Senhor, planos de paz e não de mal.", "ref": "Jeremias 29:11"},
    {"texto": "A graça do Senhor Jesus seja com todos vocês.", "ref": "Apocalipse 22:21"},
    {"texto": "Bem-aventurados os misericordiosos, porque eles alcançarão misericórdia.", "ref": "Mateus 5:7"},
    {"texto": "O Senhor te guardará de todo o mal; ele guardará a tua alma.", "ref": "Salmos 121:7"},
    {"texto": "Porque onde estiverem dois ou três reunidos em meu nome, ali estou no meio deles.", "ref": "Mateus 18:20"},
    {"texto": "Não vos conformeis com este século, mas transformai-vos pela renovação da vossa mente.", "ref": "Romanos 12:2"},
    {"texto": "Aquele que habita no esconderijo do Altíssimo, à sombra do Onipotente descansará.", "ref": "Salmos 91:1"},
    {"texto": "Mas eu, pela tua grande misericórdia, entrarei em tua casa.", "ref": "Salmos 5:7"},
    {"texto": "O Senhor é bom, um forte refúgio no dia da angústia.", "ref": "Naum 1:7"},
    {"texto": "Cria em mim, ó Deus, um coração puro, e renova dentro de mim um espírito firme.", "ref": "Salmos 51:10"},
    {"texto": "Vinde a mim, todos os que estais cansados e sobrecarregados, e eu vos aliviarei.", "ref": "Mateus 11:28"},
    {"texto": "O amor nunca falha.", "ref": "1 Coríntios 13:8"},
    {"texto": "Tudo tem o seu tempo determinado, há tempo para todo propósito debaixo do céu.", "ref": "Eclesiastes 3:1"},
    {"texto": "E conhecereis a verdade, e a verdade vos libertará.", "ref": "João 8:32"},
]

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return HTMLResponse(content=(FRONTEND_PATH / "index.html").read_text(encoding="utf-8"))

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/versiculo-do-dia")
async def versiculo_do_dia():
    dia = datetime.now().timetuple().tm_yday
    versiculo = VERSICULOS[dia % len(VERSICULOS)]
    return {
        "texto": versiculo["texto"],
        "ref": versiculo["ref"],
        "data": datetime.now().strftime("%A, %d de %B de %Y").capitalize(),
        "dia": dia
    }

@app.post("/devocional")
async def gerar_devocional(request: Request):
    body = await request.json()
    modo = body.get("modo", 1)
    estado_label = body.get("estado_label", "")
    estado_icon = body.get("estado_icon", "")
    agora = datetime.now()
    data_formatada = agora.strftime("%A, %d de %B de %Y").capitalize()
    dia_ano = agora.timetuple().tm_yday

    if modo == 1:
        prompt = f"""Você é o gerador de devocionais do app "Manhã com Deus". Gere um devocional completo e profundo para hoje ({data_formatada}, Dia {dia_ano} do ano).

REGRAS: Título CONCEITUAL forte (3-6 palavras, revela o argumento não o assunto). Reflexão com 5 parágrafos profundos. Tom espiritual moderno e acolhedor. Oração íntima na primeira pessoa. Ação prática concreta. Frase de destaque marcante.

USE EXATAMENTE este formato:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {data_formatada} · Dia {dia_ano} do ano
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✦ [TÍTULO CONCEITUAL]

📖 VERSÍCULO:
"[versículo completo]"
— [Livro Cap:Ver]

💭 REFLEXÃO:
[parágrafo 1 — ideia provocadora]

[parágrafo 2 — aprofundamento bíblico]

[parágrafo 3 — personagem bíblico concreto]

[parágrafo 4 — aplicação ao cotidiano]

[parágrafo 5 — conclusão poética]

✦ "[FRASE DE DESTAQUE]"

🙏 ORAÇÃO:
[oração íntima 4-5 linhas]

💡 AÇÃO PRÁTICA PARA HOJE:
[ação concreta]

📝 ANOTAÇÕES:
___________
___________
___________

🎵 LOUVOR DO DIA:
[Música + Artista + Link YouTube]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    else:
        prompt = f"""Você é o gerador de devocionais do app "Manhã com Deus". O usuário está se sentindo {estado_label.lower()} {estado_icon} hoje.

Gere devocional PERSONALIZADO para este estado emocional. Versículo específico para quem está {estado_label.lower()}, personagem bíblico que viveu situação similar, oração adaptada, ação prática específica.

USE EXATAMENTE este formato:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✦ Gerado para você · Estado: {estado_label}
📅 {data_formatada} · Dia {dia_ano} do ano
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✦ [TÍTULO CONCEITUAL]

📖 VERSÍCULO:
"[versículo para quem está {estado_label.lower()}]"
— [Livro Cap:Ver]

💭 REFLEXÃO:
[parágrafo 1 — reconhece o estado sem minimizar]

[parágrafo 2 — Deus vê e compreende]

[parágrafo 3 — personagem bíblico similar]

[parágrafo 4 — aplicação para quem está {estado_label.lower()}]

[parágrafo 5 — esperança e frase de impacto]

✦ "[FRASE DE DESTAQUE]"

🙏 ORAÇÃO:
[oração adaptada ao estado {estado_label.lower()}, 4-5 linhas]

💡 AÇÃO PRÁTICA PARA HOJE:
[ação específica para quem está {estado_label.lower()}]

📝 ANOTAÇÕES:
___________
___________
___________

🎵 LOUVOR DO DIA:
[Música + Artista + Link YouTube]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    def stream_generator():
        with client.messages.stream(model="claude-sonnet-4-20250514", max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


from fastapi.responses import FileResponse

@app.get("/manifest.json")
async def manifest():
    return FileResponse(str(FRONTEND_PATH / "manifest.json"), media_type="application/manifest+json")

@app.get("/sw.js")
async def service_worker():
    return FileResponse(str(FRONTEND_PATH / "sw.js"), media_type="application/javascript")

@app.get("/icon-192.png")
async def icon192():
    p = FRONTEND_PATH / "icon-192.png"
    if p.exists(): return FileResponse(str(p), media_type="image/png")
    return FileResponse(str(FRONTEND_PATH / "icon.svg"), media_type="image/svg+xml")

@app.get("/icon-512.png")  
async def icon512():
    p = FRONTEND_PATH / "icon-512.png"
    if p.exists(): return FileResponse(str(p), media_type="image/png")
    return FileResponse(str(FRONTEND_PATH / "icon.svg"), media_type="image/svg+xml")


@app.get("/install-imgs/{filename}")
async def install_imgs(filename: str):
    from fastapi.responses import FileResponse
    p = FRONTEND_PATH / "install-imgs" / filename
    if p.exists():
        return FileResponse(str(p))
    return {"error": "not found"}
