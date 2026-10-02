"""
Motor de Cálculo para Elementos en Tensión (AISC 360 LRFD)
=========================================================
Implementa las revisiones de los tres estados límite:
1. Fluencia en la sección bruta (AISC D2-1)
2. Ruptura en la sección neta (AISC D2-2 y B4.3b con regla de Cochrane s²/4g)
3. Ruptura por bloque de cortante (AISC J4.3)

Soporta cálculo directo en:
- Sistema Métrico: kg/cm², cm, cm², kg, toneladas métricas.
- Sistema Inglés: ksi, in, in², kips.
"""

from unidades import (
    KIPS_A_TON, KIPS_A_KG, KG_A_KIPS, TON_A_KIPS,
    IN2_A_CM2, CM2_A_IN2, IN_A_CM, CM_A_IN, IN_A_MM, MM_A_IN,
    KSI_A_KG_CM2, KG_CM2_A_KSI,
    formatear_fuerza, formatear_esfuerzo, formatear_area, formatear_longitud
)


def calcular_fluencia(Ag, Fy, sistema="US", phi=0.90):
    """
    Calcula la fluencia en la sección bruta:
    Pn = Fy * Ag
    phi * Pn = phi * Fy * Ag
    """
    Pn = Fy * Ag
    phi_Pn = phi * Pn

    if sistema == "METRICO":
        Pn_kg = Pn
        phi_Pn_kg = phi_Pn
        Pn_kips = Pn_kg * KG_A_KIPS
        phi_Pn_kips = phi_Pn_kg * KG_A_KIPS
        Ag_cm2 = Ag
        Ag_in2 = Ag * CM2_A_IN2
        Fy_kg = Fy
        Fy_ksi = Fy * KG_CM2_A_KSI
    else:
        Pn_kips = Pn
        phi_Pn_kips = phi_Pn
        Pn_kg = Pn_kips * KIPS_A_KG
        phi_Pn_kg = phi_Pn_kips * KIPS_A_KG
        Ag_in2 = Ag
        Ag_cm2 = Ag * IN2_A_CM2
        Fy_ksi = Fy
        Fy_kg = Fy * KSI_A_KG_CM2

    return {
        "estado_limite": "Fluencia en sección bruta",
        "phi": phi,
        "Ag": Ag,
        "Ag_in2": Ag_in2,
        "Ag_cm2": Ag_cm2,
        "Fy": Fy,
        "Fy_ksi": Fy_ksi,
        "Fy_kg_cm2": Fy_kg,
        "Pn": Pn,
        "Pn_kips": Pn_kips,
        "Pn_kg": Pn_kg,
        "Pn_ton": Pn_kg / 1000.0,
        "phi_Pn": phi_Pn,
        "phi_Pn_kips": phi_Pn_kips,
        "phi_Pn_kg": phi_Pn_kg,
        "phi_Pn_ton": phi_Pn_kg / 1000.0,
    }


def calcular_area_neta_trayectoria(Ag, t, d_agujero, num_agujeros, diagonales=None):
    """
    Calcula el área neta para una trayectoria específica según AISC B4.3b:
      An = Ag - Σ(d_agujero * t) + Σ(s² / 4g) * t

    Parámetros:
      Ag: Área bruta
      t: Espesor del elemento
      d_agujero: Diámetro de la perforación (dp)
      num_agujeros: Cantidad de agujeros cortados por la línea de falla
      diagonales: Lista de tuplas [(s1, g1), (s2, g2), ...] para cada tramo diagonal.
    """
    if diagonales is None:
        diagonales = []

    descuento_barrenos = num_agujeros * d_agujero * t
    termino_zig_zag = sum((s ** 2 / (4.0 * g)) * t for s, g in diagonales if g > 0)
    
    An = Ag - descuento_barrenos + termino_zig_zag

    return {
        "num_agujeros": num_agujeros,
        "diagonales": diagonales,
        "num_diagonales": len(diagonales),
        "descuento_barrenos": descuento_barrenos,
        "termino_zig_zag": termino_zig_zag,
        "An": An,
    }


