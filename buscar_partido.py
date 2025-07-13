import asyncio
import datetime
import re
import requests
from playwright.async_api import async_playwright

# Configuraciones
mi_equipo = "FUTSAL SANSE-MOARE"
webhook_url = "https://futsal-bot.onrender.com/"  # 👈 tu URL pública de N8N

def obtener_jornada():
    # Fecha de la primera jornada real
    fecha_inicio = datetime.datetime(2024, 9, 28)
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

        # Cookies
        try:
            await page.click("text=ACEPTO", timeout=5000)
            print("✅ Cookies aceptadas")
        except:
            print("⚠️ No apareció banner de cookies")

        # Scroll
        for _ in range(5):
            await page.mouse.wheel(0, 800)
            await asyncio.sleep(1)

        await page.wait_for_function(
            f"""() => document.body.innerText.toLowerCase().includes("{mi_equipo.lower()}")""",
            timeout=20000
        )
        print(f"🔍 Buscando datos del equipo '{mi_equipo}'...")

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

                    # Mostrar datos
                    print("✅ Partido detectado:")
                    print(f"📅 Fecha: {fecha}")
                    print(f"🕒 Hora: {hora}")
                    print(f"🆚 Rival: {rival}")
                    print(f"📊 Resultado: {resultado}")
                    print(f"🏟️ Campo: {campo}")

                    # Enviar a N8N
                    data = {
                        "fecha": fecha,
                        "hora": hora,
                        "campo": campo,
                        "resultado": resultado,
                        "rival": rival,
                        "jornada": jornada_actual
                    }

                    print("📡 Enviando datos al Webhook...")
                    response = requests.post(webhook_url, json=data)
                    print(f"✅ Estado del Webhook: {response.status_code}")
                except Exception as e:
                    print(f"⚠️ Error extrayendo datos: {e}")
                break
        else:
            print("🚫 No se encontró el equipo en la jornada.")

        await browser.close()

asyncio.run(buscar_equipo())
