"""
Aplicación Web Interactiva - Cálculo de Elementos en Tensión (AISC 360 LRFD)
=============================================================================
Desarrollada con Streamlit para uso óptimo en Celulares, Tablets y Computadoras.
Incluye:
- Catálogo oficial IMCA (Ángulos LI, Vigas IR, Canales CE, Soleras y Placas).
- Soporte dual: Sistema Métrico (SI) y Sistema Inglés (US).
- Ruptura con líneas de falla rectas o alternadas (tresbolillo, regla s²/4g).
- Bloque de cortante (AISC J4.3).
- Memoria de cálculo técnica descargable.
"""

import streamlit as st
from lector_imca import CatalogoIMCA
from aceros import TABLA_ACEROS, obtener_acero, listar_etiquetas_aceros
from motor_calculo import evaluar_conexion_tension, generar_memoria_texto
from unidades import (
    IN_A_CM, CM_A_IN, IN_A_MM, MM_A_IN,
    KIPS_A_TON, KIPS_A_KG, KSI_A_KG_CM2
)

# 1. Configuración de página (optimizada para móviles)
st.set_page_config(
    page_title="Tensión Acero - AISC LRFD",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="auto"
)

# Cargar catálogo en caché (se carga una sola vez y vuela en velocidad)
@st.cache_resource
def get_catalogo():
    cat = CatalogoIMCA()
    cat.cargar()
    return cat

catalogo = get_catalogo()

# Encabezado visual
st.markdown("""
<div style="background-color:#1e293b; padding:18px; border-radius:12px; margin-bottom:15px; color:white; text-align:center;">
    <h2 style="margin:0; color:#38bdf8;">🏗️ Diseño de Elementos en Tensión</h2>
    <p style="margin:5px 0 0 0; color:#94a3b8; font-size:14px;">Normativa AISC 360 LRFD • Catálogo IMCA • Métrico e Inglés</p>
</div>
""", unsafe_allow_html=True)

# Barra lateral: Sistema de Unidades y Acero
with st.sidebar:
    st.header("⚙️ Configuración General")
    sistema_sel = st.radio(
        "Sistema de Unidades:",
        ["🇺🇸 Sistema Inglés (in, ksi, kips)", "🇲🇽 Sistema Métrico (cm, kg/cm², kg/ton)"],
        index=0
    )
    sistema = "US" if "Inglés" in sistema_sel else "METRICO"

    st.subheader("🔩 Grado de Acero")
    lista_aceros = listar_etiquetas_aceros(sistema)
    acero_sel_txt = st.selectbox("Seleccionar Acero:", lista_aceros, index=0)
    nombre_acero = acero_sel_txt.split("|")[0].strip()
    acero = obtener_acero(nombre_acero)

    if sistema == "METRICO":
        st.info(f"**Fy:** {acero['Fy_kg_cm2']:,.0f} kg/cm²\n\n**Fu:** {acero['Fu_kg_cm2']:,.0f} kg/cm²")
    else:
        st.info(f"**Fy:** {acero['Fy_ksi']:.0f} ksi\n\n**Fu:** {acero['Fu_ksi']:.0f} ksi")

# Estructura principal en columnas / pestañas
col_izq, col_der = st.columns([1.1, 1.2])

