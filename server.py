"""
Sorteador Mediateca — Backend
FastAPI + Playwright + browser-side fetch()

La tecnica clave: page.evaluate() ejecuta fetch() DENTRO del browser,
usando las cookies y headers reales de Instagram. No hay scraping de DOM.
"""

import os, re, sys, base64, logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, BrowserContext, TimeoutError as PWTimeout

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s: %(message)s")
log = logging.getLogger("sorteador")

SESSION_FILE = "ig-session.json"

# ── Restaurar sesion desde variable de entorno (deploy en nube) ───────────
_SESSION_B64 = os.getenv("IG_SESSION_B64", "").strip()
if _SESSION_B64 and not os.path.exists(SESSION_FILE):
    try:
        with open(SESSION_FILE, "wb") as _f:
            _f.write(base64.b64decode(_SESSION_B64))
        log.info("Sesion de Instagram restaurada desde IG_SESSION_B64")
    except Exception as _e:
        log.error(f"No se pudo restaurar la sesion desde IG_SESSION_B64: {_e}")

# En Linux (nube) no existe Chrome del sistema — usar Chromium de Playwright
_IS_CLOUD = sys.platform != "win32"

_pw      = None
_browser: Browser | None        = None
_ctx:     BrowserContext | None = None

# ── Instagram shortcode → numeric media_id ────────────────────────────────
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

def _shortcode_to_id(sc: str) -> str:
    n = 0
    for ch in sc:
        n = n * 64 + _ALPHABET.index(ch)
    return str(n)

def _extract_shortcode(url: str) -> str:
    for pat in [
        r"instagram\.com/p/([A-Za-z0-9_-]+)",
        r"instagram\.com/reel(?:s)?/([A-Za-z0-9_-]+)",
        r"instagram\.com/tv/([A-Za-z0-9_-]+)",
    ]:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    raise HTTPException(400, "URL invalida. Pega el link de un post, reel o IGTV de Instagram.")

# ── JavaScript ejecutado DENTRO del browser para llamar la API ────────────
_FETCH_JS = """
async ([mediaId, maxComments]) => {
    const comments = [];
    let minId = null;
    let pages = 0;

    while (comments.length < maxComments && pages < 60) {
        let url = `https://www.instagram.com/api/v1/media/${mediaId}/comments/` +
                  `?can_support_threading=true&permalink_enabled=false`;
        if (minId) url += `&min_id=${minId}`;

        let resp;
        try {
            resp = await fetch(url, {
                credentials: 'include',
                headers: {
                    'X-IG-App-ID': '936619743392459',
                    'X-ASBD-ID':   '129477',
                    'Accept':      'application/json, */*',
                },
            });
        } catch (e) {
            break;
        }

        if (!resp.ok) break;

        let data;
        try { data = await resp.json(); } catch (e) { break; }

        const batch = data.comments || [];
        for (const c of batch) {
            comments.push({
                username: (c.user && c.user.username) || c.username || '',
                text:     c.text || '',
                ts:       c.created_at || null,
            });
        }

        // Instagram paginacion: continuar mientras exista next_min_id
        if (!data.next_min_id) break;
        minId = data.next_min_id;
        pages++;

        await new Promise(r => setTimeout(r, 300));
    }

    return comments;
}
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pw, _browser, _ctx

    _pw      = await async_playwright().start()
    launch_kw: dict = {
        "headless": True,
        "args": [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-setuid-sandbox",
            "--no-zygote",
        ],
    }
    if not _IS_CLOUD:
        launch_kw["channel"] = "chrome"   # Windows local: usa Chrome del sistema
    _browser = await _pw.chromium.launch(**launch_kw)

    ctx_kw: dict = {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1280, "height": 800},
    }
    if os.path.exists(SESSION_FILE):
        ctx_kw["storage_state"] = SESSION_FILE
        log.info("Sesion de Instagram cargada desde ig-session.json OK")
    else:
        log.warning("ig-session.json no encontrado — ejecuta setup_session.py primero")

    _ctx = await _browser.new_context(**ctx_kw)

    # Pre-warm: abrir instagram.com para que las cookies esten activas
    if os.path.exists(SESSION_FILE):
        try:
            page = await _ctx.new_page()
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(1500)
            await page.close()
            log.info("Sesion pre-calentada OK")
        except Exception as e:
            log.warning(f"Pre-warm fallo (no critico): {e}")

    yield

    if _ctx:     await _ctx.close()
    if _browser: await _browser.close()
    if _pw:      await _pw.stop()


app = FastAPI(title="Sorteador Mediateca", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "ok":            True,
        "session_ready": os.path.exists(SESSION_FILE),
        "browser_ready": _browser is not None,
    }


class FetchReq(BaseModel):
    url:          str
    max_comments: int = 1000


@app.post("/api/fetch")
async def fetch_comments(req: FetchReq):
    if _ctx is None:
        raise HTTPException(503, "Navegador no inicializado.")

    shortcode = _extract_shortcode(req.url)
    media_id  = _shortcode_to_id(shortcode)

    log.info(f"Fetching {shortcode} (media_id={media_id})")

    page = await _ctx.new_page()
    try:
        # La pagina debe estar en instagram.com para que el fetch tenga cookies
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(500)

        comments = await page.evaluate(_FETCH_JS, [media_id, req.max_comments])

    except PWTimeout:
        raise HTTPException(408, "Timeout cargando Instagram. Intenta de nuevo.")
    except Exception as e:
        raise HTTPException(500, f"Error inesperado: {e}")
    finally:
        await page.close()

    if not comments:
        raise HTTPException(
            403,
            "No se pudieron obtener comentarios. "
            "La sesion puede haber expirado — ejecuta setup_session.py de nuevo.",
        )

    log.info(f"OK: {len(comments)} comentarios para {shortcode}")
    return {"total": len(comments), "partial": False, "comments": comments}


# ── Static frontend (MUST be last) ─────────────────────────────────────────
app.mount("/", StaticFiles(directory="public", html=True), name="static")