def calcular_ruptura(Ag, Fu, t, d_agujero, num_agujeros=1, U=1.0, diagonales=None, trayectorias=None, sistema="US", phi=0.75):
    """
    Calcula la ruptura en la sección neta considerando líneas de falla rectas o alternadas (tresbolillo).
    
    Fórmula AISC B4.3b:
      An = Ag - Σ(dp · t) + Σ(s² / 4g) · t
      Ae = U · An
      Pn = Fu · Ae
      phi · Pn = 0.75 · Pn

    Parámetros:
      trayectorias: Lista opcional de diccionarios, ej:
        [
          {"nombre": "T1 (ABCD)", "num_agujeros": 2, "diagonales": []},
          {"nombre": "T2 (ABEFG)", "num_agujeros": 3, "diagonales": [(4, 5), (4, 5)]},
          {"nombre": "T3 (ABECD)", "num_agujeros": 3, "diagonales": [(4, 5), (4, 5)]},
        ]
    """
    # Si no se pasó lista de trayectorias múltiples, armar una con los parámetros individuales:
    if not trayectorias:
        trayectorias = [{
            "nombre": "Trayectoria crítica",
            "num_agujeros": num_agujeros,
            "diagonales": diagonales if diagonales else [],
        }]

    # Evaluar cada trayectoria candidata:
    resultados_trayectorias = []
    for tray in trayectorias:
        nombre = tray.get("nombre", f"Trayectoria {len(resultados_trayectorias) + 1}")
        n_ag = tray.get("num_agujeros", num_agujeros)
        diags = tray.get("diagonales", [])
        
        calc_t = calcular_area_neta_trayectoria(Ag, t, d_agujero, n_ag, diags)
        calc_t["nombre"] = nombre
        resultados_trayectorias.append(calc_t)

    # La trayectoria que gobierna es la que produce la MENOR área neta:
    trayectoria_gobernante = min(resultados_trayectorias, key=lambda x: x["An"])
    An = trayectoria_gobernante["An"]

    if An <= 0:
        raise ValueError(f"El área neta calculada ({An:.2f}) es menor o igual a cero.")

    Ae = U * An
    Pn = Fu * Ae
    phi_Pn = phi * Pn

    if sistema == "METRICO":
        Pn_kg = Pn
        phi_Pn_kg = phi_Pn
        Pn_kips = Pn_kg * KG_A_KIPS
        phi_Pn_kips = phi_Pn_kg * KG_A_KIPS
        An_cm2 = An
        An_in2 = An * CM2_A_IN2
        Ae_cm2 = Ae
        Ae_in2 = Ae * CM2_A_IN2
        t_cm = t
        t_in = t * CM_A_IN
        d_agujero_cm = d_agujero
        d_agujero_in = d_agujero * CM_A_IN
    else:
        Pn_kips = Pn
        phi_Pn_kips = phi_Pn
        Pn_kg = Pn_kips * KIPS_A_KG
        phi_Pn_kg = phi_Pn_kips * KIPS_A_KG
        An_in2 = An
        An_cm2 = An * IN2_A_CM2
        Ae_in2 = Ae
        Ae_cm2 = Ae * IN2_A_CM2
        t_in = t
        t_cm = t * IN_A_CM
        d_agujero_in = d_agujero
        d_agujero_cm = d_agujero * IN_A_CM

    return {
        "estado_limite": "Ruptura en sección neta",
        "phi": phi,
        "d_agujero": d_agujero,
        "d_agujero_in": d_agujero_in,
        "d_agujero_cm": d_agujero_cm,
        "num_agujeros": trayectoria_gobernante["num_agujeros"],
        "t": t,
        "t_in": t_in,
        "t_cm": t_cm,
        "An": An,
        "An_in2": An_in2,
        "An_cm2": An_cm2,
        "U": U,
        "Ae": Ae,
        "Ae_in2": Ae_in2,
        "Ae_cm2": Ae_cm2,
        "Pn": Pn,
        "Pn_kips": Pn_kips,
        "Pn_kg": Pn_kg,
        "Pn_ton": Pn_kg / 1000.0,
        "phi_Pn": phi_Pn,
        "phi_Pn_kips": phi_Pn_kips,
        "phi_Pn_kg": phi_Pn_kg,
        "phi_Pn_ton": phi_Pn_kg / 1000.0,
        "trayectorias_evaluadas": resultados_trayectorias,
        "trayectoria_gobernante": trayectoria_gobernante,
        "es_alternada": any(len(t_item["diagonales"]) > 0 for t_item in resultados_trayectorias) or len(resultados_trayectorias) > 1,
    }


