"""
escola_routes.py
Rotas da Escola Profética — Manhã com Deus
Inclua no main.py com:
    from escola_routes import router as escola_router
    app.include_router(escola_router)
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from openai import OpenAI
from pathlib import Path
from datetime import datetime
import json, os, httpx

# SEM prefix — rotas já têm /escola/ no nome
router = APIRouter()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
FRONTEND_PATH = Path(__file__).parent / "frontend"

MODULOS = [
    {"id": "apostasia",      "titulo": "A Apostasia dos Últimos Dias",        "capitulos": 3, "minutos": 40, "ordem": 1},
    {"id": "arrebatamento",  "titulo": "O Arrebatamento e os Últimos Dias",   "capitulos": 5, "minutos": 70, "ordem": 2},
    {"id": "cavaleiros",     "titulo": "Os 4 Cavaleiros do Apocalipse",       "capitulos": 4, "minutos": 55, "ordem": 3},
    {"id": "tribulacao",     "titulo": "A Grande Tribulação",                 "capitulos": 4, "minutos": 60, "ordem": 4},
    {"id": "anticristo",     "titulo": "O Anticristo e a Marca da Besta",     "capitulos": 3, "minutos": 50, "ordem": 5},
    {"id": "segunda_vinda",  "titulo": "A Segunda Vinda de Cristo",           "capitulos": 3, "minutos": 45, "ordem": 6},
    {"id": "milenio",        "titulo": "O Milênio e o Reino de Cristo",       "capitulos": 3, "minutos": 40, "ordem": 7},
    {"id": "nova_jerusalem", "titulo": "A Nova Jerusalém e a Eternidade",     "capitulos": 3, "minutos": 35, "ordem": 8},
]

def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

# ── Verificar acesso do aluno ────────────────────────────────────────
@router.get("/escola/acesso")
async def verificar_acesso(user_id: str, produto: str = "escola_apocalipse"):
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{SUPABASE_URL}/rest/v1/purchases"
            f"?user_id=eq.{user_id}&produto=eq.{produto}&ativo=eq.true",
            headers=sb_headers()
        )
        dados = r.json()
    return {"acesso": len(dados) > 0, "produto": produto}

# ── Listar módulos ───────────────────────────────────────────────────
@router.get("/escola/modulos")
async def listar_modulos():
    return MODULOS

# ── Progresso ────────────────────────────────────────────────────────
@router.post("/escola/progresso")
async def salvar_progresso(request: Request):
    body = await request.json()
    user_id   = body.get("user_id")
    modulo_id = body.get("modulo_id")
    capitulo  = body.get("capitulo", 1)
    concluido = body.get("concluido", False)

    if not user_id or not modulo_id:
        raise HTTPException(400, "user_id e modulo_id obrigatórios")

    async with httpx.AsyncClient() as c:
        await c.post(
            f"{SUPABASE_URL}/rest/v1/module_progress",
            headers={**sb_headers(), "Prefer": "resolution=merge-duplicates"},
            json={
                "user_id": user_id,
                "modulo_id": modulo_id,
                "ultimo_capitulo": capitulo,
                "concluido": concluido,
                "updated_at": datetime.now().isoformat()
            }
        )
    return {"ok": True}

@router.get("/escola/progresso")
async def buscar_progresso(user_id: str):
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{SUPABASE_URL}/rest/v1/module_progress?user_id=eq.{user_id}",
            headers=sb_headers()
        )
    return r.json()

# ── Anotações ────────────────────────────────────────────────────────
@router.post("/escola/anotacao")
async def salvar_anotacao(request: Request):
    body = await request.json()
    user_id   = body.get("user_id")
    modulo_id = body.get("modulo_id")
    capitulo  = body.get("capitulo", 1)
    texto     = body.get("texto", "")
    tag       = body.get("tag", "reflexao")

    if not user_id or not modulo_id:
        raise HTTPException(400, "Dados incompletos")

    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{SUPABASE_URL}/rest/v1/module_notes",
            headers={**sb_headers(), "Prefer": "return=representation"},
            json={
                "user_id": user_id,
                "modulo_id": modulo_id,
                "capitulo": capitulo,
                "texto": texto,
                "tag": tag,
                "created_at": datetime.now().isoformat()
            }
        )
    return {"ok": True, "data": r.json()}

@router.get("/escola/anotacoes")
async def buscar_anotacoes(user_id: str, modulo_id: str):
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{SUPABASE_URL}/rest/v1/module_notes"
            f"?user_id=eq.{user_id}&modulo_id=eq.{modulo_id}"
            f"&order=created_at.desc",
            headers=sb_headers()
        )
    return r.json()

@router.delete("/escola/anotacao/{nota_id}")
async def deletar_anotacao(nota_id: str, user_id: str):
    async with httpx.AsyncClient() as c:
        await c.delete(
            f"{SUPABASE_URL}/rest/v1/module_notes"
            f"?id=eq.{nota_id}&user_id=eq.{user_id}",
            headers=sb_headers()
        )
    return {"ok": True}

# ── Comentários ──────────────────────────────────────────────────────
@router.post("/escola/comentario")
async def salvar_comentario(request: Request):
    body = await request.json()
    user_id   = body.get("user_id")
    modulo_id = body.get("modulo_id")
    capitulo  = body.get("capitulo", 1)
    texto     = body.get("texto", "")

    if not user_id or not texto:
        raise HTTPException(400, "Dados incompletos")

    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{SUPABASE_URL}/rest/v1/module_comments",
            headers={**sb_headers(), "Prefer": "return=representation"},
            json={
                "user_id": user_id,
                "modulo_id": modulo_id,
                "capitulo": capitulo,
                "texto": texto,
                "curtidas": 0,
                "created_at": datetime.now().isoformat()
            }
        )
    return {"ok": True}

@router.get("/escola/comentarios")
async def buscar_comentarios(modulo_id: str, capitulo: int = 0):
    filtro = f"modulo_id=eq.{modulo_id}"
    if capitulo > 0:
        filtro += f"&capitulo=eq.{capitulo}"
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{SUPABASE_URL}/rest/v1/module_comments"
            f"?{filtro}&order=curtidas.desc,created_at.desc&limit=20",
            headers=sb_headers()
        )
    return r.json()

@router.post("/escola/comentario/{comentario_id}/curtir")
async def curtir_comentario(comentario_id: str, request: Request):
    async with httpx.AsyncClient() as c:
        await c.post(
            f"{SUPABASE_URL}/rest/v1/rpc/incrementar_curtida_comentario",
            headers=sb_headers(),
            json={"comentario_uuid": comentario_id}
        )
    return {"ok": True}

# ── Assistente IA ────────────────────────────────────────────────────
@router.post("/escola/ia")
async def assistente_ia(request: Request):
    body = await request.json()
    pergunta  = body.get("pergunta", "")
    modulo_id = body.get("modulo_id", "")
    contexto  = body.get("contexto", "")
    historico = body.get("historico", [])

    if not pergunta:
        raise HTTPException(400, "Pergunta obrigatória")

    modulo_nome = next(
        (m["titulo"] for m in MODULOS if m["id"] == modulo_id),
        "Escola Profética"
    )

    system = f"""Você é o assistente de estudos bíblicos da Escola Profética — Manhã com Deus.
