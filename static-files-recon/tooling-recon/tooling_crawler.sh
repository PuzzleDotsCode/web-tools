#!/bin/bash

# Variables de entrada
INPUT_FILE=""
SINGLE_URL=""
ENABLE_GTM=false
OUTPUT_DIR="output-ids"
GTM_OUTPUT_FILE="$OUTPUT_DIR/gtm_results.txt"

show_help() {
    echo "IDs Extractor: Extracts IDs from tools in a webpage."
    echo ""
    echo "Usage:"
    echo "  $0 urls.txt                       # Scan file with list of URLs"
    echo "  $0 --url https://example.com      # Scan a single URL"
    echo ""
    echo "Options:"
    echo "  --gtm                 Enable GTM extraction (required)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --url https://example.com --gtm"
    echo "  $0 urls.txt --gtm"
}

# Argument parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        --url)
            SINGLE_URL="$2"
            shift 2
            ;;
        --gtm)
            ENABLE_GTM=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            INPUT_FILE="$1"
            shift
            ;;
    esac
done

# Validación
if [[ "$ENABLE_GTM" != true ]]; then
    echo "[!] You must enable --gtm to run this script."
    show_help
    exit 1
fi

if [[ -z "$SINGLE_URL" && -z "$INPUT_FILE" ]]; then
    echo "[!] Missing input: provide --url or a list file"
    show_help
    exit 1
fi

# Crear carpeta de salida
mkdir -p "$OUTPUT_DIR"

# Limpiar el archivo de salida
> "$GTM_OUTPUT_FILE"

# Función: procesar una URL
process_url() {
    local URL="$1"
    echo "[*] Processing: $URL"

    local TEMP_FILE=$(mktemp)
    wget -q --user-agent="Mozilla/5.0" "$URL" -O "$TEMP_FILE"

    local GTM_LINE=$(grep 'GTM-' "$TEMP_FILE" | head -n 1)

    if [[ -n "$GTM_LINE" ]]; then
        local MATCHED=$(echo "$GTM_LINE" | sed -nE "s/.*\(([^)]*'GTM-[^)]*)\).*/\1/p")
        local GTM_ID=$(echo "$MATCHED" | awk -F ',' '{print $5}' | tr -d "'")
        if [[ -n "$GTM_ID" ]]; then
            echo "[✓] $URL -> $GTM_ID"
            echo "$GTM_ID > $URL" >> "$GTM_OUTPUT_FILE"
        else
            echo "[!] No GTM ID found in JS > $URL"
        fi
    else
        echo "[!] No GTM script found > $URL"
    fi

    rm -f "$TEMP_FILE"
}

# MAIN LOGIC
if [[ -n "$SINGLE_URL" ]]; then
    process_url "$SINGLE_URL"
elif [[ -n "$INPUT_FILE" && -f "$INPUT_FILE" ]]; then
    while IFS= read -r URL || [[ -n "$URL" ]]; do
        process_url "$URL"
    done < "$INPUT_FILE"
else
    echo "[!] File not found: $INPUT_FILE"
    exit 1
fi

echo ""
echo "[✓] Results saved to: $GTM_OUTPUT_FILE"
