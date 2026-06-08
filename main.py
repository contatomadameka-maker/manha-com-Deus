from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import json, os, asyncio
from pathlib import Path
from datetime import datetime
import httpx

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
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
        s = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=200,
            stream=True,
            messages=[{"role": "user", "content": prompt}]
        )
        for chunk in s:
            text = chunk.choices[0].delta.content or ""
            if text:
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

def get_temporada_sazonal(agora):
    mes = agora.month
    dia = agora.day
    if mes == 12 and dia >= 25: return {"nome": "Natal de Jesus", "emoji": "⭐", "cor": "#C9A84C"}
    if mes == 12 and dia >= 1: return {"nome": "Advento", "emoji": "🕯️", "cor": "#7B3FA0"}
    if mes == 1 and dia == 1: return {"nome": "Ano Novo", "emoji": "🎊", "cor": "#C9A84C"}
    if mes == 1 and dia <= 6: return {"nome": "Reis Magos", "emoji": "⭐", "cor": "#C9A84C"}
    if mes == 3 and dia >= 22 and dia <= 31: return {"nome": "Semana Santa", "emoji": "✝️", "cor": "#8B4513"}
    if mes == 4 and dia <= 25: return {"nome": "Tempo Pascal", "emoji": "🌅", "cor": "#FFD700"}
    if mes == 5 and dia >= 15: return {"nome": "Pentecostes", "emoji": "🔥", "cor": "#FF4500"}
    if mes == 6 and dia <= 15: return {"nome": "Pentecostes", "emoji": "🔥", "cor": "#FF4500"}
    if mes == 11 and dia in [1, 2]: return {"nome": "Todos os Santos", "emoji": "🕊️", "cor": "#5C7A5E"}
    if mes == 5 and agora.weekday() == 6 and 8 <= dia <= 14: return {"nome": "Dia das Mães", "emoji": "💐", "cor": "#FF69B4"}
    if mes == 8 and agora.weekday() == 6 and 8 <= dia <= 14: return {"nome": "Dia dos Pais", "emoji": "👨", "cor": "#4A7FA5"}
    return None

@app.get("/temporada")
async def temporada_atual():
    agora = datetime.now()
    t = get_temporada_sazonal(agora)
    if t:
        return t
    return {"nome": None}

@app.post("/devocional")
async def gerar_devocional(request: Request):
    body = await request.json()
    modo = body.get("modo", 1)
    estado_label = body.get("estado_label", "")
    estado_icon = body.get("estado_icon", "")
    agora = datetime.now()
    data_formatada = agora.strftime("%A, %d de %B de %Y").capitalize()
    dia_ano = agora.timetuple().tm_yday
    temporada = get_temporada_sazonal(agora)

    temporada_ctx = f"\n⚠️ IMPORTANTE: Hoje é {temporada['emoji']} {temporada['nome']}! O devocional DEVE ser especialmente temático para esta data cristã especial." if temporada else ""

    if modo == 1:
        prompt = f"""Você é o gerador de devocionais do app "Manhã com Deus". Gere um devocional completo e profundo para hoje ({data_formatada}, Dia {dia_ano} do ano).{temporada_ctx}

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
        s = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            stream=True,
            messages=[{"role": "user", "content": prompt}]
        )
        for chunk in s:
            text = chunk.choices[0].delta.content or ""
            if text:
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
[parágrafo 1]

[parágrafo 2]

[parágrafo 3]

[parágrafo 4]

[parágrafo 5]

✦ "[FRASE DE DESTAQUE]"

🙏 ORAÇÃO:
[oração específica para o tema]

💡 AÇÃO PRÁTICA PARA HOJE:
[ação concreta]

📝 ANOTAÇÕES:
___________
___________
___________

🎵 LOUVOR DO DIA:
[Música gospel alinhada ao tema + Artista + Link YouTube]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    def stream_generator():
        s = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            stream=True,
            messages=[{"role": "user", "content": prompt}]
        )
        for chunk in s:
            text = chunk.choices[0].delta.content or ""
            if text:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.get("/planos")
async def listar_planos():
    return PLANOS


# ── QUIZ BÍBLICO ──────────────────────────────────────
@app.post("/gerar-quiz")
async def gerar_quiz(request: Request):
    body = await request.json()
    nivel = body.get("nivel", "iniciante")
    semana = body.get("semana", "")

    niveis = {
        "iniciante": "perguntas básicas sobre histórias e personagens bíblicos conhecidos.",
        "intermediario": "perguntas intermediárias sobre ensinamentos, livros e contexto bíblico.",
        "avancado": "perguntas avançadas sobre teologia, profetas menores, genealogias e detalhes específicos."
    }

    prompt = f"""Gere um quiz bíblico com EXATAMENTE 5 perguntas de nível {nivel} para a semana {semana}.

