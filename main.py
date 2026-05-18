from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import anthropic, json, os, asyncio
from pathlib import Path
from datetime import datetime
import httpx

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ttcdhthjtdnudczakuhu.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
FRONTEND_PATH = Path(__file__).parent / "frontend"

VERSICULOS = [
    {"texto": "Porque sou eu que conheço os planos que tenho para vocês, planos de fazê-los prosperar e não de causar dano, planos de dar a vocês esperança e um futuro.", "ref": "Jeremias 29:11"},
    {"texto": "O Senhor é o meu pastor e nada me faltará.", "ref": "Salmos 23:1"},
    {"texto": "Tudo posso naquele que me fortalece.", "ref": "Filipenses 4:13"},
    {"texto": "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito.", "ref": "João 3:16"},
    {"texto": "Confie no Senhor de todo o seu coração e não se apoie em seu próprio entendimento.", "ref": "Provérbios 3:5"},
    {"texto": "Mas os que esperam no Senhor renovarão as suas forças. Voarão alto como águias.", "ref": "Isaías 40:31"},
    {"texto": "Não temas, porque eu sou contigo; não te assombres, porque eu sou teu Deus.", "ref": "Isaías 41:10"},
    {"texto": "Busquem em primeiro lugar o Reino de Deus e a sua justiça.", "ref": "Mateus 6:33"},
    {"texto": "O amor é paciente, o amor é bondoso. Não inveja, não se vangloria, não se orgulha.", "ref": "1 Coríntios 13:4"},
    {"texto": "Lançando sobre ele toda a vossa ansiedade, porque ele tem cuidado de vós.", "ref": "1 Pedro 5:7"},
    {"texto": "O Senhor é a minha luz e a minha salvação; a quem temerei?", "ref": "Salmos 27:1"},
    {"texto": "Alegrai-vos sempre no Senhor. Outra vez digo: Alegrai-vos!", "ref": "Filipenses 4:4"},
    {"texto": "Sede fortes e corajosos. Não temais, porque o Senhor vai convosco.", "ref": "Deuteronômio 31:6"},
    {"texto": "A fé é a certeza daquilo que esperamos e a prova das coisas que não vemos.", "ref": "Hebreus 11:1"},
    {"texto": "Deus é o nosso refúgio e a nossa força, socorro bem presente nas tribulações.", "ref": "Salmos 46:1"},
    {"texto": "A graça do Senhor Jesus seja com todos vocês.", "ref": "Apocalipse 22:21"},
    {"texto": "Bem-aventurados os misericordiosos, porque eles alcançarão misericórdia.", "ref": "Mateus 5:7"},
    {"texto": "O Senhor te guardará de todo o mal; ele guardará a tua alma.", "ref": "Salmos 121:7"},
    {"texto": "Não vos conformeis com este século, mas transformai-vos pela renovação da vossa mente.", "ref": "Romanos 12:2"},
    {"texto": "Aquele que habita no esconderijo do Altíssimo, à sombra do Onipotente descansará.", "ref": "Salmos 91:1"},
    {"texto": "Cria em mim, ó Deus, um coração puro, e renova dentro de mim um espírito firme.", "ref": "Salmos 51:10"},
    {"texto": "Vinde a mim, todos os que estais cansados e sobrecarregados, e eu vos aliviarei.", "ref": "Mateus 11:28"},
    {"texto": "O amor nunca falha.", "ref": "1 Coríntios 13:8"},
    {"texto": "Tudo tem o seu tempo determinado, há tempo para todo propósito debaixo do céu.", "ref": "Eclesiastes 3:1"},
    {"texto": "E conhecereis a verdade, e a verdade vos libertará.", "ref": "João 8:32"},
    {"texto": "Eu sou o caminho, a verdade e a vida.", "ref": "João 14:6"},
    {"texto": "Porque onde estiverem dois ou três reunidos em meu nome, ali estou no meio deles.", "ref": "Mateus 18:20"},
    {"texto": "O Senhor é bom, um forte refúgio no dia da angústia.", "ref": "Naum 1:7"},
    {"texto": "Mas eu, pela tua grande misericórdia, entrarei em tua casa.", "ref": "Salmos 5:7"},
    {"texto": "Aguarda o Senhor; sê forte, e ele fortalecerá o teu coração.", "ref": "Salmos 27:14"},
]

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return HTMLResponse(content=(FRONTEND_PATH / "index.html").read_text(encoding="utf-8"))

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

@app.get("/manifest.json")
async def manifest():
    return FileResponse(str(FRONTEND_PATH / "manifest.json"), media_type="application/manifest+json")

@app.get("/sw.js")
async def sw():
    return FileResponse(str(FRONTEND_PATH / "sw.js"), media_type="application/javascript")

@app.get("/icon-192.png")
async def icon192():
    return FileResponse(str(FRONTEND_PATH / "icon-192.png"), media_type="image/png")

@app.get("/icon-512.png")
async def icon512():
    return FileResponse(str(FRONTEND_PATH / "icon-512.png"), media_type="image/png")

@app.get("/install-imgs/{filename}")
async def install_imgs(filename: str):
    p = FRONTEND_PATH / "install-imgs" / filename
    if p.exists():
        return FileResponse(str(p))
    from fastapi import HTTPException
    raise HTTPException(404)

@app.get("/versiculo-do-dia")
async def versiculo_do_dia():
    dia = datetime.now().timetuple().tm_yday
    v = VERSICULOS[dia % len(VERSICULOS)]
    return {"texto": v["texto"], "ref": v["ref"],
            "data": datetime.now().strftime("%A, %d de %B de %Y").capitalize(),
            "dia": dia}