def calcular_bloque_cortante(Fy, Fu, t, d_agujero, n_long, s, Le_v, W_t, num_lineas_corte=1, Ubs=1.0, sistema="US", phi=0.75):
    """
    Calcula Bloque de Cortante según AISC J4.3:
    Rn = min(0.60*Fu*Anv + Ubs*Fu*Ant, 0.60*Fy*Agv + Ubs*Fu*Ant)
    phi * Rn = 0.75 * Rn
    """
    if n_long < 1:
        raise ValueError("Debe haber al menos 1 tornillo longitudinal.")

    L_v = Le_v + (n_long - 1) * s

    # Áreas a cortante:
    Agv = num_lineas_corte * (L_v * t)
    agujeros_corte_por_linea = (n_long - 1) + 0.5
    Anv = num_lineas_corte * (L_v - agujeros_corte_por_linea * d_agujero) * t
    Anv = max(0.0, Anv)

    # Áreas a tensión:
    Agt = W_t * t
    agujeros_tension = 0.5 * num_lineas_corte
    Ant = (W_t - agujeros_tension * d_agujero) * t
    Ant = max(0.0, Ant)

    # Ecuación AISC J4-5:
    Rn_1 = 0.60 * Fu * Anv + Ubs * Fu * Ant
    Rn_2 = 0.60 * Fy * Agv + Ubs * Fu * Ant

    Rn = min(Rn_1, Rn_2)
    phi_Rn = phi * Rn

    if sistema == "METRICO":
        Rn_kg = Rn
        phi_Rn_kg = phi_Rn
        Rn_kips = Rn_kg * KG_A_KIPS
        phi_Rn_kips = phi_Rn_kg * KG_A_KIPS
        Agv_cm2 = Agv
        Anv_cm2 = Anv
        Agt_cm2 = Agt
        Ant_cm2 = Ant
        Agv_in2 = Agv * CM2_A_IN2
        Anv_in2 = Anv * CM2_A_IN2
        Agt_in2 = Agt * CM2_A_IN2
        Ant_in2 = Ant * CM2_A_IN2
    else:
        Rn_kips = Rn
        phi_Rn_kips = phi_Rn
        Rn_kg = Rn_kips * KIPS_A_KG
        phi_Rn_kg = phi_Rn_kips * KIPS_A_KG
        Agv_in2 = Agv
        Anv_in2 = Anv
        Agt_in2 = Agt
        Ant_in2 = Ant
        Agv_cm2 = Agv * IN2_A_CM2
        Anv_cm2 = Anv * IN2_A_CM2
        Agt_cm2 = Agt * IN2_A_CM2
        Ant_cm2 = Ant * IN2_A_CM2

    return {
        "estado_limite": "Bloque de cortante",
        "phi": phi,
        "Agv": Agv,
        "Agv_in2": Agv_in2,
        "Agv_cm2": Agv_cm2,
        "Anv": Anv,
        "Anv_in2": Anv_in2,
        "Anv_cm2": Anv_cm2,
        "Agt": Agt,
        "Agt_in2": Agt_in2,
        "Agt_cm2": Agt_cm2,
        "Ant": Ant,
        "Ant_in2": Ant_in2,
        "Ant_cm2": Ant_cm2,
        "Rn": Rn,
        "Rn_kips": Rn_kips,
        "Rn_kg": Rn_kg,
        "Rn_ton": Rn_kg / 1000.0,
        "phi_Rn": phi_Rn,
        "phi_Rn_kips": phi_Rn_kips,
        "phi_Rn_kg": phi_Rn_kg,
        "phi_Rn_ton": phi_Rn_kg / 1000.0,
        "termo_fractura": Rn_1,
        "termo_fluencia": Rn_2,
        "rige_fluencia_corte": (Rn_2 < Rn_1),
        "Ubs": Ubs,
    }


