"""
Módulo de Conversión y Formato de Unidades
==========================================
Soporta Sistema Inglés (US) y Sistema Métrico (SI) para diseño en acero:
- Esfuerzos: ksi <-> kg/cm² <-> MPa
- Fuerzas y Resistencias: kips <-> toneladas métricas (ton) <-> kg <-> kN
- Dimensiones lineales: in (pulgadas) <-> cm <-> mm
- Áreas: in² <-> cm² <-> mm²
"""

# Factores de conversión exactos o normativos:
# 1 pulgada = 2.54 cm = 25.4 mm
IN_A_CM = 2.54
CM_A_IN = 1.0 / 2.54
IN_A_MM = 25.4
MM_A_IN = 1.0 / 25.4

# Áreas:
IN2_A_CM2 = 6.4516
CM2_A_IN2 = 1.0 / 6.4516

# Fuerzas:
# 1 kip = 1,000 lb = 453.59237 kg = 0.45359237 ton métrica = 4.44822 kN
KIPS_A_KG = 453.59237
KG_A_KIPS = 1.0 / 453.59237
KIPS_A_TON = 0.45359237
TON_A_KIPS = 1.0 / 0.45359237
KIPS_A_KN = 4.4482216
KN_A_KIPS = 1.0 / 4.4482216

# Esfuerzos:
# 1 ksi = 70.30696 kg/cm² = 6.894757 MPa
KSI_A_KG_CM2 = 70.30696
KG_CM2_A_KSI = 1.0 / 70.30696
KSI_A_MPA = 6.894757
MPA_A_KSI = 1.0 / 6.894757


def kips_a_ton(kips):
    return kips * KIPS_A_TON


def kips_a_kg(kips):
    return kips * KIPS_A_KG


def ton_a_kips(ton):
    return ton * TON_A_KIPS


def kg_a_kips(kg):
    return kg * KG_A_KIPS


def ksi_a_kg_cm2(ksi):
    return ksi * KSI_A_KG_CM2


def kg_cm2_a_ksi(kg_cm2):
    return kg_cm2 * KG_CM2_A_KSI


def in_a_mm(pulgadas):
    return pulgadas * IN_A_MM


def in_a_cm(pulgadas):
    return pulgadas * IN_A_CM


def mm_a_in(mm):
    return mm * MM_A_IN


def cm_a_in(cm):
    return cm * CM_A_IN


def in2_a_cm2(in2):
    return in2 * IN2_A_CM2


def cm2_a_in2(cm2):
    return cm2 * CM2_A_IN2


def formatear_fuerza(kips, sistema="US"):
    """
    Formatea un valor de fuerza / resistencia en el sistema deseado con el otro entre paréntesis.
    """
    ton = kips * KIPS_A_TON
    kg = kips * KIPS_A_KG
    if sistema == "METRICO":
        return f"{ton:.2f} ton ({kg:,.1f} kg)  [ {kips:.2f} kips ]"
    else:
        return f"{kips:.2f} kips  [ {ton:.2f} ton / {kg:,.0f} kg ]"


def formatear_esfuerzo(ksi, sistema="US"):
    """Formatea un esfuerzo (Fy, Fu) en ksi y kg/cm²."""
    kg_cm2 = ksi * KSI_A_KG_CM2
    mpa = ksi * KSI_A_MPA
    if sistema == "METRICO":
        return f"{kg_cm2:,.1f} kg/cm² ({mpa:.1f} MPa)  [ {ksi:.1f} ksi ]"
    else:
        return f"{ksi:.1f} ksi  [ {kg_cm2:,.1f} kg/cm² ]"


def formatear_area(in2, sistema="US"):
    """Formatea un área en in² y cm²."""
    cm2 = in2 * IN2_A_CM2
    if sistema == "METRICO":
        return f"{cm2:.2f} cm²  [ {in2:.3f} in² ]"
    else:
        return f"{in2:.3f} in²  [ {cm2:.2f} cm² ]"


def formatear_longitud(pulgadas, sistema="US", unidad_metrica="mm"):
    """Formatea dimensiones lineales."""
    if unidad_metrica == "mm":
        metrico_val = pulgadas * IN_A_MM
        txt_met = f"{metrico_val:.2f} mm"
    else:
        metrico_val = pulgadas * IN_A_CM
        txt_met = f"{metrico_val:.2f} cm"

    if sistema == "METRICO":
        return f"{txt_met}  [ {pulgadas:.3f}\" ]"
    else:
        return f"{pulgadas:.3f}\"  [ {txt_met} ]"
