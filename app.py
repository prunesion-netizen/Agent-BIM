import os
import threading
import logging
import secrets
import time
import functools
from datetime import timedelta
from pathlib import Path
from flask import Flask, request, jsonify, session, send_from_directory, redirect, abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

# ── Credențiale ────────────────────────────────────────────────────────────────
BIM_USERNAME = os.environ.get('BIM_USERNAME', 'admin')
BIM_PASSWORD_HASH = os.environ.get('BIM_PASSWORD_HASH', '')
if not BIM_PASSWORD_HASH:
    _tmp_hash = generate_password_hash('BIM2024!')
    BIM_PASSWORD_HASH = _tmp_hash
    logger.warning(
        "BIM_PASSWORD_HASH lipsește din .env! "
        "Se folosește parola temporară 'BIM2024!'. "
        "Setează BIM_PASSWORD_HASH în .env pentru producție."
    )

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Rate limiters (in-memory) ─────────────────────────────────────────────────
_login_attempts: dict = {}   # ip -> (count, first_ts)
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 900        # 15 min

_chat_requests: dict = {}    # session_id -> [timestamps]
MAX_CHAT_PER_HOUR = 60


def check_login_rate(ip: str) -> bool:
    """Return True if login is allowed, False if locked out."""
    now = time.time()
    if ip in _login_attempts:
        count, first_ts = _login_attempts[ip]
        if now - first_ts > LOCKOUT_SECONDS:
            del _login_attempts[ip]
        elif count >= MAX_LOGIN_ATTEMPTS:
            return False
    return True


def record_login_failure(ip: str) -> None:
    now = time.time()
    if ip in _login_attempts:
        count, first_ts = _login_attempts[ip]
        _login_attempts[ip] = (count + 1, first_ts)
    else:
        _login_attempts[ip] = (1, now)


def check_chat_rate(sid: str) -> bool:
    """Return True if chat request is within rate limit."""
    now = time.time()
    hour_ago = now - 3600
    ts_list = _chat_requests.get(sid, [])
    ts_list = [t for t in ts_list if t > hour_ago]
    _chat_requests[sid] = ts_list
    if len(ts_list) >= MAX_CHAT_PER_HOUR:
        return False
    ts_list.append(now)
    return True


# ── Auth helpers ──────────────────────────────────────────────────────────────
def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"error": "Neautentificat"}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


def generate_csrf() -> str:
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def csrf_protect() -> None:
    """Abort 403 if CSRF token is missing or invalid."""
    token = request.headers.get('X-CSRF-Token', '')
    if not token or token != session.get('csrf_token'):
        abort(403)


# ── Security headers ──────────────────────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return response


# ── Inițializare RAG (cu fallback graceful) ───────────────────────────────────
try:
    from bim_rag import init_rag, query_rag, get_rag_stats
    logger.info("Se inițializează motorul RAG...")
    rag_available = init_rag()
    if rag_available:
        logger.info("RAG activ.")
    else:
        stats = get_rag_stats()
        logger.warning(f"RAG inactiv: {stats.get('error', 'motiv necunoscut')}")
except Exception as e:
    logger.warning(f"Nu s-a putut importa bim_rag: {e}")
    rag_available = False
    def query_rag(q, n=5): return {"context": "", "sources": [], "rag_used": False}
    def get_rag_stats(): return {"ready": False, "chunk_count": 0, "model": None, "error": str(e)}

# ── Fallback knowledge (DOCX-uri originale) ──────────────────────────────────
fallback_knowledge = ""
if not rag_available:
    try:
        from bim_knowledge import load_bim_knowledge
        fallback_knowledge = load_bim_knowledge()
        logger.info("Fallback knowledge DOCX încărcat.")
    except Exception as e:
        logger.warning(f"Nu s-a putut încărca bim_knowledge: {e}")

# ── System prompts ────────────────────────────────────────────────────────────
SYSTEM_PROMPT_RAG = """Ești expert BIM (Building Information Modeling) specializat pe România. \
Răspunzi EXCLUSIV în limba română.

Folosești EXCLUSIV fragmentele furnizate în secțiunea CONTEXT de mai jos pentru a răspunde. \
Nu inventa informații care nu se găsesc în context.

Citează sursa la finalul fiecărei afirmații importante, în formatul: [Sursa: Titlu, Pag. X].

Dacă nu găsești informația în context, spune explicit: \
"Nu am date despre acest subiect în documentele disponibile."

Răspunde clar, structurat și profesional. Folosește liste și titluri când ajută la claritate."""

