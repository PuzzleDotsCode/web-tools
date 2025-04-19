#!/usr/bin/env python3

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from urllib.parse import urlparse

# nombre del script
script_name = Path(sys.argv[0]).name

if len(sys.argv) != 2:
    # print("Uso: python3 {script_name} https://target.com")
    print(f"""
{script_name} - Análisis dinámico de contenido web
  - Cabeceras HTTP (headers)
  - Formularios HTML y sus campos internos
  - Campos de entrada (<input>)
  - Scripts cargados externamente (<script src="...">)
  - Comentarios HTML visibles en el DOM
  - Enlaces internos válidos (relativos y absolutos dentro del mismo dominio)

Uso:
  python3 {script_name} <URL>

Ejemplo:
  python3 {script_name} https://ejemplo.com

""")
    sys.exit(1)

url = sys.argv[1]
output_dir = Path("recon_output")
output_dir.mkdir(exist_ok=True)
filename = url.replace("https://", "").replace("http://", "").replace("/", "_")
output_file = output_dir / f"{filename}.txt"

# enlaces internos
parsed_url = urlparse(url)
base_domain = parsed_url.netloc

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"[*] Navegando a {url}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)

        content = await page.content()

        with output_file.open("w", encoding="utf-8") as f:
            f.write(f"=== Análisis dinámico de URL: {url} ===\n\n")

            # HEADERS
            f.write("--- Headers HTTP ---\n")
            try:
                response = await page.goto(url)
                for k, v in response.headers.items():
                    f.write(f"{k}: {v}\n")
            except:
                f.write("No se pudieron obtener headers.\n")

            # Formularios
            f.write("\n--- Formularios detectados ---\n")
            forms = await page.query_selector_all("form")
            for i, form in enumerate(forms, 1):
                html = await form.inner_html()
                f.write(f"[Formulario {i}]\n{html}\n\n")

            # Inputs
            f.write("\n--- Campos de entrada (input) ---\n")
            inputs = await page.query_selector_all("input")
            for i, inp in enumerate(inputs, 1):
                outer = await inp.evaluate("e => e.outerHTML")
                f.write(f"[Input {i}] {outer}\n")

            # Scripts
            f.write("\n--- Scripts cargados ---\n")
            scripts = await page.query_selector_all("script[src]")
            for s in scripts:
                src = await s.get_attribute("src")
                f.write(f"{src}\n")

            # Comentarios
            f.write("\n--- Comentarios HTML ---\n")
            comments = await page.evaluate("""
                () => {
                    const comments = [];
                    const treeWalker = document.createTreeWalker(document.body, NodeFilter.SHOW_COMMENT, null, false);
                    let node;
                    while (node = treeWalker.nextNode()) {
                        comments.push(node.nodeValue);
                    }
                    return comments;
                }
            """)
            # Limpiar y filtrar comentarios
            # Eliminamos espacios en blanco y saltos de línea
            for c in comments:
                cleaned = c.strip()
                if cleaned:  # solo si no está vacío
                    f.write(f"<!-- {cleaned} -->\n")

            # Enlaces internos
            f.write("\n--- Enlaces internos ---\n")
            links = await page.query_selector_all("a[href]")
            seen = set()
            for link in links:
                href = await link.get_attribute("href")
                if not href or href.startswith("javascript:") or href.startswith("#"):
                    continue
                if (
                    href.startswith("/")
                    or href.startswith(".")
                    or parsed_url.netloc in href  # mismo dominio
                ):
                    if href not in seen:
                        f.write(f"{href}\n")
                        seen.add(href)

        await browser.close()
        print(f"[✓] Análisis guardado en {output_file}")

asyncio.run(main())

