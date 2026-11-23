import os
import re
import json
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image
import streamlit as st
from ddgs import DDGS

# Try importing Google Generative AI
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Page configuration
st.set_page_config(
    page_title="Tarik AutoProduct | أتمتة إدخال المنتجات",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #4B5563;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# App directories
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = BASE_DIR / "history.json"

# Load history
def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(entry):
    history = load_history()
    history = [h for h in history if h.get("title") != entry.get("title")]
    history.insert(0, entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)

# Helper to sanitize folder name
def sanitize_filename(name):
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = clean.strip().replace(" ", "_")
    return clean[:60] if clean else "product"

# Search Images via DuckDuckGo
def search_images(query, max_images=12):
    try:
        ddgs = DDGS()
        results = list(ddgs.images(query, max_results=max_images))
        valid_results = []
        for r in results:
            img_url = r.get("image") or r.get("thumbnail")
            if img_url and img_url.startswith("http"):
                valid_results.append({
                    "title": r.get("title", ""),
                    "image": img_url,
                    "thumbnail": r.get("thumbnail", img_url),
                    "width": r.get("width", "N/A"),
                    "height": r.get("height", "N/A"),
                    "source": r.get("url", "")
                })
        return valid_results
    except Exception as e:
        return []

# Search Web text for smart fallback
def smart_web_search(query):
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query + " prix algerie fiche technique", max_results=5))
        return results
    except Exception:
        return []

# Generate Title and Description
def generate_product_info(raw_name, api_key=None):
    # 1. First, search web to get context & discover exact model numbers (like CT21055LM)
    web_results = smart_web_search(raw_name)
    web_context = "\n".join([f"- {r.get('title')}: {r.get('body')}" for r in web_results])

    # Extract best candidate title from Algerian/official ecommerce results if available
    best_candidate_title = ""
    for r in web_results:
        t = r.get("title", "")
        # Remove site suffixes
        clean_t = re.sub(r'\s*[-|–—:]\s*(Ouedkniss|Mabricole|Decooutillage|Yamcoo|Facebook|YouTube|Prix).*$', '', t, flags=re.I).strip()
        if len(clean_t) > len(best_candidate_title) and any(w.lower() in clean_t.lower() for w in raw_name.split()[:2]):
            best_candidate_title = clean_t

    prompt = f"""
Tu es un expert en e-commerce d'outillage, quincaillerie et électroménager (marques comme CROWN, INGCO, BEETRO, TOTAL, HONESTPRO, DINGQI) pour un site WooCommerce en Algérie (EdenGroupes).

Nom brut entré par l'utilisateur: "{raw_name}"
Résultats de recherche Web récents trouvés:
{web_context}

TÂCHE:
1. Trouver le NOM EXACT, OFFICIEL ET COMPLET EN FRANÇAIS (avec la marque en MAJUSCULE et la référence modèle exacte si disponible, ex: "Visseuse-Perceuse Sans Fil 14.4V CROWN CT21055LM-1.5BMC (2 Batteries)").
2. Rédiger une fiche technique et description commerciale en français adaptée à WooCommerce.

Réponds sous forme de JSON strict:
{{
  "french_title": "Nom exact complet",
  "search_query": "Requête pour trouver les photos officielles",
  "short_description": "Courte description commerciale",
  "full_description_html": "<h3>Présentation</h3><p>...</p><h3>Caractéristiques Techniques</h3><ul><li>...</li></ul><h3>Contenu du coffret</h3><ul><li>...</li></ul><h3>Points Forts</h3><ul><li>...</li></ul>"
}}
"""
    if api_key and HAS_GENAI:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            txt = response.text.strip()
            if txt.startswith("```json"):
                txt = txt[7:]
            elif txt.startswith("```"):
                txt = txt[3:]
            if txt.endswith("```"):
                txt = txt[:-3]
            data = json.loads(txt.strip())
            return data
        except Exception:
            pass

    # High-quality smart fallback without API key
    final_title = best_candidate_title if best_candidate_title else raw_name.strip().title()
    
    # Generate structured HTML description
    description_html = f"""<h3>Présentation</h3>
<p>Le <strong>{final_title}</strong> est un outil professionnel robuste et performant, idéal pour vos travaux quotidiens et professionnels de haute intensité.</p>

<h3>Caractéristiques Techniques</h3>
<ul>
    <li><strong>Marque & Modèle :</strong> {final_title}</li>
    <li><strong>Conception :</strong> Ergonomique avec poignée antidérapante pour un confort optimal</li>
    <li><strong>Performance :</strong> Moteur puissant et durable avec protection thermique</li>
    <li><strong>Polyvalence :</strong> Conçu pour un usage continu et exigeant</li>
</ul>

<h3>Contenu du Coffret / Accessoires</h3>
<ul>
    <li>1 x {final_title}</li>
    <li>Accessoires de service et adaptateurs standards</li>
    <li>Manuel d'utilisation et consignes de sécurité</li>
</ul>

<h3>Points Forts</h3>
<ul>
    <li>Excellente prise en main et équilibrage du poids</li>
    <li>Matériaux haute résistance et durabilité éprouvée</li>
    <li>Garantie et service après-vente assuré</li>
</ul>"""

    return {
        "french_title": final_title,
        "search_query": final_title,
        "short_description": f"{final_title} - Outil haute performance et durabilité garantie.",
        "full_description_html": description_html
    }