with col_izq:
    st.subheader("1. Perfil Estructural")
    tipo_perfil = st.selectbox(
        "Tipo de Elemento:",
        [
            "Placa Personalizada",
            "Perfil LI (Ángulos)",
            "Perfil IR (Vigas W / IPR)",
            "Perfil CE (Canales)",
            "Soleras IMCA"
        ],
        index=0
    )

    perfil = None
    if tipo_perfil == "Placa Personalizada":
        c_ancho, c_esp = st.columns(2)
        if sistema == "METRICO":
            ancho_val = c_ancho.number_input("Ancho (cm):", min_value=0.1, value=24.0, step=1.0)
            esp_val = c_esp.number_input("Espesor (cm o mm):", min_value=0.01, value=0.95, step=0.05)
            t_cm = (esp_val / 10.0) if esp_val > 3.0 else esp_val
            perfil = {
                "tipo": "PLACA",
                "designacion_si": f"Placa {t_cm:.2f} cm x {ancho_val:.1f} cm",
                "designacion_us": f"Placa {t_cm / 2.54:.3f}\" x {ancho_val / 2.54:.2f}\"",
                "area_cm2": ancho_val * t_cm,
                "area_in2": (ancho_val * t_cm) / 6.4516,
                "espesor_cm": t_cm,
                "espesor_in": t_cm / 2.54,
            }
        else:
            ancho_val = c_ancho.number_input("Ancho (in):", min_value=0.1, value=11.0, step=0.5)
            esp_str = c_esp.text_input("Espesor (in, decimal o fracción):", value="1/2")
            try:
                if "/" in esp_str:
                    n, d = esp_str.split("/")
                    t_in = float(n) / float(d)
                else:
                    t_in = float(esp_str)
            except Exception:
                t_in = 0.5
            perfil = CatalogoIMCA.crear_placa_personalizada(ancho_in=ancho_val, espesor_in=t_in)
    else:
        tipo_map = {
            "Perfil LI (Ángulos)": "LI",
            "Perfil IR (Vigas W / IPR)": "IR",
            "Perfil CE (Canales)": "CE",
            "Soleras IMCA": "SOLERA"
        }
        clave_tipo = tipo_map[tipo_perfil]
        etiquetas_perfiles = catalogo.obtener_lista_etiquetas(clave_tipo, sistema=sistema)
        perfil_seleccionado_txt = st.selectbox("Seleccionar del catálogo IMCA:", etiquetas_perfiles, index=0)
        perfil = catalogo.buscar_perfil(clave_tipo, perfil_seleccionado_txt)

    if perfil:
        if sistema == "METRICO":
            st.caption(f"📐 **Área Bruta (Ag):** {perfil.get('area_cm2', 0):.2f} cm² | **Espesor (t):** {perfil.get('espesor_cm', perfil.get('t_mm', 0)/10):.2f} cm")
        else:
            st.caption(f"📐 **Área Bruta (Ag):** {perfil.get('area_in2', 0):.3f} in² | **Espesor (t):** {perfil.get('espesor_in', perfil.get('t_in', 0)):.3f}\"")

    st.markdown("---")
    st.subheader("2. Conexión Atornillada")

    modo_dp = st.radio(
        "Modo de especificación del diámetro:",
        ["Tornillo nominal dt (sumar +1/8\" / +3.18mm autom.)", "Barreno directo dp (ya incluye el 1/8\")"],
        index=0
    )
    modo_str = "TORNILLO" if "nominal" in modo_dp else "BARRENO"

    diam_txt = st.text_input(
        f"Diámetro ({'in o fracción ej. 3/4' if sistema == 'US' else 'cm, mm o pulg ej. 2.22 o 3/4'}):",
        value="3/4" if sistema == "US" else "2.22"
    )

    # Cálculo y preview del barreno
    try:
        s_clean = diam_txt.strip().replace('"', '').replace("'", "")
        if "/" in s_clean:
            n_val, d_val = s_clean.split("/")
            num_d = float(n_val) / float(d_val)
        else:
            num_d = float(s_clean)

        if sistema == "METRICO":
            if modo_str == "TORNILLO":
                if "/" in s_clean or num_d <= 1.5:
                    dp_cm = (num_d + 0.125) * 2.54
                elif num_d < 4.0:
                    dp_cm = num_d + 0.3175
                else:
                    dp_cm = (num_d + 3.175) / 10.0
            else:
                if "/" in s_clean:
                    dp_cm = num_d * 2.54
                elif num_d < 4.0:
                    dp_cm = num_d
                else:
                    dp_cm = num_d / 10.0
            dp_in = dp_cm / 2.54
            st.success(f"➜ **Barreno de cálculo:** dp = **{dp_cm:.2f} cm** ({dp_cm*10:.1f} mm) [ {dp_in:.3f}\" ]")
        else:
            if modo_str == "TORNILLO":
                dp_in = num_d + 0.125
            else:
                dp_in = num_d
            dp_cm = dp_in * 2.54
            st.success(f"➜ **Barreno de cálculo:** dp = **{dp_in:.3f}\"** [ {dp_cm:.2f} cm ]")
    except Exception:
        dp_in = 0.875
        dp_cm = 2.22
        st.warning("Ingrese un diámetro válido.")

    col_barr, col_u = st.columns(2)
    n_barrenos_recta = col_barr.number_input("Barrenos sección recta:", min_value=1, value=2, step=1)
    u_factor = col_u.number_input("Factor U (rezago cortante):", min_value=0.1, max_value=1.0, value=0.90, step=0.05)

    # 3. Perforaciones alternadas (tresbolillo)
    st.markdown("---")
    con_alternadas = st.checkbox("⚡ Activar Perforaciones Alternadas (regla s²/4g)", value=False)
    trayectorias_alt = None

    if con_alternadas:
        st.caption("Configura el patrón y las trayectorias de falla a evaluar:")
        col_s_alt, col_g_alt = st.columns(2)
        s_alt = col_s_alt.number_input(f"Paso 's' ({'in' if sistema == 'US' else 'cm'}):", min_value=0.1, value=4.0 if sistema == "US" else 10.0)
        g_alt = col_g_alt.number_input(f"Gramil 'g' ({'in' if sistema == 'US' else 'cm'}):", min_value=0.1, value=5.0 if sistema == "US" else 12.5)

        t1_c1, t1_c2, t1_c3 = st.columns([1.5, 1, 1])
        t1_nom = t1_c1.text_input("Trayectoria 1:", value="T1 (ABCD)")
        t1_b = t1_c2.number_input("Barrenos T1:", min_value=1, value=2)
        t1_d = t1_c3.number_input("Diagonales T1:", min_value=0, value=0)

        t2_c1, t2_c2, t2_c3 = st.columns([1.5, 1, 1])
        t2_nom = t2_c1.text_input("Trayectoria 2:", value="T2 (ABEFG)")
        t2_b = t2_c2.number_input("Barrenos T2:", min_value=1, value=3)
        t2_d = t2_c3.number_input("Diagonales T2:", min_value=0, value=2)

        t3_c1, t3_c2, t3_c3 = st.columns([1.5, 1, 1])
        t3_nom = t3_c1.text_input("Trayectoria 3:", value="T3 (ABECD)")
        t3_b = t3_c2.number_input("Barrenos T3:", min_value=1, value=3)
        t3_d = t3_c3.number_input("Diagonales T3:", min_value=0, value=2)

        trayectorias_alt = [
            {"nombre": t1_nom, "num_agujeros": int(t1_b), "diagonales": [(s_alt, g_alt)] * int(t1_d)},
            {"nombre": t2_nom, "num_agujeros": int(t2_b), "diagonales": [(s_alt, g_alt)] * int(t2_d)},
            {"nombre": t3_nom, "num_agujeros": int(t3_b), "diagonales": [(s_alt, g_alt)] * int(t3_d)},
        ]

    # 4. Bloque de cortante
    st.markdown("---")
    con_bloque = st.checkbox("📦 Activar Revisión de Bloque de Cortante (AISC J4.3)", value=True)
    config_bloque = {}

    if con_bloque:
        col_bl1, col_bl2 = st.columns(2)
        n_long = col_bl1.number_input("Tornillos línea longitudinal:", min_value=1, value=3, step=1)
        s_bloque = col_bl2.number_input(f"Paso 's' ({'in' if sistema == 'US' else 'cm'}):", min_value=0.1, value=3.0 if sistema == "US" else 8.0)

        col_bl3, col_bl4 = st.columns(2)
        lev_bloque = col_bl3.number_input(f"Dist. borde 'Le' ({'in' if sistema == 'US' else 'cm'}):", min_value=0.1, value=1.5 if sistema == "US" else 4.0)
        wt_bloque = col_bl4.number_input(f"Ancho tensión 'Wt' ({'in' if sistema == 'US' else 'cm'}):", min_value=0.1, value=1.5 if sistema == "US" else 8.0)

        col_bl5, col_bl6 = st.columns(2)
        num_lineas_corte = col_bl5.selectbox("Líneas de cortante:", [1, 2], index=1 if sistema == "METRICO" else 0)
        ubs_factor = col_bl6.selectbox("Factor Ubs (tensión uniforme):", [1.0, 0.5], index=0)

        config_bloque = {
            "n_long": int(n_long),
            "s": float(s_bloque),
            "Le_v": float(lev_bloque),
            "W_t": float(wt_bloque),
            "num_lineas_corte": int(num_lineas_corte),
            "Ubs": float(ubs_factor)
        }

