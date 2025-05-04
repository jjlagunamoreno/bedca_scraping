from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

# CONFIGURACIÓN DEL DRIVER
options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
service = Service("C:/Program Files/chromedriverwin64/chromedriver.exe")

driver = webdriver.Chrome(service=service, options=options)
driver.get("https://www.bedca.net/bdpub/index.php")

wait = WebDriverWait(driver, 10)

# ENTRAR EN CONSULTA > GRUPOS DE ALIMENTOS
wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Consulta"))).click()
wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Grupos de alimentos"))).click()

# OBTENER LISTA DE VALORES Y TEXTOS (una vez, seguros)
wait.until(EC.presence_of_element_located((By.ID, "fglist")))
select = Select(driver.find_element(By.ID, "fglist"))
valores_opciones = [
    (op.get_attribute("value"), op.text.strip())
    for op in select.options
    if op.get_attribute("value")
]

alimentos = []

# RECORRER CADA OPCIÓN DE GRUPO
for valor, texto in valores_opciones:
    driver.get("https://www.bedca.net/bdpub/index.php")
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Consulta"))).click()
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Grupos de alimentos"))).click()
    wait.until(EC.presence_of_element_located((By.ID, "fglist")))

    select = Select(driver.find_element(By.ID, "fglist"))
    select.select_by_value(valor)
    driver.find_element(By.NAME, "button").click()

    try:
        wait.until(EC.presence_of_element_located((By.ID, "querytable1")))
        rows = driver.find_elements(By.CSS_SELECTOR, "#querytable1 tr")[1:]

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 3:
                alimento_id = cols[0].text.strip()
                nombre_esp = cols[1].text.strip()
                nombre_eng = cols[2].text.strip()
                alimentos.append(f"{alimento_id} - {nombre_esp} / {nombre_eng} ({texto})")

        print(f"✔️ Grupo '{texto}' procesado con {len(rows)} alimentos.")
    except:
        print(f"⚠️ Fallo al procesar grupo: {texto}")

# GUARDAR DATOS
ruta = "C:/Users/Jaime/OneDrive - Medios Audiovisuales Masmedia SL/jj/scripts/bedca_scraping/alimentos.txt"
with open(ruta, "w", encoding="utf-8") as f:
    for a in alimentos:
        f.write(a + "\n")

driver.quit()
print(f"✅ Scraping completado. Total alimentos: {len(alimentos)}. Guardado en:\n{ruta}")