# Function to download images to local folder with fallback
def download_selected_images(images, folder_name):
    save_path = DOWNLOADS_DIR / folder_name
    save_path.mkdir(parents=True, exist_ok=True)
    downloaded_files = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }

    for idx, img_info in enumerate(images, start=1):
        urls_to_try = [img_info.get("image"), img_info.get("thumbnail")]
        success = False

        for url in urls_to_try:
            if not url:
                continue
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    img_data = BytesIO(resp.content)
                    img = Image.open(img_data)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    filename = f"image_{idx}.jpg"
                    filepath = save_path / filename
                    img.save(filepath, "JPEG", quality=95)
                    downloaded_files.append(str(filepath))
                    success = True
                    break
            except Exception:
                continue

    return downloaded_files

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/wrench.png", width=64)
    st.title("⚙️ Paramètres (الإعدادات)")
    
    env_key = os.environ.get("GEMINI_API_KEY", "")
    gemini_key = st.text_input(
        "Clé API Gemini (Optionnelle - اختياري):",
        value=env_key,
        type="password",
        help="يعمل البرنامج بشكل ممتاز بدون أي مفتاح عبر محرك البحث المدمج."
    )
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key

    st.markdown("---")
    st.markdown(f"📂 **Dossier de téléchargement:**\n`{DOWNLOADS_DIR}`")
    
    if st.button("📁 Ouvrir le dossier des téléchargements"):
        try:
            os.startfile(str(DOWNLOADS_DIR))
        except Exception:
            pass

    st.markdown("---")
    st.subheader("🕒 Historique récent (السجل)")
    history_items = load_history()
    if history_items:
        for item in history_items[:8]:
            st.caption(f"• **{item.get('title', 'Sans titre')}**")
    else:
        st.caption("Aucun produit traité pour le moment.")

# --- MAIN CONTENT ---
st.markdown('<div class="main-title">⚡ Tarik AutoProduct Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">أداة طارق للبحث التلقائي: الاسم الكامل بالفرنسية + الوصف التقني + تنزيل 3 صور بجودة عالية</div>', unsafe_allow_html=True)

# Input Row
col_input, col_btn = st.columns([4, 1])
with col_input:
    product_input = st.text_input(
        "Nom brut du produit (اسم المنتج الأولي كما هو):",
        value="VISSEUSE 14.4V CROWN 2 BAT 1.5AH",
        key="prod_query"
    )
with col_btn:
    st.write("")
    st.write("")
    search_clicked = st.button("🔍 Traiter le produit", type="primary", use_container_width=True)

# Process search
if search_clicked and product_input:
    with st.spinner("Analyse du produit et recherche des données officielles..."):
        prod_data = generate_product_info(product_input, gemini_key)
        st.session_state["prod_data"] = prod_data
        
        img_query = prod_data.get("search_query") or product_input
        with st.spinner(f"Recherche des images pour '{img_query}'..."):
            images = search_images(img_query, max_images=9)
            st.session_state["fetched_images"] = images

# Display Results
if "prod_data" in st.session_state:
    data = st.session_state["prod_data"]
    images = st.session_state.get("fetched_images", [])

    st.markdown("---")
    
    # 1. FRENCH TITLE SECTION
    st.subheader("1. 🏷️ Titre officiel en français (الاسم الصحيح الكامل)")
    french_title = data.get("french_title", "")
    edited_title = st.text_input("Titre modifiable :", value=french_title, key="edit_title")
    st.caption("📋 انقر على زر النسخ في الزاوية العلوية اليمنى من المربع:")
    st.code(edited_title, language="text")

    # 2. FRENCH DESCRIPTION SECTION
    st.subheader("2. 📝 Description technique complète (الوصف بالفرنسية)")
    col_desc1, col_desc2 = st.columns([1, 1])
    
    html_desc = data.get("full_description_html", "")
    with col_desc1:
        st.markdown("**Aperçu visuel (المعاينة):**")
        st.markdown(html_desc, unsafe_allow_html=True)

    with col_desc2:
        st.markdown("**Code HTML prêt pour WooCommerce (كود جاهز للنسخ):**")
        st.code(html_desc, language="html")

    # 3. IMAGES SECTION
    st.subheader("3. 🖼️ Sélection et téléchargement des 3 images (الصور)")
    
    if not images:
        st.warning("Aucune image trouvée. Veuillez vérifier le terme de recherche.")
    else:
        st.write("Sélectionnez les 3 meilleures images pour ce produit (les 3 premières sont cochées par défaut) :")
        
        cols = st.columns(3)
        selected_images = []

        for i, img_item in enumerate(images):
            col_idx = i % 3
            with cols[col_idx]:
                st.image(img_item.get("thumbnail") or img_item.get("image"), use_container_width=True)
                default_checked = (i < 3)
                is_selected = st.checkbox(
                    f"Image #{i+1}",
                    value=default_checked,
                    key=f"img_check_{i}"
                )
                if is_selected:
                    selected_images.append(img_item)

        st.markdown("---")
        
        # Download Action
        col_dl, col_info = st.columns([1, 2])
        with col_dl:
            folder_clean = sanitize_filename(edited_title)
            btn_download = st.button(
                f"💾 Télécharger les {len(selected_images)} images sélectionnées",
                type="primary",
                use_container_width=True
            )
            
        with col_info:
            if btn_download:
                if len(selected_images) == 0:
                    st.warning("Veuillez sélectionner au moins une image.")
                else:
                    with st.spinner("Téléchargement des 3 images en cours..."):
                        saved_files = download_selected_images(selected_images, folder_clean)
                        if saved_files:
                            st.success(f"✅ تم بنجاح حفظ {len(saved_files)} صور في المجلد:\n`downloads/{folder_clean}`")
                            save_history({
                                "title": edited_title,
                                "folder": folder_clean,
                                "images_count": len(saved_files)
                            })
                            try:
                                os.startfile(str(DOWNLOADS_DIR / folder_clean))
                            except Exception:
                                pass
