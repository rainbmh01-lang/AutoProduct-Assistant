# tarik — Tarik AutoProduct Assistant

> ID: CLI-04  
> Category: `client-work`  
> Original Name: `tarik`  
> Stack: Python 3, Streamlit, Google GenAI SDK, DuckDuckGo Search (ddgs), Pillow  
> Status: active

## One Job
Automate e-commerce product cataloging: extract precise French titles, generate structured technical descriptions, discover high-resolution product imagery for interactive selection, and download selected assets with WooCommerce-ready HTML.

## Context & Inputs
- **Codebase Root**: `./`
- **Application Logic**: `app.py`
- **Configuration**: `requirements.txt`, `.env.example`, `.streamlit/config.toml`
- **Shared Reference**: `../../../_shared/rules.md`

## Architecture & Workflows
- **Entry Point**: `app.py`
- **Launcher**: `start.bat`
- **Key Modules & Directories**:
  - `app.py`: Streamlit frontend interface, web scraping / search routines, GenAI prompt pipeline, image fetcher.
  - `downloads/`: Output folder receiving downloaded product images organized per product.
  - `history.json`: Local persistence cache of recently processed products.

## Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Start via batch launcher (Windows)
start.bat

# Or direct Streamlit command
streamlit run app.py --browser.gatherUsageStats=false
```

## Outputs
- **Generated Assets**: Downloaded product images inside `downloads/{product_slug}/`
- **Formatted Copy**: WooCommerce HTML description and specifications ready for clipboard copy.

## Human Gate & Verification
Run `streamlit run app.py` and process a test query (e.g. `visseuse crown 14.4v`); confirm French title resolution, description formatting, and image download pipeline.
