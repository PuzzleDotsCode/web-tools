#!/bin/bash

# Variables de entrada
INPUT_FILE=""
SINGLE_URL=""
SHOW_ERRORS=false
ENABLE_GTM=false
CUSTOM_NAME="temp.html"
LOAD_EXISTING_HTML=""

OUTPUT_DIR="output-files"

show_help() {
    echo "Web Crawler: Download index, extracts links, GTM IDs, and folder structure from a webpage."
    echo ""
    echo "Usage:"
    echo "  $0 urls.txt                             # Scan file with list of URLs"
    echo "  $0 --url https://example.com            # Scan a single URL"
    echo ""
    echo "Options:"
    echo "  --gtm                 Enable GTM extraction"
    echo "  --name <filename>     Name for downloaded HTML (default: temp.html)"
    echo "  --load <filename>     Load existing HTML file (skip wget)"
    echo "  --error               Show failed URLs at the end"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --url https://example.com --name page.html --gtm"
    echo "  $0 urls.txt --error"
}

# Argument parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        --url)
            SINGLE_URL="$2"
            shift 2
            ;;
        --name)
            CUSTOM_NAME="$2"
            shift 2
            ;;
        --load)
            LOAD_EXISTING_HTML="$2"
            shift 2
            ;;
        --gtm)
            ENABLE_GTM=true
            shift
            ;;
        --error)
            SHOW_ERRORS=true
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

# Validación de entrada
if [[ -z "$SINGLE_URL" && -z "$INPUT_FILE" && -z "$LOAD_EXISTING_HTML" ]]; then
    echo "[!] Missing input: provide --url, file.txt or --load"
    show_help
    exit 1
fi

# Crear carpeta de salida
mkdir -p "$OUTPUT_DIR"

# GLOBAL FILES (redirigidos a output-files/)
URL_FILE="$OUTPUT_DIR/$CUSTOM_NAME"
HREF_FILE="$OUTPUT_DIR/href.txt"
SRC_FILE="$OUTPUT_DIR/src.txt"
IMAGES_FILE="$OUTPUT_DIR/images.txt"
IMAGES_BASE64_FILE="$OUTPUT_DIR/images_base64.txt"
CLEAN_HREF_FILE="$OUTPUT_DIR/clean_href.txt"
CLEAN_SRC_FILE="$OUTPUT_DIR/clean_src.txt"
FOLDER_TREE_FILE="$OUTPUT_DIR/folder_tree.txt"
NO_GTM_FILE="$OUTPUT_DIR/noGTM.txt"

# Reset output files
rm -f "$HREF_FILE" "$SRC_FILE" "$IMAGES_FILE" "$IMAGES_BASE64_FILE" "$CLEAN_HREF_FILE" "$CLEAN_SRC_FILE" "$FOLDER_TREE_FILE"
touch "$FOLDER_TREE_FILE"

# Función: Descargar página y/o analizar GTM
process_url() {
    local URL="$1"
    echo "[*] Processing: $URL"

    if [[ -z "$LOAD_EXISTING_HTML" ]]; then
        wget -q --user-agent="Mozilla/5.0" "$URL" -O "$URL_FILE"
    fi

    if [[ "$ENABLE_GTM" = true ]]; then
        GTM_LINE=$(grep 'GTM-' "$URL_FILE" | head -n 1)

        if [[ -n "$GTM_LINE" ]]; then
            MATCHED=$(echo "$GTM_LINE" | sed -nE "s/.*\(([^)]*'GTM-[^)]*)\).*/\1/p")
            GTM_ID=$(echo "$MATCHED" | awk -F ',' '{print $5}' | tr -d "'")
            if [[ -n "$GTM_ID" ]]; then
                echo "[*] '$GTM_ID' > $URL"
            else
                echo "[!] No GTM ID found in JS > $URL"
                echo "$URL" >> "$NO_GTM_FILE"
            fi
        else
            echo "[!] No GTM script found > $URL"
            echo "$URL" >> "$NO_GTM_FILE"
        fi
    fi
}