SYSTEM_PROMPT_FALLBACK = f"""Ești un expert BIM (Building Information Modeling) specializat în \
implementarea BIM în sectorul construcțiilor din România. Răspunzi EXCLUSIV în limba română.

Cunoștințele tale se bazează pe documentele oficiale BIM furnizate mai jos.

{fallback_knowledge}

Răspunde clar, structurat și profesional. Dacă nu știi răspunsul, spune că \
informația nu se găsește în documentele disponibile."""


# ── Rute publice ──────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET"])
def login_page():
    if session.get('logged_in'):
        return redirect('/')
    return send_from_directory(app.static_folder, "login.html")


@app.route("/login", methods=["POST"])
def login_post():
    ip = request.remote_addr or '0.0.0.0'
    if not check_login_rate(ip):
        return jsonify({"error": "Prea multe încercări. Încearcă din nou după 15 minute."}), 429

    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if username == BIM_USERNAME and check_password_hash(BIM_PASSWORD_HASH, password):
        session.permanent = True
        session['logged_in'] = True
        csrf = generate_csrf()
        if ip in _login_attempts:
            del _login_attempts[ip]
        logger.info(f"Login reușit pentru utilizatorul '{username}' de la {ip}")
        return jsonify({"csrf_token": csrf})
    else:
        record_login_failure(ip)
        logger.warning(f"Autentificare eșuată pentru '{username}' de la {ip}")
        return jsonify({"error": "Utilizator sau parolă incorectă."}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect('/login')


@app.route("/csrf-token")
@login_required
def csrf_token_endpoint():
    return jsonify({"csrf_token": generate_csrf()})


# ── Rute protejate ────────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/status")
@login_required
def status():
    stats = get_rag_stats()
    return jsonify({
        "rag_ready":   stats["ready"],
        "chunk_count": stats["chunk_count"],
        "model":       stats["model"],
        "error":       stats["error"],
    })


@app.route("/chat", methods=["POST"])
@login_required
def chat():
    csrf_protect()

    sid = session.get('_id', id(session))
    if not check_chat_rate(str(sid)):
        return jsonify({"error": "Limita de 60 mesaje/oră atinsă. Revino mai târziu."}), 429

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing message"}), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if "history" not in session:
        session["history"] = []

    session["history"].append({"role": "user", "content": user_message})

    sources   = []
    rag_used  = False

    if rag_available:
        rag_result = query_rag(user_message)
        rag_used   = rag_result["rag_used"]
        sources    = rag_result["sources"]

        if rag_used and rag_result["context"]:
            system = SYSTEM_PROMPT_RAG + f"\n\n--- CONTEXT ---\n\n{rag_result['context']}\n\n--- SFÂRȘIT CONTEXT ---"
        else:
            system = SYSTEM_PROMPT_RAG
    else:
        system = SYSTEM_PROMPT_FALLBACK

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            messages=session["history"],
        )
        assistant_message = response.content[0].text
        session["history"].append({"role": "assistant", "content": assistant_message})
        session.modified = True

        return jsonify({
            "response": assistant_message,
            "sources":  sources,
            "rag_used": rag_used,
        })

    except Exception as e:
        session["history"].pop()
        logger.error(f"Eroare Claude API: {e}")
        return jsonify({"error": "Eroare internă. Contactați administratorul."}), 500


@app.route("/reset", methods=["POST"])
@login_required
def reset():
    csrf_protect()
    session.pop("history", None)
    return jsonify({"status": "ok"})


# ── Generator imports (graceful) ──────────────────────────────────────────────
try:
    from bim_generators import (
        start_generation, get_job_status,
        list_generated_files, GENERATORS, DOC_LABELS,
        GENERATED_DIR,
    )
    _gen_ok = True
except Exception as _gen_err:
    logger.warning(f"bim_generators indisponibil: {_gen_err}")
    _gen_ok = False


# ── API: Proiecte ─────────────────────────────────────────────────────────────
@app.route("/api/projects")
@login_required
def api_projects():
    bim_dir = Path("BIM")
    if not bim_dir.exists():
        return jsonify([])
    projects = sorted(
        [d.name for d in bim_dir.iterdir() if d.is_dir()],
        key=str.lower,
    )
    return jsonify(projects)


# ── API: Documente indexate ───────────────────────────────────────────────────
@app.route("/api/documents")
@login_required
def api_documents():
    bim_dir = Path("BIM")
    if not bim_dir.exists():
        return jsonify([])
    files = []
    for ext in ("*.pdf", "*.docx"):
        for f in sorted(bim_dir.rglob(ext)):
            if f.name.startswith("~$"):
                continue
            rel = str(f.relative_to(bim_dir))
            parts = rel.replace("\\", "/").split("/")
            project = parts[0] if len(parts) > 1 else "—"
            files.append({
                "name":    f.name,
                "project": project,
                "path":    rel,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "ext":     f.suffix.upper().lstrip("."),
            })
    return jsonify(files)