def evaluar_conexion_tension(datos_perfil, datos_acero, config, sistema="US"):
    """
    Evalúa todos los estados límite y determina el caso gobernante.
    """
    if sistema == "METRICO":
        Ag = datos_perfil.get("area_cm2")
        t = datos_perfil.get("espesor_cm") or (datos_perfil.get("espesor_mm", 0) / 10.0) or (datos_perfil.get("t_mm", 0) / 10.0) or (datos_perfil.get("tw_mm", 0) / 10.0)
        Fy = datos_acero["Fy_kg_cm2"]
        Fu = datos_acero["Fu_kg_cm2"]
        d_agujero = config.get("d_agujero_cm", 2.22)
    else:
        Ag = datos_perfil.get("area_in2")
        t = datos_perfil.get("espesor_in") or datos_perfil.get("t_in") or datos_perfil.get("tw_in")
        Fy = datos_acero["Fy_ksi"]
        Fu = datos_acero["Fu_ksi"]
        d_agujero = config.get("d_agujero_in", 0.875)

    num_tornillos_sec = config.get("num_tornillos_seccion", 1)
    U = config.get("U", 1.0)
    diagonales = config.get("diagonales", None)
    trayectorias = config.get("trayectorias", None)

    # 1. Fluencia:
    res_fluencia = calcular_fluencia(Ag, Fy, sistema=sistema)

    # 2. Ruptura (con soporte para trayectorias múltiples y s²/4g):
    res_ruptura = calcular_ruptura(
        Ag=Ag,
        Fu=Fu,
        t=t,
        d_agujero=d_agujero,
        num_agujeros=num_tornillos_sec,
        U=U,
        diagonales=diagonales,
        trayectorias=trayectorias,
        sistema=sistema
    )

    # 3. Bloque de cortante (si está activado):
    res_bloque = None
    if "n_long" in config and "s" in config and "Le_v" in config and "W_t" in config:
        res_bloque = calcular_bloque_cortante(
            Fy=Fy,
            Fu=Fu,
            t=t,
            d_agujero=d_agujero,
            n_long=config["n_long"],
            s=config["s"],
            Le_v=config["Le_v"],
            W_t=config["W_t"],
            num_lineas_corte=config.get("num_lineas_corte", 1),
            Ubs=config.get("Ubs", 1.0),
            sistema=sistema
        )

    # Gobernantes:
    candidatos = [
        ("Fluencia en sección bruta", res_fluencia["phi_Pn"]),
        ("Ruptura en sección neta", res_ruptura["phi_Pn"]),
    ]
    if res_bloque:
        candidatos.append(("Bloque de cortante", res_bloque["phi_Rn"]))

    gobernante_nombre, phi_resistencia = min(candidatos, key=lambda x: x[1])

    return {
        "sistema": sistema,
        "fluencia": res_fluencia,
        "ruptura": res_ruptura,
        "bloque_cortante": res_bloque,
        "gobernante": gobernante_nombre,
        "phi_Pn_diseno": phi_resistencia,
        "phi_Pn_diseno_kips": res_fluencia["phi_Pn_kips"] if gobernante_nombre == "Fluencia en sección bruta" else (res_ruptura["phi_Pn_kips"] if gobernante_nombre == "Ruptura en sección neta" else res_bloque["phi_Rn_kips"]),
        "phi_Pn_diseno_kg": res_fluencia["phi_Pn_kg"] if gobernante_nombre == "Fluencia en sección bruta" else (res_ruptura["phi_Pn_kg"] if gobernante_nombre == "Ruptura en sección neta" else res_bloque["phi_Rn_kg"]),
    }