Nível: {niveis.get(nivel, niveis['iniciante'])}

REGRAS:
- Cada pergunta deve ter exatamente 4 alternativas (A, B, C, D)
- Apenas UMA alternativa correta
- As perguntas devem ser variadas
- As alternativas erradas devem ser plausíveis
- Inclua uma explicação curta para a resposta correta

Responda APENAS em JSON válido, sem markdown, sem explicações fora do JSON:

{{"perguntas": [{{"id": 1, "pergunta": "texto", "alternativas": {{"A": "texto", "B": "texto", "C": "texto", "D": "texto"}}, "correta": "A", "explicacao": "explicação"}}]}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = response.choices[0].message.content.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        import json as json_lib
        dados = json_lib.loads(texto)
        return dados
    except Exception as e:
        return {"error": str(e)}


# ── ORAÇÃO GUIADA ─────────────────────────────────────
@app.post("/gerar-oracao")
async def gerar_oracao(request: Request):
    body = await request.json()
    tipo = body.get("tipo", "diaria")
    tema = body.get("tema", "")
    estado = body.get("estado", "")

    agora = datetime.now()
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    dias_sem = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira","Sábado","Domingo"]
    data_formatada = dias_sem[agora.weekday()] + ", " + str(agora.day) + " de " + meses[agora.month-1] + " de " + str(agora.year)

    if tipo == "noturna":
        prompt = f"""Gere uma oração noturna guiada para encerrar o dia com Deus.
Data: {data_formatada}
{f"Tema do dia: {tema}" if tema else ""}

USE EXATAMENTE este formato:

🌙 ORAÇÃO DA NOITE
{data_formatada}

✦ GRATIDÃO PELO DIA
[2-3 linhas de gratidão]

✦ PERDÃO E ENTREGA
[2-3 linhas]

✦ INTERCESSÃO
[2-3 linhas]

✦ PAZ PARA DORMIR
[2-3 linhas]

✦ DECLARAÇÃO FINAL
[1-2 linhas]

Amém. 🙏"""
    else:
        contexto = f"sobre o tema: {tema}" if tema else "para começar o dia com Deus"
        estado_ctx = f"O usuário está se sentindo {estado}." if estado else ""

        prompt = f"""Gere uma oração matinal guiada {contexto}.
Data: {data_formatada}
{estado_ctx}

USE EXATAMENTE este formato:

☀️ ORAÇÃO DA MANHÃ
{data_formatada}

✦ ADORAÇÃO
[2-3 linhas]

✦ GRATIDÃO
[2-3 linhas]

✦ CONFISSÃO
[2-3 linhas]

✦ PEDIDOS DO DIA
[3-4 linhas]

✦ DECLARAÇÃO E ENVIO
[2-3 linhas]

Amém. 🙏"""

    def stream():
        s = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=800,
            stream=True,
            messages=[{"role": "user", "content": prompt}]
        )
        for chunk in s:
            text = chunk.choices[0].delta.content or ""
            if text:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── MEDITAÇÃO NOTURNA ─────────────────────────────────
