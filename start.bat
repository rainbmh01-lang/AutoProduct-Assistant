@echo off
title Tarik AutoProduct Assistant
cd /d "%~dp0"
echo ========================================================
echo  Lancement de Tarik AutoProduct Assistant...
echo  تشغيل أداة طارق لأتمتة إدخال المنتجات...
echo ========================================================
python -m streamlit run app.py --browser.gatherUsageStats=false
pause
