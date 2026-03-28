import streamlit as st
import pandas as pd
import math
import os

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Cotizador Raíz Latina", layout="centered")

# =========================
# CARGAR DATA
# =========================
@st.cache_data
def cargar_datos():
    df = pd.read_excel("dicc_envios.xlsx")
    df.columns = df.columns.str.strip()
    return df

df = cargar_datos()

# =========================
# FUNCIONES
# =========================

def obtener_tarifa(pais, peso):
    tarifas_pais = df[df["Pais"] == pais]

    if tarifas_pais.empty:
        return None

    tarifas_pais = tarifas_pais.sort_values("Kg")
    posibles = tarifas_pais[tarifas_pais["Kg"] >= peso]

    if not posibles.empty:
        return posibles.iloc[0]["Tarifa"]
    else:
        return tarifas_pais.iloc[-1]["Tarifa"]

def calcular_envio(pais, peso_total):
    cajas = math.ceil(peso_total / 14)
    peso_por_caja = peso_total / cajas
    peso_final = math.ceil(peso_por_caja + 1)

    tarifa = obtener_tarifa(pais, peso_final)

    if tarifa is None:
        return None

    total = tarifa * cajas
    return cajas, peso_final, tarifa, total

# =========================
# PDF PRO
# =========================
def generar_pdf_bytes(nombre, direccion, pais, ciudad, telefono, email, valor_productos, envio, total):

    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from datetime import datetime
    from io import BytesIO
    import json

    contador_path = "contador.json"

    if os.path.exists(contador_path):
        with open(contador_path, "r") as f:
            data = json.load(f)
            numero = data.get("contador", 0) + 1
    else:
        numero = 1

    with open(contador_path, "w") as f:
        json.dump({"contador": numero}, f)

    codigo = f"RL-{str(numero).zfill(4)}"
    fecha = datetime.now().strftime("%d/%m/%Y")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=30,leftMargin=30,
                            topMargin=30,bottomMargin=30)

    azul = colors.HexColor("#0B1F3A")
    amarillo = colors.HexColor("#FFD60A")  # MÁS AMARILLO

    estilo_normal = ParagraphStyle(name="Normal", fontSize=10, leading=14)

    estilo_subtitulo = ParagraphStyle(
        name="Subtitulo",
        fontSize=10,  # MÁS PEQUEÑO
        textColor=colors.white,
        backColor=azul,
        alignment=1,
        spaceBefore=4,
        spaceAfter=4
    )

    elementos = []

    # LOGO PROPORCIONAL
    logo = Image("logo.png", width=2.5*inch, height=1.7*inch)

    info = Paragraph(
        f"<b>Fecha:</b> {fecha}<br/><b>Cotización:</b> {codigo}",
        estilo_normal
    )

    header = Table([[logo, info]], colWidths=[260, 240])
    header.setStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")])

    elementos.append(header)
    elementos.append(Spacer(1, 10))

    # SUBTITULO
    elementos.append(Paragraph("COTIZACIÓN ENVÍO INTERNACIONAL", estilo_subtitulo))
    elementos.append(Spacer(1, 12))

    from_data = f"""
    <b>FROM:</b><br/>
    RAÍZ LATINA BEAUTY SUPPLY<br/>
    Medellín, Colombia<br/>
    +57 3242128894<br/>
    raizlatinaexpo@gmail.com
    """

    to_data = f"""
    <b>TO:</b><br/>
    {nombre}<br/>
    {direccion}<br/>
    {ciudad}<br/>
    {pais}<br/>
    {telefono}<br/>
    {email}
    """

    tabla_info = Table([
        [Paragraph(from_data, estilo_normal), Paragraph(to_data, estilo_normal)]
    ], colWidths=[270, 270])

    elementos.append(tabla_info)
    elementos.append(Spacer(1, 18))

    data = [
        ["Concepto", "Valor (USD)"],
        ["Valor productos", f"${valor_productos:,.2f}"],
        ["Tarifa envío", f"${envio:,.2f}"],
        ["TOTAL", f"${total:,.2f}"],
    ]

    tabla = Table(data, colWidths=[300, 240])

    tabla.setStyle([
        ("BACKGROUND", (0,0), (-1,0), azul),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("BACKGROUND", (0,-1), (-1,-1), amarillo),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("ALIGN", (1,1), (-1,-1), "RIGHT")
    ])

    elementos.append(tabla)
    elementos.append(Spacer(1, 18))

    elementos.append(Paragraph("<b>Transportadora aliada:</b> DHL", estilo_normal))
    elementos.append(Paragraph("<b>Incoterms:</b> DAP", estilo_normal))
    elementos.append(Spacer(1, 12))

    metodos = """
    <b>Métodos de pago:</b><br/>
    • Banco Europa: Transferencia en EUR<br/>
    • Banco Estados Unidos: Transferencia en USD<br/>
    • Banco Colombia: Transferencia en COP
    """

    elementos.append(Paragraph(metodos, estilo_normal))

    doc.build(elementos)
    buffer.seek(0)

    nombre_archivo = f"{nombre.replace(' ', '_')}_{codigo}.pdf"

    return buffer, nombre_archivo

# =========================
# UI
# =========================

st.image("logo.png", width=350)
st.markdown("## 🌎 Cotizador Internacional Raíz Latina")
st.markdown("---")

tipo = st.selectbox("📦 Tipo de cotización", ["Express", "Cliente"])

paises = sorted(df["Pais"].dropna().unique())

col1, col2 = st.columns(2)
with col1:
    pais = st.selectbox("🌍 País destino", paises)
with col2:
    peso_total = st.number_input("⚖️ Peso total (Kg)", min_value=0.1)

valor_productos = 0

if tipo == "Cliente":
    st.markdown("### 📋 Datos del cliente")

    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre")
        direccion = st.text_input("Dirección")
        ciudad = st.text_input("Ciudad / Código Postal")

    with col2:
        telefono = st.text_input("Teléfono")
        email = st.text_input("Email")
        valor_productos = st.number_input("💰 Valor productos (USD)", min_value=0.0)

st.markdown("---")

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    cotizar_btn = st.button("💰 Cotizar")
with col_btn2:
    limpiar_btn = st.button("🧹 Limpiar")

if limpiar_btn:
    st.rerun()

if cotizar_btn:

    resultado = calcular_envio(pais, peso_total)

    if resultado:
        cajas, peso_caja, tarifa, total_envio = resultado

        st.success("✅ Cotización lista")

        # 🔥 DASHBOARD CUADRÍCULA
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        col1.metric("📦 Cajas", cajas)
        col2.metric("⚖️ Peso/caja", f"{peso_caja} Kg")
        col3.metric("💵 Tarifa/caja", f"${tarifa:,.2f}")
        col4.metric("🚚 Total envío", f"${total_envio:,.2f}")

        if tipo == "Cliente":

            total = valor_productos + total_envio

            st.markdown("---")
            st.subheader("💳 Resumen de pago")

            st.metric("🧾 TOTAL A PAGAR", f"${total:,.2f}")

            pdf_buffer, nombre_archivo = generar_pdf_bytes(
                nombre, direccion, pais, ciudad, telefono, email,
                valor_productos, total_envio, total
            )

            st.download_button(
                "📄 Descargar PDF",
                pdf_buffer,
                file_name=nombre_archivo,
                mime="application/pdf"
            )