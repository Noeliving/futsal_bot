import asyncio
import datetime
import re
from playwright.async_api import async_playwright

mi_equipo = "FUTSAL SANSE-MOARE"

# Calcular jornada automáticamente
def obtener_jornada():
    base_jornada = 1
    fecha_inicio = datetime.datetime(2024, 9, 28)  # primera jornada de tu liga
    hoy = datetime.datetime.today()
    semanas = (hoy - fecha_inicio).days // 7
    return base_jornada + semanas

jornada_actual = obtener_jornada()
url = f"https://www.rffm.es/competicion/resultados-y-jornadas?temporada=20&competicion=21434281&grupo=22633526&jornada={jornada_actual}&tipojuego=3"

async def buscar_equipo():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        try:
            await page.click("text=ACEPTO", timeout=5000)
        except:
            pass

        for _ in range(6):
            await page.mouse.wheel(0, 1000)
            await asyncio.sleep(1)

        await page.wait_for_function(
            f"""() => document.body.innerText.toLowerCase().includes("{mi_equipo.lower()}")""",
            timeout=20000
        )

        filas = await page.locator("table.tablaCalendario >> div.MuiGrid-container").all()
        for i, fila in enumerate(filas):
            texto = await fila.inner_text()
            if mi_equipo.lower() in texto.lower():
                resultado = re.search(r"(\d+\s*-\s*\d+)", texto).group(1)
                fecha = re.search(r"\d{2}/\d{2}/\d{4}", texto).group()
                hora = re.search(r"\d{2}:\d{2}h", texto).group()
                campo = re.search(r"Lugar:\s*(.*)", texto).group(1)
                partes = texto.split(resultado)
                local = partes[0].strip().splitlines()[-1].strip()
                visitante = partes[1].strip().splitlines()[0].strip()

                print(f"🏠 Local: {local}")
                print(f"🆚 Visitante: {visitante}")
                print(f"📅 Fecha: {fecha}")
                print(f"🕒 Hora: {hora}")
                print(f"📊 Resultado: {resultado}")
                print(f"🏟️ Campo: {campo}")
                break
        await browser.close()

asyncio.run(buscar_equipo())