# Columna derecha: Resultados y Memoria
with col_der:
    st.subheader("3. Resultados de Capacidad (AISC LRFD)")

    if perfil and acero:
        # Armar config
        config_calculo = {
            "U": float(u_factor)
        }
        if sistema == "METRICO":
            config_calculo["d_agujero_cm"] = dp_cm
        else:
            config_calculo["d_agujero_in"] = dp_in

        if con_alternadas and trayectorias_alt:
            config_calculo["trayectorias"] = trayectorias_alt
        else:
            config_calculo["num_tornillos_seccion"] = int(n_barrenos_recta)

        if con_bloque:
            config_calculo.update(config_bloque)

        try:
            res = evaluar_conexion_tension(perfil, acero, config_calculo, sistema=sistema)

            # Tarjetas métricas llamativas
            c_res1, c_res2 = st.columns(2)
            if sistema == "METRICO":
                c_res1.metric(
                    "Capacidad de Diseño (ϕPn)",
                    f"{res['phi_Pn_diseno_kg']:,.0f} kg",
                    f"{res['phi_Pn_diseno_kg']/1000:.2f} ton"
                )
            else:
                c_res1.metric(
                    "Capacidad de Diseño (ϕPn)",
                    f"{res['phi_Pn_diseno_kips']:.2f} kips",
                    f"{res['phi_Pn_diseno_kg']:,.0f} kg"
                )

            c_res2.metric(
                "Estado Límite Gobernante",
                res["gobernante"],
                "Rige la menor capacidad"
            )

            # Tabla comparativa interactiva
            estados = [
                {
                    "Estado Límite": "Fluencia en Sección Bruta (D2-1)",
                    "ϕ": "0.90",
                    "Capacidad Nominal": f"{res['fluencia']['Pn_kg']:,.0f} kg" if sistema == "METRICO" else f"{res['fluencia']['Pn_kips']:.2f} kips",
                    "Capacidad de Diseño": f"{res['fluencia']['phi_Pn_kg']:,.0f} kg" if sistema == "METRICO" else f"{res['fluencia']['phi_Pn_kips']:.2f} kips",
                    "Condición": "RIGE" if res["gobernante"] == "Fluencia en sección bruta" else "OK"
                },
                {
                    "Estado Límite": "Ruptura en Sección Neta (D2-2)",
                    "ϕ": "0.75",
                    "Capacidad Nominal": f"{res['ruptura']['Pn_kg']:,.0f} kg" if sistema == "METRICO" else f"{res['ruptura']['Pn_kips']:.2f} kips",
                    "Capacidad de Diseño": f"{res['ruptura']['phi_Pn_kg']:,.0f} kg" if sistema == "METRICO" else f"{res['ruptura']['phi_Pn_kips']:.2f} kips",
                    "Condición": "RIGE" if res["gobernante"] == "Ruptura en sección neta" else "OK"
                }
            ]
            if res.get("bloque_cortante"):
                bc = res["bloque_cortante"]
                estados.append({
                    "Estado Límite": "Bloque de Cortante (J4.3)",
                    "ϕ": "0.75",
                    "Capacidad Nominal": f"{bc['Rn_kg']:,.0f} kg" if sistema == "METRICO" else f"{bc['Rn_kips']:.2f} kips",
                    "Capacidad de Diseño": f"{bc['phi_Rn_kg']:,.0f} kg" if sistema == "METRICO" else f"{bc['phi_Rn_kips']:.2f} kips",
                    "Condición": "RIGE" if res["gobernante"] == "Bloque de cortante" else "OK"
                })

            st.dataframe(estados, use_container_width=True, hide_index=True)

            # Pestaña de Memoria Técnica
            with st.expander("📄 Ver Memoria de Cálculo Completa", expanded=True):
                reporte_texto = generar_memoria_texto(perfil, acero, res, sistema=sistema)
                st.code(reporte_texto, language="text")

                st.download_button(
                    label="📥 Descargar Memoria de Cálculo (.txt)",
                    data=reporte_texto,
                    file_name="memoria_calculo_tension.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"Error en el cálculo: {e}")