# ── API: Upload document ──────────────────────────────────────────────────────
ALLOWED_EXT = {'.pdf', '.docx'}
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
MAGIC_BYTES = {'.pdf': b'%PDF', '.docx': b'PK\x03\x04'}


@app.route("/api/upload", methods=["POST"])
@login_required
def api_upload():
    csrf_protect()

    if "file" not in request.files:
        return jsonify({"error": "Niciun fișier trimis"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Nume fișier gol"}), 400

    # 1. Extensie
    ext = Path(f.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return jsonify({"error": f"Tip fișier nepermis. Sunt acceptate: PDF, DOCX"}), 400

    # 2. Mărime
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_UPLOAD_SIZE:
        return jsonify({"error": "Fișierul depășește limita de 50 MB"}), 400

    # 3. Magic bytes
    header = f.read(4)
    f.seek(0)
    expected_magic = MAGIC_BYTES.get(ext, b'')
    if expected_magic and not header.startswith(expected_magic):
        return jsonify({"error": "Fișierul nu corespunde extensiei declarate"}), 400

    # 4. Secure filename
    safe_name = secure_filename(f.filename)
    if not safe_name:
        return jsonify({"error": "Nume fișier invalid"}), 400

    project = request.form.get("project", "Uploads").strip() or "Uploads"
    safe_project = "".join(c for c in project if c.isalnum() or c in " _-")[:50]

    dest_dir = Path("BIM") / safe_project
    dest_dir.mkdir(parents=True, exist_ok=True)

    try:
        dest = dest_dir / safe_name
        f.save(str(dest))
    except Exception as e:
        logger.error(f"Eroare salvare fișier: {e}")
        return jsonify({"error": "Eroare internă. Contactați administratorul."}), 500

    return jsonify({"status": "ok", "path": str(dest), "project": safe_project})


# ── API: Re-indexare ──────────────────────────────────────────────────────────
_reindex_state = {"running": False, "last_result": None}


@app.route("/api/reindex", methods=["POST"])
@login_required
def api_reindex():
    csrf_protect()

    if _reindex_state["running"]:
        return jsonify({"status": "already_running"})

    def _run():
        _reindex_state["running"] = True
        try:
            import importlib, bim_ingest
            importlib.reload(bim_ingest)
            bim_ingest.main()
            global rag_available
            from bim_rag import init_rag
            rag_available = init_rag()
            _reindex_state["last_result"] = "ok"
        except Exception as e:
            logger.error(f"Eroare re-indexare: {e}")
            _reindex_state["last_result"] = str(e)
        finally:
            _reindex_state["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/api/reindex/status")
@login_required
def api_reindex_status():
    return jsonify({
        "running":     _reindex_state["running"],
        "last_result": _reindex_state["last_result"],
    })


# ── API: Generare documente ───────────────────────────────────────────────────
@app.route("/api/generate", methods=["POST"])
@login_required
def api_generate():
    csrf_protect()

    if not _gen_ok:
        return jsonify({"error": "Modulul de generare indisponibil"}), 500
    data    = request.get_json() or {}
    doc_type = data.get("type", "").lower()
    project  = data.get("project", "").strip()

    if doc_type not in GENERATORS:
        return jsonify({"error": f"Tip necunoscut: {doc_type}. Valid: {list(GENERATORS.keys())}"}), 400

    try:
        job_id = start_generation(doc_type, project)
    except Exception as e:
        logger.error(f"Eroare generare: {e}")
        return jsonify({"error": "Eroare internă. Contactați administratorul."}), 500

    return jsonify({"job_id": job_id, "label": DOC_LABELS.get(doc_type, doc_type)})


@app.route("/api/generate/status/<job_id>")
@login_required
def api_generate_status(job_id):
    if not _gen_ok:
        return jsonify({"error": "Modul generare indisponibil"}), 500
    return jsonify(get_job_status(job_id))


# ── API: Lista fisiere generate ───────────────────────────────────────────────
@app.route("/api/generated")
@login_required
def api_generated():
    if not _gen_ok:
        return jsonify([])
    return jsonify(list_generated_files())


# ── Download fișier generat ───────────────────────────────────────────────────
@app.route("/download/<path:filename>")
@login_required
def download_file(filename):
    if not _gen_ok:
        return "Modul generare indisponibil", 500
    safe = Path(filename).name  # fara path traversal
    return send_from_directory(
        str(GENERATED_DIR.resolve()),
        safe,
        as_attachment=True,
    )


if __name__ == "__main__":
    print("Agent BIM pornit la http://localhost:5000")
    app.run(debug=False, port=5000)
