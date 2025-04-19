#!/bin/bash

if [[ "$1" == "-h" || "$1" == "--help" || -z "$1" ]]; then
    echo "Analizador de Bundles para Web Apps Modernas"
    echo "Descarga y analiza JS, JSX, TS, TSX con LinkFinder y SecretFinder"
    echo
    echo "Uso:"
    echo "  $0 https://target.com [--bundles ruta_relativa/]"
    echo
    echo "Ejemplo:"
    echo "  $0 https://example.com --bundles _next/static/chunks/"
    exit 0
fi

if [[ ! "$1" =~ ^https?:// ]]; then
    echo "[!] El primer argumento debe ser una URL válida (ej: https://target.com)"
    exit 1
fi

TARGET="$1"
BUNDLE_RELATIVE=""
shift

while [[ $# -gt 0 ]]; do
    case "$1" in
        --bundles)
            BUNDLE_RELATIVE="$2"
            shift 2
            ;;
        *)
            echo "[!] Opción no reconocida: $1"
            exit 1
            ;;
    esac
done

OUTPUT_DIR="js_analysis_output"
JS_DIR="$OUTPUT_DIR/js_files"
REPORT="$OUTPUT_DIR/report_$(echo $TARGET | sed 's~https\?://~~;s~/~_~g').txt"

mkdir -p "$JS_DIR"
mkdir -p "$OUTPUT_DIR"

echo "[*] Analizando $TARGET"
echo "[*] Descargando archivos JS, JSX, TS, TSX desde HTML inicial..."

USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Extraer y procesar cada script desde el HTML
curl -s -A "$USER_AGENT" "$TARGET" | \
grep -Eo 'src=["'\''"]([^"'\''"]+\.(js|jsx|ts|tsx))["'\''"]' | \
cut -d'"' -f2 | while read -r JS_PATH; do

    # Construcción segura de URL sin doble slash
    if [[ "$JS_PATH" =~ ^https?:// ]]; then
        JS_URL="$JS_PATH"
    elif [[ "$JS_PATH" =~ ^// ]]; then
        JS_URL="http:${JS_PATH}"
    else
        JS_URL="${TARGET%/}/${JS_PATH#/}"
    fi

    FILE_NAME=$(basename "$JS_URL" | cut -d'?' -f1)

    # Validación de URL antes de descargar
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -A "$USER_AGENT" -H "Referer: $TARGET" "$JS_URL")

    if [[ "$HTTP_CODE" == "200" ]]; then
        echo "  [+] $JS_URL → $JS_DIR/$FILE_NAME"
        curl -s -A "$USER_AGENT" \
             -H "Referer: $TARGET" \
             -H "Accept: text/javascript, application/javascript, */*;q=0.8" \
             -H "Accept-Language: en-US,en;q=0.9" \
             "$JS_URL" -o "$JS_DIR/$FILE_NAME"
    else
        echo "  [!] ❌ URL inválida o inaccesible ($HTTP_CODE): $JS_URL"
    fi
done

# Descarga adicional desde ruta --bundles si fue especificada
if [ -n "$BUNDLE_RELATIVE" ]; then
    FULL_BUNDLE_URL="${TARGET%/}/${BUNDLE_RELATIVE#/}"
    echo "[*] Descargando bundles desde: $FULL_BUNDLE_URL"
    wget --user-agent="$USER_AGENT" \
         --referer="$TARGET" \
         -q -r -l1 -nd -A "js,jsx,ts,tsx" "$FULL_BUNDLE_URL" -P "$JS_DIR"
fi

echo "[*] Ejecutando herramientas sobre los archivos descargados..."
echo "=== Informe de análisis para $TARGET ===" > "$REPORT"

shopt -s nullglob
JS_FILES=("$JS_DIR"/*.{js,jsx,ts,tsx})
shopt -u nullglob

# LINKFINDER
echo -e "\n--- LINKFINDER (endpoints) ---" >> "$REPORT"
if [ ${#JS_FILES[@]} -eq 0 ]; then
    echo "No se encontraron archivos para analizar." >> "$REPORT"
else
    for f in "${JS_FILES[@]}"; do
        echo "[Archivo: $(basename "$f")]" >> "$REPORT"
        python3 LinkFinder/linkfinder.py -i "$f" -o cli >> "$REPORT"
    done
fi

# SECRETFINDER
echo -e "\n--- SECRETFINDER (secretos embebidos) ---" >> "$REPORT"
if [ ${#JS_FILES[@]} -eq 0 ]; then
    echo "No se encontraron archivos para analizar." >> "$REPORT"
else
    for f in "${JS_FILES[@]}"; do
        echo "[Archivo: $(basename "$f")]" >> "$REPORT"
        python3 SecretFinder/SecretFinder.py -i "$f" -o cli >> "$REPORT"
    done
fi

echo "[✓] Análisis finalizado. Informe generado en: $REPORT"
