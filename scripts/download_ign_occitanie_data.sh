#!/bin/bash
#
# Download IGN Open Data for Occitanie Departments
# Uses the IGN open data download URLs for geographic data enrichment
#

# Configuration
OUTPUT_DIR="data/ign_opendata"
LOG_FILE="$OUTPUT_DIR/download.log"

# Occitanie department codes
OCCITANIE_DEPTS=(
    "009"  # Ariège
    "011"  # Aude
    "012"  # Aveyron
    "030"  # Gard
    "031"  # Haute-Garonne
    "032"  # Gers
    "034"  # Hérault
    "046"  # Lot
    "048"  # Lozère
    "065"  # Hautes-Pyrénées
    "066"  # Pyrénées-Orientales
    "081"  # Tarn
    "082"  # Tarn-et-Garonne
)

# Products to download (comment out ones you don't need)
PRODUCTS=(
    "BDTOPO"        # Topographic database - Essential for spots
    "RGEALTI"       # Elevation model - Critical for hiking
    # "BDFORET"     # Forest database - Good for camping spots
    # "BDORTHO"     # Orthophotography - Large files (15-20GB per dept)
    # "RPG"         # Agricultural parcels - To avoid private land
)

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "Starting IGN data download for Occitanie - $(date)" > "$LOG_FILE"

# Function to download a file with retry
download_with_retry() {
    local url=$1
    local output_file=$2
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        echo "Downloading: $output_file (attempt $((retry_count+1)))"
        
        if wget -c "$url" -O "$output_file" >> "$LOG_FILE" 2>&1; then
            echo "✅ Success: $output_file" | tee -a "$LOG_FILE"
            return 0
        else
            echo "❌ Failed: $output_file (attempt $((retry_count+1)))" | tee -a "$LOG_FILE"
            retry_count=$((retry_count+1))
            sleep 5
        fi
    done
    
    echo "❌ Failed after $max_retries attempts: $output_file" | tee -a "$LOG_FILE"
    return 1
}

# Download each product for each department
total_downloads=$((${#OCCITANIE_DEPTS[@]} * ${#PRODUCTS[@]}))
current_download=0

echo "📥 Downloading $total_downloads files for Occitanie..."

for product in "${PRODUCTS[@]}"; do
    echo -e "\n📦 Downloading $product data..."
    product_dir="$OUTPUT_DIR/$product"
    mkdir -p "$product_dir"
    
    for dept in "${OCCITANIE_DEPTS[@]}"; do
        current_download=$((current_download+1))
        progress=$((current_download * 100 / total_downloads))
        
        echo -e "\n[$current_download/$total_downloads - $progress%] Department $dept"
        
        # Construct URL based on product
        if [ "$product" == "RPG" ]; then
            # RPG uses region codes, not department
            case $dept in
                "009"|"031"|"065") region="R76" ;;  # Occitanie
                *) region="R76" ;;
            esac
            url="https://wxs.ign.fr/rpg/telechargement/prepackage/RPG_${region}_latest.7z"
            output_file="$product_dir/RPG_${region}_latest.7z"
        else
            url="https://wxs.ign.fr/${product,,}/telechargement/prepackage/${product}_D${dept}_latest.7z"
            output_file="$product_dir/${product}_D${dept}_latest.7z"
        fi
        
        # Skip if already downloaded
        if [ -f "$output_file" ]; then
            echo "⏭️  Already exists: $(basename $output_file)"
            continue
        fi
        
        # Download the file
        download_with_retry "$url" "$output_file"
    done
done

echo -e "\n✅ Download complete!" | tee -a "$LOG_FILE"
echo "Files saved to: $OUTPUT_DIR" | tee -a "$LOG_FILE"

# Optional: Extract files
read -p "Extract downloaded files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Extracting archives..."
    
    for product in "${PRODUCTS[@]}"; do
        product_dir="$OUTPUT_DIR/$product"
        
        for archive in "$product_dir"/*.7z; do
            if [ -f "$archive" ]; then
                echo "Extracting: $(basename $archive)"
                extract_dir="${archive%.7z}"
                mkdir -p "$extract_dir"
                7z x -o"$extract_dir" "$archive" >> "$LOG_FILE" 2>&1
            fi
        done
    done
    
    echo "✅ Extraction complete!"
fi

# Summary
echo -e "\n📊 Download Summary:"
echo "-------------------"
for product in "${PRODUCTS[@]}"; do
    count=$(find "$OUTPUT_DIR/$product" -name "*.7z" 2>/dev/null | wc -l)
    size=$(du -sh "$OUTPUT_DIR/$product" 2>/dev/null | cut -f1)
    echo "$product: $count files, $size total"
done

echo -e "\n💡 Next steps:"
echo "1. Extract the .7z files: 7z x filename.7z"
echo "2. Load shapefiles into GIS software or Python"
echo "3. Use BDTOPO for water features and trails"
echo "4. Use RGEALTI for elevation profiles"
echo "5. Cross-reference with your spots database"