@app.post("/meditacao-noturna")
async def meditacao_noturna(request: Request):
    body = await request.json()
    tema = body.get("tema", "")

    agora = datetime.now()
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    dias_sem = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira","Sábado","Domingo"]
    data_formatada = dias_sem[agora.weekday()] + ", " + str(agora.day) + " de " + meses[agora.month-1] + " de " + str(agora.year)

    prompt = f"""Gere uma meditação noturna cristã suave e tranquilizadora.
Data: {data_formatada}
{f"Tema do dia: {tema}" if tema else ""}

USE EXATAMENTE este formato:

🌙 MEDITAÇÃO NOTURNA
{data_formatada}

✦ [TÍTULO SUAVE]

📖 VERSÍCULO DA NOITE:
"[versículo sobre paz ou descanso]"
— [Referência]

💭 REFLEXÃO:
[parágrafo 1 — suave, agradecendo pelo dia]

[parágrafo 2 — entregando preocupações a Deus]

[parágrafo 3 — encontrando paz no descanso]

🌬️ RESPIRAÇÃO GUIADA:
Inspire por 4 tempos... segure por 4... expire por 6...
[2-3 frases suaves]

🙏 ORAÇÃO DA NOITE:
[oração curta de 3-4 linhas]

✦ "[FRASE DE PAZ]"

Boa noite. 🌙"""

    def stream():
        s = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=800,
            stream=True,
            messages=[{"role": "user", "content": prompt}]
        )
        for chunk in s:
            text = chunk.choices[0].delta.content or ""
            if text:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── PEDIDOS DE ORAÇÃO ─────────────────────────────────
@app.get("/pedidos-oracao")
async def listar_pedidos():
    return {"ok": True}

@app.post("/orar-por-pedido")
async def orar_por_pedido(request: Request):
    body = await request.json()
    pedido_id = body.get("pedido_id")
    if not pedido_id:
        return {"error": "pedido_id obrigatório"}
    return {"ok": True}


# ── RELATÓRIO MENSAL ──────────────────────────────────
@app.post("/relatorio-mensal")
async def relatorio_mensal(request: Request):
    body = await request.json()
    dados = body.get("dados", {})

    agora = datetime.now()
    mes_anterior = agora.month - 1 if agora.month > 1 else 12
    ano = agora.year if agora.month > 1 else agora.year - 1
    meses = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    nome_mes = meses[mes_anterior]

    devocionais = dados.get("devocionais", 0)
    streak_max = dados.get("streak_max", 0)
    oracoes = dados.get("oracoes", 0)
    meditacoes = dados.get("meditacoes", 0)
    quiz_acertos = dados.get("quiz_acertos", 0)
    quiz_total = dados.get("quiz_total", 0)
    planos_ativos = dados.get("planos_ativos", 0)
    dias_lidos = dados.get("dias_lidos", 0)

    prompt = f"""Você é o assistente espiritual do app "Manhã com Deus". Gere um relatório espiritual mensal personalizado e encorajador.

MÊS: {nome_mes} de {ano}

DADOS:
- Devocionais lidos: {devocionais}
- Dias com leitura: {dias_lidos}
- Maior sequência: {streak_max} dias
- Orações realizadas: {oracoes}
- Meditações noturnas: {meditacoes}
- Quiz: {quiz_acertos} acertos de {quiz_total} perguntas
- Planos ativos: {planos_ativos}

USE EXATAMENTE este formato:

📊 RELATÓRIO ESPIRITUAL
{nome_mes} de {ano}

✦ [TÍTULO DA JORNADA]

🌟 SUA JORNADA EM NÚMEROS:
[Celebre cada dado — 4-5 linhas]

📖 PALAVRA PARA ESTA JORNADA:
"[Versículo]"
— [Referência]

💭 REFLEXÃO DO MÊS:
[2-3 parágrafos encorajadores]

🌱 SEMENTE PARA {meses[agora.month] if agora.month <= 12 else "Janeiro"}:
[Encorajamento para o próximo mês]

✦ "[FRASE DE ENCORAJAMENTO FINAL]"

Com amor e fé,
Manhã com Deus 🙏"""

    def stream():
        s = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1000,
            stream=True,
            messages=[{"role": "user", "content": prompt}]
        )
        for chunk in s:
            text = chunk.choices[0].delta.content or ""
            if text:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── PALAVRA PROFÉTICA SEMANAL ─────────────────────────