# ── DIÁRIO ESPIRITUAL ─────────────────────────────────
@app.post("/prompt-diario")
async def prompt_diario(request: Request):
    body = await request.json()
    titulo_devocional = body.get("titulo", "")
    estado = body.get("estado", "")

    contexto = f'sobre o devocional "{titulo_devocional}"' if titulo_devocional else ""
    estado_ctx = f" para alguém que estava se sentindo {estado}" if estado else ""

    prompt = f"""Gere 3 perguntas reflexivas curtas e profundas para um diário espiritual cristão {contexto}{estado_ctx}.

As perguntas devem:
- Ser pessoais e introspectivas
- Conectar a Palavra de Deus com a vida prática
- Incentivar o crescimento espiritual
- Ter no máximo 15 palavras cada

Responda APENAS com as 3 perguntas, uma por linha, sem numeração, sem explicações."""

    def stream():
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        ) as s:
            for text in s.text_stream:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# ── NOTIFICAÇÕES ──────────────────────────────────────
@app.post("/salvar-notificacao")
async def salvar_notificacao(request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    horario = body.get("horario", "07:00")
    mensagem = body.get("mensagem", "Bom dia! Sua Palavra de hoje está esperando. ☀️")
    ativa = body.get("ativa", True)
    push_token = body.get("push_token", "")

    if not user_id:
        return {"error": "user_id obrigatório"}

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    async with httpx.AsyncClient() as c:
        await c.patch(
            f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}",
            headers=headers,
            json={
                "notif_horario": horario,
                "notif_mensagem": mensagem,
                "notif_ativa": ativa,
                "notif_push_token": push_token
            }
        )

    return {"ok": True}

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

Gere devocional PERSONALIZADO para este estado emocional. Versículo específico, personagem bíblico similar, oração adaptada, ação prática específica.

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

[parágrafo 4 — aplicação prática]

[parágrafo 5 — esperança e frase de impacto]

✦ "[FRASE DE DESTAQUE]"

🙏 ORAÇÃO:
[oração adaptada ao estado, 4-5 linhas]

💡 AÇÃO PRÁTICA PARA HOJE:
[ação específica]

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


# ── PLANOS TEMÁTICOS ──────────────────────────────────
PLANOS = {
    "ansiedade": {"nome": "Vencendo a Ansiedade", "dias": 7, "emoji": "🧘", "desc": "7 dias encontrando paz em Deus", "cor": "#4A7FA5"},
    "gratidao": {"nome": "Coração Grato", "dias": 7, "emoji": "🙏", "desc": "7 dias cultivando gratidão", "cor": "#5C7A5E"},
    "proposito": {"nome": "Descobrindo seu Propósito", "dias": 30, "emoji": "🧭", "desc": "30 dias buscando direção divina", "cor": "#C9A84C"},
    "casamento": {"nome": "Amor que Transforma", "dias": 30, "emoji": "💑", "desc": "30 dias fortalecendo seu relacionamento", "cor": "#CC7B7B"},
    "trabalho": {"nome": "Fé no Trabalho", "dias": 7, "emoji": "💼", "desc": "7 dias integrando fé e carreira", "cor": "#7B8FCC"},
    "cura": {"nome": "Cura Interior", "dias": 30, "emoji": "💚", "desc": "30 dias de restauração e cura", "cor": "#5C7A5E"},
    "novo_comeco": {"nome": "Novo Começo", "dias": 7, "emoji": "✨", "desc": "7 dias recomeçando com Deus", "cor": "#C9A84C"},
}

@app.post("/devocional-plano")
async def devocional_plano(request: Request):
    body = await request.json()
    plano_id = body.get("plano_id")
    dia = body.get("dia", 1)

    if plano_id not in PLANOS:
        from fastapi import HTTPException
        raise HTTPException(400, "Plano não encontrado")

    plano = PLANOS[plano_id]
    agora = datetime.now()
    data_formatada = agora.strftime("%A, %d de %B de %Y").capitalize()

    prompt = f"""Você é o gerador de devocionais do app "Manhã com Deus". Gere o devocional do DIA {dia} de {plano['dias']} do plano "{plano['nome']}".

CONTEXTO DO PLANO: {plano['desc']}
DIA: {dia} de {plano['dias']}
DATA: {data_formatada}

REGRAS:
- O devocional deve ser específico para o tema "{plano['nome']}" no dia {dia}
- Deve haver uma progressão — dia 1 é introdução, dias seguintes aprofundam
- Versículo deve ser diretamente relacionado ao tema do dia
- Personagem bíblico que viveu o tema
- Tom acolhedor, profundo, sem jargão excessivo
- Título conceitual forte (3-6 palavras)

USE EXATAMENTE este formato:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{plano['emoji']} {plano['nome']} · Dia {dia} de {plano['dias']}
📅 {data_formatada}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✦ [TÍTULO CONCEITUAL]

📖 VERSÍCULO:
"[versículo relacionado ao tema do dia {dia}]"
— [Livro Cap:Ver]

💭 REFLEXÃO:
[parágrafo 1 — introduce o aspecto do tema para o dia {dia}]

[parágrafo 2 — aprofundamento bíblico]

[parágrafo 3 — personagem bíblico que viveu isso]

[parágrafo 4 — aplicação prática para hoje]

[parágrafo 5 — encorajamento e conexão com o próximo dia]

✦ "[FRASE DE DESTAQUE]"

🙏 ORAÇÃO:
[oração específica para o tema {plano['nome']} no dia {dia}]

💡 AÇÃO PRÁTICA PARA HOJE:
[ação concreta relacionada ao tema]

📝 ANOTAÇÕES:
___________
___________
___________

🎵 LOUVOR DO DIA:
[Música gospel alinhada ao tema + Artista + Link YouTube]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    def stream_generator():
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.get("/planos")
async def listar_planos():
    return PLANOS
