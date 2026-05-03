# Sorteador Mediateca · Instagram

App web gratuita para sorteos de Instagram. Pegás el link del post, el sistema extrae **todos los comentarios automáticamente** y sortea 1, 2 o 3 ganadores con animación.

Desarrollado por [@mostadata](https://www.instagram.com/mostadata) para [@mediateca.viedma](https://www.instagram.com/mediateca.viedma)

---

## Cómo funciona

1. Pegás el link de cualquier post, reel o IGTV de Instagram
2. El backend (Python + Playwright) usa una sesión real de Chrome para llamar la API privada de Instagram — sin scraping de DOM, sin limitaciones de bots
3. El frontend deduplica participantes, aplica filtros y sortea con animación
4. Se muestran ganadores con su comentario ganador

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | HTML + CSS + JS vanilla (sin dependencias) |
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| Automatización | Playwright (usa Chrome instalado en el sistema) |
| Sesión | `ig-session.json` — guardada una sola vez con `setup_session.py` |

---

## Requisitos

- Python 3.10+
- **Google Chrome** instalado en el sistema
- Cuenta de Instagram (recomendado: cuenta secundaria)

---

## Instalación (Windows)

```
1. Clonar el repositorio
   git clone https://github.com/TU_USUARIO/sorteador-mediateca.git
   cd sorteador-mediateca

2. Crear entorno virtual e instalar dependencias
   python -m venv venv
   venv\Scripts\pip install -r requirements.txt

3. Crear el archivo .env con tus credenciales de Instagram
   Copiar .env.example → .env  y completar usuario/contraseña

4. Iniciar la app (doble clic en start.bat)
   start.bat
```

La primera vez que ejecutás `start.bat`, se abre Chrome visible y loguea automáticamente con las credenciales del `.env`. La sesión queda guardada en `ig-session.json` y no vuelve a pedir login.

---

## Uso

1. Abrí `http://localhost:8000` en tu navegador
2. Pegá el link del post de Instagram
3. Elegí cuántos ganadores sortear (1, 2 o 3)
4. Hacé clic en **Cargar comentarios** → **Sortear**

---

## Filtros disponibles

| Filtro | Descripción |
|--------|-------------|
| Mín. menciones (@) | Requerí que el comentario etiquete N amigos |
| Excluir usuarios | Cuentas a ignorar (la tuya, bots, moderadores) |
| Deduplicación | Automática — cada usuario participa una sola vez |
| Sin repetición | Los ganadores se eliminan del pool antes del siguiente sorteo |

---

## Seguridad

- `.env` y `ig-session.json` están en `.gitignore` — **nunca se suben al repositorio**
- El servidor corre solo en `127.0.0.1` (localhost) — no es accesible desde internet
- No se almacenan comentarios ni datos de participantes en disco

---

## Estructura del proyecto

```
sorteador-mediateca/
├── public/
│   ├── index.html          # Frontend completo (sin dependencias externas)
│   ├── mostadata-logo.png  # Logo MostaData (topbar)
│   ├── mediateca-logo.png  # Logo Mediateca (hero + modal) — agregar manualmente
│   └── Instagram_icon.png  # Ícono de Instagram
├── server.py               # API FastAPI + Playwright
├── setup_session.py        # Login único de Instagram (ejecutar una vez)
├── start.bat               # Launcher Windows (doble clic)
├── requirements.txt
├── .env.example            # Plantilla de credenciales
├── .gitignore
└── README.md
```

---

## Donaciones

Si esta herramienta te sirve, podés apoyar el proyecto:

**Alias Mercado Pago:** `mostadata`

---

## Licencia

MIT — libre para uso personal y comercial.