def generar_memoria_texto(perfil, acero, res, sistema="US"):
    """
    Genera el texto de la memoria formateado con detalle de líneas de falla.
    """
    fl = res["fluencia"]
    rup = res["ruptura"]
    bc = res.get("bloque_cortante")

    lineas = [
        "=" * 68,
        f"        MEMORIA DE CÁLCULO DE TENSIÓN - AISC 360 LRFD",
        f"               SISTEMA: {'MÉTRICO (SI)' if sistema == 'METRICO' else 'INGLÉS (US)'}",
        "=" * 68,
        f"Elemento:         {perfil.get('designacion_si' if sistema == 'METRICO' else 'designacion_us')}",
        f"Tipo de perfil:   {perfil['tipo']}",
    ]

    unid_area = "cm²" if sistema == "METRICO" else "in²"
    unid_long = "cm" if sistema == "METRICO" else "in"

    if sistema == "METRICO":
        lineas.extend([
            f"Área Bruta:       Ag = {fl['Ag_cm2']:.2f} cm²  [ {fl['Ag_in2']:.3f} in² ]",
            f"Espesor crítico:  t  = {rup['t_cm']:.2f} cm ({rup['t_cm']*10:.1f} mm)  [ {rup['t_in']:.3f}\" ]",
            f"Material:         Acero {acero['nombre']} (Fy = {acero['Fy_kg_cm2']:,.0f} kg/cm², Fu = {acero['Fu_kg_cm2']:,.0f} kg/cm²)",
            "-" * 68,
            "1. FLUENCIA EN LA SECCIÓN BRUTA (AISC D2-1)",
            "   Fórmula:       phi * Pn = 0.90 * Fy * Ag",
            f"   Nominal (Pn):  {fl['Pn_kg']:,.0f} kg ({fl['Pn_ton']:.2f} ton)  [ {fl['Pn_kips']:.2f} kips ]",
            f"   Diseño (phi*Pn): {fl['phi_Pn_kg']:,.0f} kg ({fl['phi_Pn_ton']:.2f} ton)  [ {fl['phi_Pn_kips']:.2f} kips ]",
            "-" * 68,
            "2. RUPTURA EN LA SECCIÓN NETA (AISC D2-2 Y B4.3b)",
            f"   Fórmula:       An = Ag - Sum(dp * t) + Sum(s^2 / 4g) * t",
            f"   Agujero (dp):  {rup['d_agujero_cm']:.2f} cm ({rup['d_agujero_cm']*10:.1f} mm)  [ {rup['d_agujero_in']:.3f}\" ]",
        ])
    else:
        lineas.extend([
            f"Área Bruta:       Ag = {fl['Ag_in2']:.3f} in²  [ {fl['Ag_cm2']:.2f} cm² ]",
            f"Espesor crítico:  t  = {rup['t_in']:.3f}\"  [ {rup['t_cm']*10:.1f} mm ]",
            f"Material:         Acero {acero['nombre']} (Fy = {acero['Fy_ksi']:.0f} ksi, Fu = {acero['Fu_ksi']:.0f} ksi)",
            "-" * 68,
            "1. FLUENCIA EN LA SECCIÓN BRUTA (AISC D2-1)",
            "   Fórmula:       phi * Pn = 0.90 * Fy * Ag",
            f"   Nominal (Pn):  {fl['Pn_kips']:.2f} kips  [ {fl['Pn_kg']:,.0f} kg / {fl['Pn_ton']:.2f} ton ]",
            f"   Diseño (phi*Pn): {fl['phi_Pn_kips']:.2f} kips  [ {fl['phi_Pn_kg']:,.0f} kg / {fl['phi_Pn_ton']:.2f} ton ]",
            "-" * 68,
            "2. RUPTURA EN LA SECCIÓN NETA (AISC D2-2 Y B4.3b)",
            f"   Fórmula:       An = Ag - Sum(dp * t) + Sum(s^2 / 4g) * t",
            f"   Agujero (dp):  {rup['d_agujero_in']:.3f}\"  [ {rup['d_agujero_cm']*10:.1f} mm ]",
        ])

    # Si se evaluaron trayectorias múltiples o alternadas:
    trays = rup.get("trayectorias_evaluadas", [])
    if len(trays) > 1 or rup.get("es_alternada"):
        lineas.append("\n   Análisis de Líneas de Falla (Trayectorias):")
        for tr in trays:
            es_gov = (tr["nombre"] == rup["trayectoria_gobernante"]["nombre"])
            gov_tag = "  <<< RIGE" if es_gov else ""
            desc_diags = f"{tr['num_diagonales']} diag." if tr["num_diagonales"] > 0 else "0 diag."
            if tr["num_diagonales"] > 0:
                s_g_str = ", ".join(f"s={s:.3g}{unid_long}, g={g:.3g}{unid_long}" for s, g in tr["diagonales"])
                desc_diags += f" ({s_g_str})"
            lineas.append(f"   * {tr['nombre']:<16}: {tr['num_agujeros']} barrenos, {desc_diags} -> An = {tr['An']:.3f} {unid_area}{gov_tag}")
        lineas.append(f"   Trayectoria crítica: {rup['trayectoria_gobernante']['nombre']}")
    else:
        lineas.append(f"   No. barrenos:  {rup['num_agujeros']} en sección transversal de falla")

    if sistema == "METRICO":
        lineas.extend([
            f"   Área Neta:     An = {rup['An_cm2']:.2f} cm²  [ {rup['An_in2']:.3f} in² ]",
            f"   Factor U:      U  = {rup['U']:.3f}  ->  Área Efectiva Ae = {rup['Ae_cm2']:.2f} cm²",
            f"   Nominal (Pn):  {rup['Pn_kg']:,.0f} kg ({rup['Pn_ton']:.2f} ton)  [ {rup['Pn_kips']:.2f} kips ]",
            f"   Diseño (phi*Pn): {rup['phi_Pn_kg']:,.0f} kg ({rup['phi_Pn_ton']:.2f} ton)  [ {rup['phi_Pn_kips']:.2f} kips ]",
            "-" * 68,
        ])
    else:
        lineas.extend([
            f"   Área Neta:     An = {rup['An_in2']:.3f} in²  [ {rup['An_cm2']:.2f} cm² ]",
            f"   Factor U:      U  = {rup['U']:.3f}  ->  Área Efectiva Ae = {rup['Ae_in2']:.3f} in²",
            f"   Nominal (Pn):  {rup['Pn_kips']:.2f} kips  [ {rup['Pn_kg']:,.0f} kg ]",
            f"   Diseño (phi*Pn): {rup['phi_Pn_kips']:.2f} kips  [ {rup['phi_Pn_kg']:,.0f} kg ]",
            "-" * 68,
        ])

    if bc:
        if sistema == "METRICO":
            lineas.extend([
                "3. BLOQUE DE CORTANTE (AISC J4.3)",
                f"   Áreas cortante: Agv = {bc['Agv_cm2']:.2f} cm², Anv = {bc['Anv_cm2']:.3f} cm²",
                f"   Áreas tensión:  Agt = {bc['Agt_cm2']:.2f} cm², Ant = {bc['Ant_cm2']:.3f} cm²",
                f"   Término 1 (Fractura en corte): 0.60*Fu*Anv + Ubs*Fu*Ant = {bc['termo_fractura']:,.0f} kg",
                f"   Término 2 (Fluencia en corte): 0.60*Fy*Agv + Ubs*Fu*Ant = {bc['termo_fluencia']:,.0f} kg",
                f"   Capacidad Nom:  Rn = {bc['Rn_kg']:,.0f} kg ({'Rige fluencia en corte' if bc['rige_fluencia_corte'] else 'Rige fractura en corte'})",
                f"   Diseño (phi*Rn): {bc['phi_Rn_kg']:,.0f} kg ({bc['phi_Rn_ton']:.2f} ton)  [ {bc['phi_Rn_kips']:.2f} kips ]",
                "-" * 68,
            ])
        else:
            lineas.extend([
                "3. BLOQUE DE CORTANTE (AISC J4.3)",
                f"   Áreas cortante: Agv = {bc['Agv_in2']:.3f} in², Anv = {bc['Anv_in2']:.3f} in²",
                f"   Áreas tensión:  Agt = {bc['Agt_in2']:.3f} in², Ant = {bc['Ant_in2']:.3f} in²",
                f"   Término 1 (Fractura en corte): {bc['termo_fractura']:.2f} kips",
                f"   Término 2 (Fluencia en corte): {bc['termo_fluencia']:.2f} kips",
                f"   Capacidad Nom:  Rn = {bc['Rn_kips']:.2f} kips ({'Rige fluencia en corte' if bc['rige_fluencia_corte'] else 'Rige fractura en corte'})",
                f"   Diseño (phi*Rn): {bc['phi_Rn_kips']:.2f} kips  [ {bc['phi_Rn_kg']:,.0f} kg ]",
                "-" * 68,
            ])

    if sistema == "METRICO":
        diseno_str = f"{res['phi_Pn_diseno_kg']:,.0f} kg ({res['phi_Pn_diseno_kg']/1000.0:.2f} ton)  [ {res['phi_Pn_diseno_kips']:.2f} kips ]"
    else:
        diseno_str = f"{res['phi_Pn_diseno_kips']:.2f} kips  [ {res['phi_Pn_diseno_kg']:,.0f} kg ]"

    lineas.extend([
        f">>> ESTADO LÍMITE GOBERNANTE: {res['gobernante'].upper()} <<<",
        f">>> CAPACIDAD RESISTENTE DE DISEÑO: {diseno_str} <<<",
        "=" * 68,
    ])

    return "\n".join(lineas)
