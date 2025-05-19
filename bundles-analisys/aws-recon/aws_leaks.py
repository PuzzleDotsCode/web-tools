#!/usr/bin/env python3
import os
import re
import argparse
from pathlib import Path
import sys

### Nice to analise wordlists
# 1. /usr/share/wordlists/SecLists/Discovery/Variables/awesome-environment-variable-names.txt
# 2. /usr/share/wordlists/SecLists/Discovery/Variables/secret-keywords.txt

DEFAULT_REGEX_PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "aws_secret_key": re.compile(r"(?i)aws.*?(secret|key).*?['\"][A-Za-z0-9/+=]{40}['\"]"),
    "s3_bucket_url": re.compile(r"[a-z0-9.-]{3,63}\.s3\.amazonaws\.com"),
    "graphql_endpoint": re.compile(r"https?://[a-z0-9\-_\.]+/graphql"),
    "api_gateway_url": re.compile(r"https://[a-z0-9\-]+\.execute-api\.[a-z0-9\-]+\.amazonaws\.com/[^\s\"']*"),
    "jwt_token": re.compile(r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"),
    "public_env_var": re.compile(r"(NEXT_PUBLIC_[A-Z0-9_]+|REACT_APP_[A-Z0-9_]+)\s*[:=]\s*[\"']?.+?[\"']?"),
    "s3_bucket_url": re.compile(r"https://[a-z0-9\.\-_]+\.s3\.[a-z0-9\-]+\.amazonaws\.com")
}

SUPPORTED_EXTENSIONS = [".js", ".jsx", ".ts", ".tsx"]

def load_keyword_patterns(source):
    patterns = {}
    words = []

    if os.path.isfile(source):
        try:
            with open(source, "r") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        words.append(word)
        except Exception as e:
            print(f"[!] Error leyendo wordlist: {e}")
    else:
        words = [w.strip() for w in source.split(",") if w.strip()]

    for i, word in enumerate(words):
        patterns[f"keyword_{i}"] = re.compile(re.escape(word))

    return patterns

def analyze_file(filepath, patterns, verbose=False, suppress_errors=False):
    findings = {}
    try:
        with open(filepath, "r", errors="ignore") as f:
            content = f.read()
            for name, pattern in patterns.items():
                matches = pattern.findall(content)
                if matches:
                    unique_matches = list(set(matches))
                    findings[name] = unique_matches
                    if verbose:
                        for match in unique_matches:
                            print(f"[{name}]: {match} |> {filepath}")
    except Exception as e:
        if not suppress_errors:
            print(f"[!] Error leyendo {filepath}: {e}")
    return findings

def find_code_files(directory, exclude=None):
    exclude = exclude or []
    all_files = []
    for p in Path(directory).rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            relative = str(p.relative_to(directory))
            if not any(relative.startswith(ex.strip("/")) for ex in exclude):
                all_files.append(p)
    return all_files

def analyze_directory(files, patterns, verbose=False, suppress_errors=False):
    findings = {}
    for filepath in files:
        result = analyze_file(filepath, patterns, verbose, suppress_errors)
        if result:
            findings[str(filepath)] = result
    return findings

def report(findings, report_dir):
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "aws_leaks_report.txt")
    lines = ["[!] Posibles fugas encontradas:\n"]
    for file, data in findings.items():
        lines.append(f"📄 Archivo: {file}")
        for name, values in data.items():
            lines.append(f"  └─ {name}:")
            for v in values:
                lines.append(f"     • {v}")
        lines.append("")
    try:
        with open(report_path, "a") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[*] Informe guardado en {report_path}")
    except Exception as e:
        print(f"[!] No se pudo guardar el informe: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Análisis pasivo local de fugas estructurales AWS en archivos JS/TS.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Ejemplos de uso:
  python3 aws_leaks.py --folder ./js_bundles
  python3 aws_leaks.py --folder ./js_bundles --wordlist mywords.txt
  python3 aws_leaks.py --folder . --wordlist AKIA,secret_key,graphql --exclude venv,node_modules --no-errors
"""
    )

    parser.add_argument("--folder", required=True, help="Ruta relativa o absoluta al directorio local a analizar.")
    parser.add_argument("--wordlist", help="Palabras clave a buscar: archivo .txt o lista separada por comas.")
    parser.add_argument("--verbose", action="store_true", help="Mostrar progreso en tiempo real.")
    parser.add_argument("--output-report", help="Carpeta donde guardar el informe (default: ./output-report/)")
    parser.add_argument("--exclude", help="Subrutas a excluir, separadas por coma (ej: node_modules,venv,dist)")
    parser.add_argument("--no-errors", action="store_true", help="No mostrar log de archivos si no se detectan fugas.")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    exclude_paths = [p.strip() for p in args.exclude.split(",")] if args.exclude else []
    suppress_errors = args.no_errors

    code_files = find_code_files(args.folder, exclude=exclude_paths)

    if not code_files:
        print(f"[!] No se encontraron archivos .js, .jsx, .ts o .tsx en: {args.folder}")
        exit(1)

    patterns = DEFAULT_REGEX_PATTERNS.copy()

    if args.wordlist:
        patterns.update(load_keyword_patterns(args.wordlist))

    findings = analyze_directory(code_files, patterns, verbose=args.verbose, suppress_errors=suppress_errors)

    if not suppress_errors:
        print("[*] Archivos encontrados para análisis:")
        for f in code_files:
            print(f" - {f}")

    if findings:
        report_dir = args.output_report or "output-report"
        report(findings, report_dir)
        print("[✓] Se detectan archivos objetivo, y se detectaron fugas.")
        exit(0)
    else:
        print("[-] Se detectan archivos objetivo, pero no se detectaron fugas.")
        exit(2)
