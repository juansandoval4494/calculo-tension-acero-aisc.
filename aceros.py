"""
Módulo de Materiales de Acero Estructural
=========================================
Propiedades mecánicas estándar según el Manual IMCA y norma AISC 360:
- A36:     Fy = 2,530 kg/cm² (36 ksi),  Fu = 4,080 kg/cm² (58 ksi)
- A529-50: Fy = 3,515 kg/cm² (50 ksi),  Fu = 4,920 kg/cm² (70 ksi)
- A992:    Fy = 3,515 kg/cm² (50 ksi),  Fu = 4,570 kg/cm² (65 ksi)
"""

TABLA_ACEROS = {
    "A36": {
        "Fy_ksi": 36.0,
        "Fu_ksi": 58.0,
        "Fy_kg_cm2": 2530.0,
        "Fu_kg_cm2": 4080.0,
        "Fy_mpa": 250.0,
        "Fu_mpa": 400.0,
        "descripcion": "Acero al carbono estándar (placas, ángulos, canales)",
    },
    "A529-50": {
        "Fy_ksi": 50.0,
        "Fu_ksi": 70.0,
        "Fy_kg_cm2": 3515.0,
        "Fu_kg_cm2": 4920.0,
        "Fy_mpa": 345.0,
        "Fu_mpa": 485.0,
        "descripcion": "Acero de alta resistencia para perfiles y placas",
    },
    "A992": {
        "Fy_ksi": 50.0,
        "Fu_ksi": 65.0,
        "Fy_kg_cm2": 3515.0,
        "Fu_kg_cm2": 4570.0,
        "Fy_mpa": 345.0,
        "Fu_mpa": 450.0,
        "descripcion": "Acero estándar para perfiles estructurales tipo W / IR",
    },
}


def obtener_acero(nombre):
    """
    Obtiene las propiedades de un acero por nombre.
    """
    nombre_limpio = nombre.strip().upper()
    for k in TABLA_ACEROS.keys():
        if k in nombre_limpio or nombre_limpio in k:
            datos = TABLA_ACEROS[k]
            return {
                "nombre": k,
                "Fy_ksi": datos["Fy_ksi"],
                "Fu_ksi": datos["Fu_ksi"],
                "Fy_kg_cm2": datos["Fy_kg_cm2"],
                "Fu_kg_cm2": datos["Fu_kg_cm2"],
                "Fy_mpa": datos["Fy_mpa"],
                "Fu_mpa": datos["Fu_mpa"],
                "descripcion": datos["descripcion"],
            }
    
    nombres_disponibles = ", ".join(TABLA_ACEROS.keys())
    raise ValueError(f"Acero '{nombre}' no reconocido. Disponibles: {nombres_disponibles}")


def registrar_acero_personalizado(nombre, fy, fu, unidad="METRICO", descripcion="Acero personalizado"):
    """Permite registrar cualquier acero definiendo Fy y Fu directamente."""
    nombre_limpio = nombre.strip().upper()
    if unidad.upper() in ("METRICO", "KG/CM2"):
        fy_kg = float(fy)
        fu_kg = float(fu)
        fy_ksi = fy_kg / 70.30696
        fu_ksi = fu_kg / 70.30696
    else:
        fy_ksi = float(fy)
        fu_ksi = float(fu)
        fy_kg = fy_ksi * 70.30696
        fu_kg = fu_ksi * 70.30696

    TABLA_ACEROS[nombre_limpio] = {
        "Fy_ksi": fy_ksi,
        "Fu_ksi": fu_ksi,
        "Fy_kg_cm2": fy_kg,
        "Fu_kg_cm2": fu_kg,
        "Fy_mpa": fy_ksi * 6.89476,
        "Fu_mpa": fu_ksi * 6.89476,
        "descripcion": descripcion,
    }
    return obtener_acero(nombre_limpio)


def listar_etiquetas_aceros(sistema="US"):
    """Devuelve las opciones para listas desplegables."""
    lista = []
    for nom in TABLA_ACEROS.keys():
        info = TABLA_ACEROS[nom]
        if sistema == "METRICO":
            etiqueta = f"{nom:<8} | Fy={info['Fy_kg_cm2']:,.0f} kg/cm², Fu={info['Fu_kg_cm2']:,.0f} kg/cm²"
        else:
            etiqueta = f"{nom:<8} | Fy={info['Fy_ksi']:.0f} ksi, Fu={info['Fu_ksi']:.0f} ksi"
        lista.append(etiqueta)
    return lista