@app.get("/palavra-profetica")
async def palavra_profetica():
    agora = datetime.now()
    meses = ["janeiro","fevereiro","março","abril","maio","junho",
             "julho","agosto","setembro","outubro","novembro","dezembro"]
    dias_sem = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira",
                "Sexta-feira","Sábado","Domingo"]
    data_formatada = dias_sem[agora.weekday()] + ", " + str(agora.day) + " de " + meses[agora.month-1] + " de " + str(agora.year)
    semana = agora.isocalendar()[1]
    mes = agora.month

    if mes in [12, 1]: temporada = "Advento e Natal"
    elif mes in [2, 3]: temporada = "Quaresma"
    elif mes == 4: temporada = "Páscoa"
    elif mes == 5: temporada = "Pentecostes"
    else: temporada = "Tempo Comum"

    prompt = f"""Gere uma palavra profética semanal para esta semana.

Data: {data_formatada}
Semana {semana} do ano
Temporada espiritual: {temporada}

USE EXATAMENTE este formato:

⚡ PALAVRA DA SEMANA
Semana {semana} · {data_formatada}

✦ [TÍTULO — 3-5 palavras impactantes]

📖 VERSÍCULO ÂNCORA:
"[versículo]"
— [Referência]

🔥 A PALAVRA:
[2-3 parágrafos proféticos e encorajadores]

🎯 DECLARAÇÃO DA SEMANA:
"[Frase começando com EU SOU, EU TENHO ou EU POSSO]"

🙏 ORA ASSIM:
[Oração curta de 2-3 linhas]

✦ Que esta palavra frutifique em sua vida esta semana. 🙏"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = response.choices[0].message.content.strip()
        return {"texto": texto, "semana": semana, "data": data_formatada}
    except Exception as e:
        return {"error": str(e)}


# ── ACONSELHAMENTO IA ─────────────────────────────────
@app.post("/aconselhamento")
async def aconselhamento(request: Request):
    body = await request.json()
    mensagem = body.get("mensagem", "")
    historico = body.get("historico", [])

    if not mensagem:
        return {"error": "mensagem obrigatória"}

    system = """Você é um conselheiro cristão compassivo e sábio no app "Manhã com Deus". 
