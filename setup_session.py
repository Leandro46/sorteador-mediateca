# -*- coding: utf-8 -*-
"""
Setup unico de sesion de Instagram.

Abre Chrome visible, inicia sesion con las credenciales del .env
y guarda la sesion en ig-session.json.

Los usuarios finales de la app NUNCA ven esta pantalla.

Ejecutar una sola vez:
    venv\\Scripts\\python setup_session.py
"""

import os, sys
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

IG_USER  = os.getenv("IG_USERNAME", "").strip()
IG_PASS  = os.getenv("IG_PASSWORD", "").strip()
SESSION  = "ig-session.json"


def log(msg):
    print(msg, flush=True)


def main():
    if not IG_USER or not IG_PASS:
        log("ERROR: IG_USERNAME o IG_PASSWORD no estan en el archivo .env")
        sys.exit(1)

    log("=" * 55)
    log("  CONFIGURACION DE SESION - Sorteador Mediateca")
    log("=" * 55)
    log(f"\n>> Abriendo Chrome para iniciar sesion como: {IG_USER}")
    log("   Si Instagram pide verificacion extra, completala")
    log("   en el navegador. El sistema espera hasta 3 minutos.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=120,
            channel="chrome",   # usa el Chrome instalado en el sistema
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()

        log(">> Navegando a Instagram login...")
        page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # Aceptar cookies si aparece el banner
        for sel in [
            'button:has-text("Allow essential and optional cookies")',
            'button:has-text("Accept all")',
            'button:has-text("Aceptar todas")',
        ]:
            try:
                page.click(sel, timeout=3000)
                page.wait_for_timeout(1000)
                break
            except Exception:
                pass

        # Completar credenciales
        try:
            page.wait_for_selector('input[name="username"]', timeout=15000)
            page.fill('input[name="username"]', IG_USER)
            page.wait_for_timeout(400)
            page.fill('input[name="password"]', IG_PASS)
            page.wait_for_timeout(400)
            page.click('button[type="submit"]')
            log(">> Credenciales enviadas. Esperando respuesta de Instagram...")
        except Exception as e:
            log(f"AVISO: No encontre el formulario de login: {e}")
            log("       Completa el login manualmente en el navegador abierto.")

        # Esperar login exitoso (hasta 3 min para verificacion manual)
        log(">> Esperando... (si hay verificacion extra, completala ahora en el navegador)")
        try:
            page.wait_for_url(
                lambda url: (
                    "instagram.com" in url
                    and "/login"     not in url
                    and "/challenge" not in url
                    and "/two_factor" not in url
                ),
                timeout=180_000,
            )

            # Descartar "Guardar info de inicio de sesion"
            for sel in [
                'button:has-text("Save info")',
                'button:has-text("Not now")',
                'button:has-text("Guardar info")',
                'button:has-text("Ahora no")',
            ]:
                try:
                    page.click(sel, timeout=4000)
                    break
                except Exception:
                    pass

            page.wait_for_timeout(2000)

            # Guardar sesion
            ctx.storage_state(path=SESSION)
            log(f"\nOK: Sesion guardada en {SESSION}!")
            log("    El servidor ya puede usarse. Cerrando navegador...")

        except Exception as e:
            log(f"\nERROR: No se completo el login: {e}")
            log("       Verifica que las credenciales en .env sean correctas.")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
