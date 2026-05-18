from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import anthropic, json, os
from pathlib import Path
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
FRONTEND_PATH = Path(__file__).parent / "frontend"

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return HTMLResponse(content=(FRONTEND_PATH / "index.html").read_text(encoding="utf-8"))

@app.get("/health")
async def health():
    return {"status": "ok"}

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

REGRAS: Título CONCEITUAL forte (3-6 palavras). Reflexão com 5 parágrafos profundos. Tom espiritual moderno. Oração íntima na primeira pessoa. Ação prática concreta. Frase de destaque marcante.

USE EXATAMENTE este formato:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {data_formatada} · Dia {dia_ano} do ano
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✦ [TÍTULO CONCEITUAL]

📖 VERSÍCULO:
"[versículo completo]"
— [Livro Cap:Ver]

💭 REFLEXÃO:
[parágrafo 1]

[parágrafo 2]

[parágrafo 3]

[parágrafo 4]

[parágrafo 5]

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

Gere devocional PERSONALIZADO para este estado. Versículo específico, personagem bíblico similar, oração adaptada, ação prática para quem está {estado_label.lower()}.

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
[parágrafo 1 — reconhece o estado]

[parágrafo 2 — Deus vê e compreende]

[parágrafo 3 — personagem bíblico similar]

[parágrafo 4 — aplicação prática]

[parágrafo 5 — esperança e impacto]

✦ "[FRASE DE DESTAQUE]"

🙏 ORAÇÃO:
[oração adaptada ao estado, 4-5 linhas]

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
