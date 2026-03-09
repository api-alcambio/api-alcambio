import re
import time
from fastapi import FastAPI, HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI(title="API AlCambio - Vista Tasas")

@app.get("/tasas")
def obtener_tasas():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    resultados = {
        "tasas": {
            "dolar": 0.0,
            "euro": 0.0,
            "usdt": 0.0
        }
    }
    
    try:
        print("Cargando página...")
        driver.get("https://alcambio.app/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # -----------------------------------------------------
        # PASO 1: HACER CLIC EN "TASAS" PARA ABRIR EL MENÚ
        # -----------------------------------------------------
        try:
            # Buscamos el enlace o botón que dice "Tasas"
            xpath_tasas = "//a[contains(text(), 'Tasas')] | //button[contains(text(), 'Tasas')] | //div[contains(text(), 'Tasas')]"
            btn_tasas = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_tasas)))
            
            # Hacemos clic por JS para asegurar que funcione
            driver.execute_script("arguments[0].click();", btn_tasas)
            print("Click en menú 'Tasas' realizado.")
            time.sleep(3) # Esperar a que se abra el panel
        except Exception as e:
            print(f"No se encontró el botón Tasas (quizás ya está abierto): {e}")

        # -----------------------------------------------------
        # PASO 2: EXTRAER TODO EL TEXTO DEL PANEL
        # -----------------------------------------------------
        # Usamos JS para obtener absolutamente todo el texto visible, inputs incluidos
        texto_completo = driver.execute_script("""
            let elems = document.querySelectorAll('input, span, div, p, h1, h2, h3, li');
            let txt = [];
            elems.forEach(e => {
                if(e.value) txt.push(e.value); // Captura valores de inputs
                if(e.innerText) txt.push(e.innerText); // Captura texto visible
            });
            return txt.join(' \\n ');
        """)
        
        print("--- Texto capturado para análisis ---")
        # print(texto_completo) # Descomenta si quieres ver qué ve el robot

        # -----------------------------------------------------
        # PASO 3: BUSCAR PATRONES ESPECÍFICOS (REGEX)
        # -----------------------------------------------------
        
        # Buscar Dólar BCV
        # Patrón: "Dólar" seguido de números decimales y "Bs" (salteando "BCV" si es necesario)
        match_dolar = re.search(r'Dólar.*?(\d+(?:[.,]\d+))\s*Bs', texto_completo, re.IGNORECASE)
        if match_dolar:
            valor = match_dolar.group(1).replace(',', '.')
            resultados["tasas"]["dolar"] = float(valor)
            print(f"Dólar BCV detectado: {valor}")

        # Buscar Euro
        # Patrón: "Euro" seguido de números y "Bs"
        match_euro = re.search(r'Euro.*?(\d+(?:[.,]\d+))\s*Bs', texto_completo, re.IGNORECASE)
        if match_euro:
            valor = match_euro.group(1).replace(',', '.')
            resultados["tasas"]["euro"] = float(valor)
            print(f"Euro detectado: {valor}")

        # Buscar USDT (Promedio)
        # Patrón: "Promedio" seguido de números y "Bs" (para no confundir con Compra/Venta)
        match_usdt = re.search(r'Promedio.*?(\d+(?:[.,]\d+))\s*Bs', texto_completo, re.IGNORECASE)
        if match_usdt:
            valor = match_usdt.group(1).replace(',', '.')
            resultados["tasas"]["usdt"] = float(valor)
            print(f"USDT Promedio detectado: {valor}")
            
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        driver.quit()
        
    return resultados

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)