O aluno está estudando o módulo: "{modulo_nome}".
{"O aluno selecionou o seguinte trecho do material: " + contexto if contexto else ""}

Suas regras:
- Responda APENAS com base na Bíblia e no conteúdo do módulo
- Tom de pastor amigo: cálido, acessível, sem jargão excessivo
- Citar versículos relevantes de forma natural
- Máximo 4 parágrafos por resposta
- Português brasileiro natural
- Se a pergunta fugir completamente do tema bíblico, redirecione gentilmente
"""

    mensagens = [{"role": "system", "content": system}]
    for h in historico[-6:]:
        mensagens.append({"role": h["role"], "content": h["content"]})
    mensagens.append({"role": "user", "content": pergunta})

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

# ── Gerar PDF ────────────────────────────────────────────────────────
@router.post("/escola/gerar-pdf")
async def gerar_pdf_aluno(request: Request):
    body = await request.json()
    modulo_id    = body.get("modulo_id", "")
    anotacoes    = body.get("anotacoes", [])
    respostas_ia = body.get("respostas_ia", [])

    modulo = next((m for m in MODULOS if m["id"] == modulo_id), None)
    if not modulo:
        raise HTTPException(404, "Módulo não encontrado")

    conteudo = f"""ESCOLA PROFÉTICA — MANHÃ COM DEUS
{modulo['titulo'].upper()}

Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MINHAS ANOTAÇÕES
"""
    for nota in anotacoes:
        conteudo += f"\n[{nota.get('tag','').upper()}] Cap. {nota.get('capitulo','')}\n"
        conteudo += f"{nota.get('texto','')}\n"
        conteudo += "─" * 40 + "\n"

    if respostas_ia:
        conteudo += "\nMINHAS PERGUNTAS E RESPOSTAS DA IA\n"
        for item in respostas_ia:
            conteudo += f"\nP: {item.get('pergunta','')}\n"
            conteudo += f"R: {item.get('resposta','')}\n"
            conteudo += "─" * 40 + "\n"

    conteudo += "\n\nEscola Profética · Manhã com Deus · manhacomdeus.com.br"
    return {"conteudo": conteudo, "modulo": modulo["titulo"]}

# ── Stripe Webhook ───────────────────────────────────────────────────
@router.post("/escola/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.json()
    evento = body.get("type", "")

    if evento == "checkout.session.completed":
        session = body.get("data", {}).get("object", {})
        user_id = session.get("metadata", {}).get("user_id")
        produto = session.get("metadata", {}).get("produto", "escola_apocalipse")

        if user_id:
            async with httpx.AsyncClient() as c:
                await c.post(
                    f"{SUPABASE_URL}/rest/v1/purchases",
                    headers={**sb_headers(), "Prefer": "return=minimal"},
                    json={
                        "user_id": user_id,
                        "produto": produto,
                        "ativo": True,
                        "stripe_session_id": session.get("id"),
                        "created_at": datetime.now().isoformat()
                    }
                )
    return {"received": True}
