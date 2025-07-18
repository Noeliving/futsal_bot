import asyncio
import datetime
import re
import requests
from playwright.async_api import async_playwright

mi_equipo = "FUTSAL SANSE-MOARE"
webhook_url = "https://n8n-service-m2j9.onrender.com:5678/webhook/futsal"  # 🔄 producción

def obtener_jornada():
    fecha_inicio = datetime.datetime(2024, 9, 28)  # primer partido real
    hoy = datetime.datetime.today()
    semanas = (hoy - fecha_inicio).days // 7
    return semanas + 1

jornada_actual = obtener_jornada()
url = f"https://www.rffm.es/competicion/resultados-y-jornadas?temporada=20&competicion=21434281&grupo=22633526&jornada={jornada_actual}&tipojuego=3"

async def buscar_equipo():
    async with async_playwright() as p:
        print(f"🌐 Cargando jornada {jornada_actual}")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        # Aceptar cookies si están
        try:
            await page.click("text=ACEPTO", timeout=5000)
            print("✅ Cookies aceptadas")
        except:
            print("ℹ️ No había cookies que aceptar")

        # Scroll para cargar contenido
        for _ in range(5):
            await page.mouse.wheel(0, 800)
            await asyncio.sleep(1)

        # Espera hasta que aparezca el equipo o timeout
        try:
            await page.wait_for_function(
                f"""() => document.body.innerText.toLowerCase().includes("{mi_equipo.lower()}")""",
                timeout=40000
            )
        except Exception as e:
            print(f"⚠️ No se encontró el equipo en la jornada {jornada_actual}: {e}")
            await browser.close()
            return

        # Buscar datos del equipo en las filas
        filas = await page.locator("table.tablaCalendario >> div.MuiGrid-container").all()
        for fila in filas:
            texto = await fila.inner_text()
            if mi_equipo.lower() in texto.lower():
                try:
                    resultado = re.search(r"(\d+\s*-\s*\d+)", texto).group(1)
                    fecha = re.search(r"\d{2}/\d{2}/\d{4}", texto).group()
                    hora = re.search(r"\d{2}:\d{2}h", texto).group()
                    campo = re.search(r"Lugar:\s*(.*)", texto).group(1)

                    partes = texto.split(resultado)
                    local = partes[0].strip().splitlines()[-1].strip()
                    visitante = partes[1].strip().splitlines()[0].strip()

                    rival = visitante if mi_equipo.lower() in local.lower() else local

                    data = {
                        "fecha": fecha,
                        "hora": hora,
                        "campo": campo,
                        "resultado": resultado,
                        "rival": rival,
                        "jornada": jornada_actual
                    }

                    print("📡 Enviando datos a N8N...")
                    response = requests.post(webhook_url, json=data)
                    print(f"✅ Estado del webhook: {response.status_code}")

                except Exception as e:
                    print(f"⚠️ Error extrayendo datos: {e}")
                break

        await browser.close()

asyncio.run(buscar_equipo())
