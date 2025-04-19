#!/usr/bin/env python3
import argparse
import requests
from urllib.parse import urljoin
import re

"""
graphql_recon.py
----------------

Este script genera endpoints posibles para GraphQL basándose exclusivamente en
información real extraída desde un archivo de cabeceras capturado con DevTools.

FUNCIONALIDAD:
- Extrae los campos: Request URL, :authority, request-pathname, url, id_client
- También usa Remote Address (IP) y via (infra de CDN o proxies)
- Construye endpoints combinando cada uno con el sufijo `/graphql`
- Siempre muestra las combinaciones generadas
- Con el flag --test, envía una query de introspección (`__typename`) y clasifica la respuesta:
    • "Abierto"                → respuesta válida con datos
    • "Necesita Autenticación" → status 401 o texto Unauthorized
    • "False"                  → cualquier otra respuesta

NO introduce rutas genéricas ni convencionales (como /api, /v1, etc.),
a menos que sean explícitamente incluidas en el archivo de cabeceras.
"""

# ---------------------------
# Extracción: modo por defecto (key en una línea, valor en la siguiente)
# ---------------------------
def extract_params_from_headers(header_file):
    with open(header_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    fields = {
        "request url": None,
        ":authority": None,
        "request-pathname": None,
        "url": None,
        "id_client": None,
        "remote address": None,
        "via": None,
    }

    for i, line in enumerate(lines):
        lower = line.lower()
        for key in fields:
            if lower.startswith(key):
                if i + 1 < len(lines):
                    value = lines[i + 1].strip()
                    if value and not value.lower().startswith(key):
                        fields[key] = value
    return fields

# ---------------------------
# Extracción: modo --oneline (key: value en una misma línea)
# ---------------------------
def extract_params_oneline(header_file):
    with open(header_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    fields = {
        "request url": None,
        ":authority": None,
        "request-pathname": None,
        "url": None,
        "id_client": None,
        "remote address": None,
        "via": None,
    }

    for line in lines:
        lower = line.lower()
        for key in fields:
            if lower.startswith(key + ":"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    fields[key] = parts[1].strip()
    return fields

# ---------------------------
# Generación de endpoints únicamente desde los datos presentes
# ---------------------------
def generate_graphql_endpoints(base_url, parts):
    endpoints = set()
    for path in parts:
        clean = path.strip("/").split("?")[0]
        full_path = f"{clean}/graphql" if clean else "graphql"
        full_url = urljoin(base_url.rstrip("/") + "/", full_path)
        endpoints.add(full_url)
    return sorted(endpoints)

# ---------------------------
# Prueba de endpoints con introspección mínima
# ---------------------------
def test_graphql_endpoint(endpoint):
    try:
        response = requests.post(endpoint, json={"query": "query test { __typename }"}, timeout=5)
        if response.status_code == 401 or "Unauthorized" in response.text:
            return "Necesita Autenticación"
        elif response.status_code == 200 and "data" in response.text:
            return "Abierto"
        else:
            return "False"
    except Exception:
        return "False"

# ---------------------------
# CLI
# ---------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extracción y prueba de endpoints GraphQL a partir de cabeceras DevTools.")
    parser.add_argument("--headers", required=True, help="Archivo de cabeceras exportado desde DevTools.")
    parser.add_argument("--test", action="store_true", help="Probar cada combinación con introspección básica.")
    parser.add_argument("--oneline", action="store_true", help="Soporta formato clave: valor en una sola línea.")
    args = parser.parse_args()

    if args.oneline:
        params = extract_params_oneline(args.headers)
    else:
        params = extract_params_from_headers(args.headers)

    if params.get("request url"):
        base_url = params["request url"]
    elif params.get(":authority"):
        base_url = "https://" + params[":authority"]
    else:
        print("[!] No se pudo determinar una URL base válida.")
        exit(1)

    path_parts = set()
    for key in ["request-pathname", "url", "id_client"]:
        val = params.get(key)
        if val:
            path_parts.add(val.strip())
    path_parts.add("")

    # Endpoints estándar
    endpoints = generate_graphql_endpoints(base_url, path_parts)
    print("\n[*] Posibles endpoints GraphQL generados (basado en valores presentes en el archivo):\n")
    for ep in endpoints:
        print(f" - {ep}")

    if args.test:
        print("\n[*] Resultado de introspección:\n")
        for ep in endpoints:
            result = test_graphql_endpoint(ep)
            print(f"[*] {ep}: {result}")

    # Detectar infraestructura alternativa
    alt_hosts = set()
    remote = params.get("remote address")
    if remote and ":" in remote:
        ip = remote.split(":")[0]
        alt_hosts.add("https://" + ip)

    via = params.get("via")
    if via:
        match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', via)
        if match:
            alt_hosts.add("https://" + match.group(1))

    if alt_hosts:
        print("\n[*] Endpoints alternativos desde infraestructura detectada (Remote Address / VIA):\n")
        for alt_base in alt_hosts:
            alt_endpoints = generate_graphql_endpoints(alt_base, path_parts)
            for ep in alt_endpoints:
                print(f" - {ep}")
            if args.test:
                print("\n[*] Resultado de introspección:\n")
                for ep in alt_endpoints:
                    result = test_graphql_endpoint(ep)
                    print(f"[*] {ep}: {result}")
