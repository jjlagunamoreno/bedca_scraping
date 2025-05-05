from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from openpyxl import Workbook
from bs4 import BeautifulSoup
import time

# CONFIGURACIÓN DEL DRIVER
options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
service = Service("C:/Program Files/chromedriverwin64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 10)

# INICIO
driver.get("https://www.bedca.net/bdpub/index.php")
wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Consulta"))).click()
wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Grupos de alimentos"))).click()

# GRUPOS
wait.until(EC.presence_of_element_located((By.ID, "fglist")))
select = Select(driver.find_element(By.ID, "fglist"))
grupos = [(opt.get_attribute("value"), opt.text.strip()) for opt in select.options if opt.get_attribute("value")]

# EXCEL
wb = Workbook()
ws_resumen = wb.active
ws_resumen.title = "Resumen"
ws_resumen.append(["Grupo", "ID", "Nombre Español", "Nombre Inglés"])

ws_nutrientes = wb.create_sheet(title="Nutrientes")
ws_nutrientes.append([
    "Grupo", "ID", "Nombre Español",
    "Código Foodex", "Parte comestible (%)",
    "Componente", "Valor", "Unidad", "Fuente"
])

# PROCESAR TODOS LOS GRUPOS
for valor, nombre_grupo in grupos:
    try:
        driver.get("https://www.bedca.net/bdpub/index.php")
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Consulta"))).click()
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Grupos de alimentos"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "fglist")))

        fglist_element = driver.find_element(By.ID, "fglist")
        driver.execute_script("arguments[0].scrollIntoView(true);", fglist_element)
        select = Select(fglist_element)
        select.select_by_value(valor)

        driver.find_element(By.NAME, "button").click()
    except Exception as nav_error:
        print(f"🚫 No se pudo cargar el grupo '{nombre_grupo}': {nav_error}")
        continue

    try:
        wait.until(EC.presence_of_element_located((By.ID, "querytable1")))
        filas = driver.find_elements(By.CSS_SELECTOR, "#querytable1 tr")[1:]

        for i in range(len(filas)):
            try:
                filas = driver.find_elements(By.CSS_SELECTOR, "#querytable1 tr")[1:]
                columnas = filas[i].find_elements(By.TAG_NAME, "td")
                if len(columnas) < 3:
                    continue

                alimento_id = columnas[0].text.strip()
                nombre_esp = columnas[1].text.strip()
                nombre_eng = columnas[2].text.strip()

                columnas[1].find_element(By.TAG_NAME, "a").click()
                wait.until(EC.presence_of_element_located((By.ID, "content2")))
                time.sleep(1)

                # Extraer Foodex y Parte comestible usando BeautifulSoup
                html_detalle = driver.find_element(By.ID, "content2").get_attribute("innerHTML")
                soup = BeautifulSoup(html_detalle, "html.parser")

                foodex = "-"
                parte_comestible = "-"

                for p in soup.find_all("p"):
                    b = p.find("b")
                    if b:
                        label = b.text.lower().strip()
                        if "código foodex" in label:
                            foodex = p.get_text().replace("Código foodex:", "").strip()
                        elif "parte comestible" in label:
                            parte_comestible = p.get_text().replace("Parte comestible (%):", "").strip()

                print(f"📘 {alimento_id} - {nombre_esp} ({nombre_eng})")
                print(f"   └ Código Foodex: {foodex}")
                print(f"   └ Parte comestible (%): {parte_comestible}")

                # Guardar en hoja Resumen
                ws_resumen.append([nombre_grupo, alimento_id, nombre_esp, nombre_eng])

                # Nutrientes
                tablas = driver.find_elements(By.XPATH, "//div[@id='content2']//table")
                if tablas:
                    filas_nutrientes = tablas[-1].find_elements(By.TAG_NAME, "tr")
                    for fila in filas_nutrientes:
                        celdas = fila.find_elements(By.TAG_NAME, "td")
                        if len(celdas) == 4:
                            componente = celdas[0].text.strip()
                            valor = celdas[1].text.strip()
                            unidad = celdas[2].text.strip()
                            fuente = celdas[3].text.strip()
                            ws_nutrientes.append([
                                nombre_grupo, alimento_id, nombre_esp,
                                foodex, parte_comestible,
                                componente, valor, unidad, fuente
                            ])

                # Volver al listado
                try:
                    wait.until(EC.element_to_be_clickable((By.ID, "Todos"))).click()
                    wait.until(EC.presence_of_element_located((By.ID, "querytable1")))
                except:
                    print(f"⚠️ No se pudo volver al listado tras: {nombre_esp}")
                    break

            except Exception as fila_error:
                print(f"❌ Error en fila {i} del grupo {nombre_grupo}: {fila_error}")
                continue

        print(f"📦 Grupo completado: {nombre_grupo}")
        time.sleep(2)

    except Exception as e:
        print(f"⚠️ Fallo en grupo {nombre_grupo}: {e}")

# GUARDAR EXCEL
ruta = "C:/Users/Jaime/OneDrive - Medios Audiovisuales Masmedia SL/jj/scripts/bedca_scraping/alimentos_bedca.xlsx"
wb.save(ruta)
driver.quit()
print(f"\n✅ Excel generado correctamente:\n{ruta}")