Seu papel é ouvir com empatia, responder com base bíblica e oferecer direção espiritual.
- Sempre comece reconhecendo o sentimento da pessoa
- Use versículos relevantes de forma natural
- Tom de pastor amigo, não de pregador formal
- Seja específico para o que a pessoa disse
- Ofereça uma pergunta reflexiva ao final
- Máximo 4-5 parágrafos
- Português brasileiro natural e acolhedor"""

    mensagens = [{"role": "system", "content": system}]
    for h in historico[-6:]:
        mensagens.append({"role": h["role"], "content": h["content"]})
    mensagens.append({"role": "user", "content": mensagem})

    def stream():
        s = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=600,
            stream=True,
            messages=mensagens
        )
        for chunk in s:
            text = chunk.choices[0].delta.content or ""
            if text:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── TESTEMUNHOS ───────────────────────────────────────
@app.get("/testemunhos")
async def listar_testemunhos():
    return {"ok": True}


# ── MODO FAMÍLIA ──────────────────────────────────────
import random
import string

def gerar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.post("/familia/criar")
async def criar_familia(request: Request):
    body = await request.json()
    nome = body.get("nome", "Minha Família")
    user_id = body.get("user_id")
    if not user_id:
        return {"error": "user_id obrigatório"}

    codigo = gerar_codigo()
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    async with httpx.AsyncClient() as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/grupos_familia",
            headers=headers,
            json={"nome": nome, "codigo": codigo, "criador_id": user_id}
        )
        grupo = r.json()
        if isinstance(grupo, list): grupo = grupo[0]
        grupo_id = grupo.get("id")

        await c.post(f"{SUPABASE_URL}/rest/v1/membros_familia",
            headers=headers,
            json={"grupo_id": grupo_id, "user_id": user_id, "apelido": "Líder"}
        )

    return {"codigo": codigo, "grupo_id": grupo_id, "nome": nome}

@app.post("/familia/entrar")
async def entrar_familia(request: Request):
    body = await request.json()
    codigo = body.get("codigo", "").upper().strip()
    user_id = body.get("user_id")
    apelido = body.get("apelido", "Membro")

    if not user_id or not codigo:
        return {"error": "Dados incompletos"}

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    async with httpx.AsyncClient() as c:
        r = await c.get(f"{SUPABASE_URL}/rest/v1/grupos_familia?codigo=eq.{codigo}",
            headers=headers)
        grupos = r.json()
        if not grupos:
            return {"error": "Código inválido"}
        grupo = grupos[0]

        await c.post(f"{SUPABASE_URL}/rest/v1/membros_familia",
            headers=headers,
            json={"grupo_id": grupo["id"], "user_id": user_id, "apelido": apelido}
        )

    return {"ok": True, "grupo": grupo}


# ── CÉLULA ────────────────────────────────────────────
@app.post("/celula/criar")
async def criar_celula(request: Request):
    body = await request.json()
    nome = body.get("nome", "Minha Célula")
    descricao = body.get("descricao", "")
    user_id = body.get("user_id")
    if not user_id:
        return {"error": "user_id obrigatório"}

    codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    async with httpx.AsyncClient() as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/celulas",
            headers=headers,
            json={"nome": nome, "codigo": codigo, "lider_id": user_id, "descricao": descricao}
        )
        celula = r.json()
        if isinstance(celula, list): celula = celula[0]
        celula_id = celula.get("id")

        await c.post(f"{SUPABASE_URL}/rest/v1/membros_celula",
            headers=headers,
            json={"celula_id": celula_id, "user_id": user_id, "nome": "Líder"}
        )

    return {"codigo": codigo, "celula_id": celula_id, "nome": nome}

@app.post("/celula/entrar")
async def entrar_celula(request: Request):
    body = await request.json()
    codigo = body.get("codigo", "").upper().strip()
    user_id = body.get("user_id")
    nome = body.get("nome", "Membro")

    if not user_id or not codigo:
        return {"error": "Dados incompletos"}

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    async with httpx.AsyncClient() as c:
        r = await c.get(f"{SUPABASE_URL}/rest/v1/celulas?codigo=eq.{codigo}",
            headers=headers)
        celulas = r.json()
        if not celulas:
            return {"error": "Código inválido"}
        celula = celulas[0]

        await c.post(f"{SUPABASE_URL}/rest/v1/membros_celula",
            headers=headers,
            json={"celula_id": celula["id"], "user_id": user_id, "nome": nome}
        )

    return {"ok": True, "celula": celula}

@app.post("/celula/gerar-aula")
async def gerar_aula_celula(request: Request):
    body = await request.json()
    tema = body.get("tema", "")
    passagem = body.get("passagem", "")
    nivel = body.get("nivel", "adultos")

    prompt = f"""Você é um preparador de aulas para células e grupos bíblicos. Gere uma aula completa e rica.

TEMA: {tema}
PASSAGEM BÍBLICA: {passagem if passagem else "Escolha a mais adequada para o tema"}
P�BLICO: {nivel}

═══════════════════════════════════════
📖 AULA DA CÉLULA
{tema.upper()}
═══════════════════════════════════════

⏱️ DURAÇÃO SUGERIDA: 60-90 minutos

📌 OBJETIVO DA AULA:
[1-2 frases]

📖 PASSAGEM BASE:
"[versículo principal]"
— [Referência]

🎯 INTRODUÇÃO (10 min):
[Dinâmica ou pergunta quebra-gelo]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✦ PONTO 1: [Título]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Desenvolvimento — 3-4 parágrafos]

❓ Pergunta de discussão: [pergunta]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✦ PONTO 2: [Título]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Desenvolvimento — 3-4 parágrafos]

❓ Pergunta de discussão: [pergunta]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✦ PONTO 3: [Título]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Desenvolvimento — 3-4 parágrafos]

❓ Pergunta de discussão: [pergunta]

🎯 APLICAÇÃO PRÁTICA (10 min):
[Desafio concreto para a semana]

🙏 ORAÇÃO DE ENCERRAMENTO:
[Oração modelo]

💡 DICA PARA O LÍDER:
[1-2 dicas práticas]

═══════════════════════════════════════"""

    def stream():
        s = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            stream=True,
            messages=[{"role": "user", "content": prompt}]
        )
        for chunk in s:
            text = chunk.choices[0].delta.content or ""
            if text:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
