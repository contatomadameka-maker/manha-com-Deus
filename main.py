from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import anthropic
import json
import os
from pathlib import Path
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

FRONTEND_PATH = Path(__file__).parent / "frontend"

app.mount("/static", StaticFiles(directory=str(FRONTEND_PATH / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_file = FRONTEND_PATH / "index.html"
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Manhã com Deus"}


def build_prompt_modo1(data_formatada: str, dia_ano: int) -> str:
    return f"""Você é o gerador de devocionais do app "Manhã com Deus". Gere um devocional completo, profundo e rico para hoje ({data_formatada}, Dia {dia_ano} do ano).

REGRAS ABSOLUTAS DE QUALIDADE:
- Título forte e CONCEITUAL (3-6 palavras) que revela o argumento, não o assunto. Ex: "O Amor é o Acesso" — não "Ame o Próximo". O título deve instigar curiosidade.
- Reflexão com 5 parágrafos de 3-4 linhas cada, com progressão lógica: [1] ideia provocadora; [2] aprofundamento bíblico; [3] personagem bíblico concreto; [4] aplicação ao cotidiano; [5] conclusão poética com frase de impacto.
- Tom: espiritual e moderno, acolhedor, sem jargão doutrinário excessivo. Alcança quem está começando na fé.
- Oração íntima, específica, na primeira pessoa — não genérica.
- Ação prática concreta e simples para hoje.
- Frase de destaque marcante — a mais poderosa do devocional.
- Para louvor: sugira música gospel brasileira ou internacional alinhada ao tema.

USE EXATAMENTE este formato:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {data_formatada} · Dia {dia_ano} do ano
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✦ [TÍTULO CONCEITUAL AQUI]

📖 VERSÍCULO:
"[Texto completo do versículo]"
— [Livro Capítulo:Versículo]

💭 REFLEXÃO:
[Parágrafo 1 — abre com ideia provocadora]

[Parágrafo 2 — aprofunda o argumento bíblico]

[Parágrafo 3 — ancora em personagem bíblico concreto]

[Parágrafo 4 — aplica ao cotidiano]

[Parágrafo 5 — conclusão com frase de impacto]

✦ "[FRASE DE DESTAQUE — a mais poderosa, para guardar no coração]"

🙏 ORAÇÃO:
[1 parágrafo de oração na primeira pessoa, íntima e específica, 4-5 linhas]

💡 AÇÃO PRÁTICA PARA HOJE:
[1 ação concreta, simples e específica para hoje]

📝 ANOTAÇÕES:
___________
___________
___________
___________

🎵 LOUVOR DO DIA:
[Música + Artista + Link YouTube]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


def build_prompt_modo2(data_formatada: str, dia_ano: int, estado_label: str, estado_icon: str) -> str:
    return f"""Você é o gerador de devocionais do app "Manhã com Deus". O usuário está se sentindo {estado_label.lower()} {estado_icon} hoje.

Gere um devocional COMPLETAMENTE PERSONALIZADO para este estado emocional específico. O devocional deve:
- Falar diretamente com quem está {estado_label.lower()}
- Escolher um versículo que responde diretamente a este estado
- Trazer um personagem bíblico que viveu situação similar
- Oferecer conforto, esperança e direção prática para ESTA emoção específica
- Ser acolhedor, nunca condescendente ou superficial

REGRAS DE QUALIDADE:
- Título conceitual e forte (3-6 palavras) revelando o argumento, não o assunto
- Reflexão com 5 parágrafos profundos com progressão lógica
- Tom: espiritual e moderno, sem jargão excessivo
- Oração adaptada ao estado emocional — íntima e específica
- Ação prática real para quem está neste estado hoje

USE EXATAMENTE este formato:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✦ Gerado para você · Estado: {estado_label}
📅 {data_formatada} · Dia {dia_ano} do ano
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✦ [TÍTULO CONCEITUAL AQUI]

📖 VERSÍCULO:
"[Texto completo do versículo — escolhido especificamente para quem está {estado_label.lower()}]"
— [Livro Capítulo:Versículo]

💭 REFLEXÃO:
[Parágrafo 1 — reconhece o estado emocional sem minimizá-lo]

[Parágrafo 2 — mostra que Deus vê e compreende este sentimento]

[Parágrafo 3 — ancora em personagem bíblico que viveu situação similar]

[Parágrafo 4 — aplica ao cotidiano de quem está {estado_label.lower()} hoje]

[Parágrafo 5 — conclusão com esperança e frase de impacto]

✦ "[FRASE DE DESTAQUE — a mais poderosa para quem está {estado_label.lower()}]"

🙏 ORAÇÃO:
[Oração na primeira pessoa, adaptada para quem está {estado_label.lower()}, íntima, 4-5 linhas]

💡 AÇÃO PRÁTICA PARA HOJE:
[1 ação concreta e específica para quem está {estado_label.lower()} — não genérica]

📝 ANOTAÇÕES:
___________
___________
___________
___________

🎵 LOUVOR DO DIA:
[Música + Artista que fala ao coração de quem está {estado_label.lower()} + Link YouTube]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


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
        prompt = build_prompt_modo1(data_formatada, dia_ano)
    else:
        prompt = build_prompt_modo2(data_formatada, dia_ano, estado_label, estado_icon)

    def stream_generator():
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                chunk = json.dumps({"text": text}, ensure_ascii=False)
                yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
    