# Función: Extracción de links, análisis y árbol de carpetas
get_links() {
    grep -oP "href\s*=\s*([\"'])?\K[^\"' >]+" "$URL_FILE" | sort -u > "$HREF_FILE"
    grep -oP "src\s*=\s*([\"'])?\K[^\"' >]+" "$URL_FILE" | sort -u > "$SRC_FILE"

    grep -Ei 'base64' "$HREF_FILE" > "$IMAGES_BASE64_FILE"
    grep -Ei '\.(png|jpe?g|gif|webp|bmp|ico)(\?|$)|/images?/|/img/' "$HREF_FILE" > "$IMAGES_FILE"
    grep -Evi 'base64|\.(png|jpe?g|gif|webp|bmp|ico)(\?|$)|/images?/|/img/' "$HREF_FILE" > "$CLEAN_HREF_FILE"
    grep -Evi 'base64|\.(png|jpe?g|gif|webp|bmp|ico)(\?|$)|/images?/|/img/' "$SRC_FILE" > "$CLEAN_SRC_FILE"

    local input="$CLEAN_HREF_FILE"
    local abs_urls=$(mktemp)
    local rel_urls=$(mktemp)

    grep -E '^https?://' "$input" > "$abs_urls"
    grep -vE '^https?://' "$input" | grep -E '^/' > "$rel_urls"

    echo -e "========= ROOT DOMAINS =========\n" >> "$FOLDER_TREE_FILE"
    cut -d/ -f1,2,3 "$abs_urls" | sort -u >> "$FOLDER_TREE_FILE"

    echo -e "\n========= DEPTH 1 (ABSOLUTE) =========\n" >> "$FOLDER_TREE_FILE"
    awk -F/ 'NF==4' "$abs_urls" >> "$FOLDER_TREE_FILE"

    echo -e "\n========= DEPTH 2 (ABSOLUTE) =========\n" >> "$FOLDER_TREE_FILE"
    awk -F/ 'NF==5' "$abs_urls" >> "$FOLDER_TREE_FILE"

    echo -e "\n========= DEPTH 1 (RELATIVE) =========\n" >> "$FOLDER_TREE_FILE"
    awk -F/ 'NF==2' "$rel_urls" >> "$FOLDER_TREE_FILE"

    echo -e "\n========= DEPTH 2 (RELATIVE) =========\n" >> "$FOLDER_TREE_FILE"
    awk -F/ 'NF==3' "$rel_urls" >> "$FOLDER_TREE_FILE"

    echo -e "\n[✓] Folder tree saved in $FOLDER_TREE_FILE"

    # Preview on screen
    echo -e "\n========= ROOT DOMAINS =========\n"
    cut -d/ -f1,2,3 "$abs_urls" | sort -u | head -n 5

    echo -e "\n========= DEPTH 1 (ABSOLUTE) =========\n"
    awk -F/ 'NF==4' "$abs_urls" | head -n 5

    echo -e "\n========= DEPTH 2 (ABSOLUTE) =========\n"
    awk -F/ 'NF==5' "$abs_urls" | head -n 5

    echo -e "\n========= DEPTH 1 (RELATIVE) =========\n"
    awk -F/ 'NF==2' "$rel_urls" | head -n 5

    echo -e "\n========= DEPTH 2 (RELATIVE) =========\n"
    awk -F/ 'NF==3' "$rel_urls" | head -n 5

    rm -f "$abs_urls" "$rel_urls"
}

get_inputs() {
    echo -e "========= INPUT ELEMENTS =========\n"
    grep -oi '<input[^>]*>' "$URL_FILE"
    echo ""
}

get_buttons() {
    echo -e "========= BUTTON ELEMENTS =========\n"
    grep -oi '<button[^>]*>' "$URL_FILE"
    echo ""
}

# MAIN LOGIC
if [[ -n "$SINGLE_URL" ]]; then
    process_url "$SINGLE_URL"
    if [[ "$ENABLE_GTM" != true ]]; then
        get_links
        get_inputs
        get_buttons
    fi
elif [[ -n "$INPUT_FILE" && -f "$INPUT_FILE" ]]; then
    while IFS= read -r URL || [[ -n "$URL" ]]; do
        process_url "$URL"
        if [[ "$ENABLE_GTM" != true ]]; then
            get_links
            get_inputs
            get_buttons
        fi
    done < "$INPUT_FILE"
else
    process_url "local"
    if [[ "$ENABLE_GTM" != true ]]; then
        get_links
        get_inputs
        get_buttons
    fi
fi

# Mostrar errores si corresponde
if [[ "$SHOW_ERRORS" = true && -f "$NO_GTM_FILE" ]]; then
    echo -e "\n== URLs without GTM ID =="
    cat "$NO_GTM_FILE"
    rm -f "$NO_GTM_FILE"
fi
