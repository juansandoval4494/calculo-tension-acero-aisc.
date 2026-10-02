"""
Módulo de Lectura del Catálogo IMCA (Manual de Construcción en Acero)
=====================================================================
Extrae las propiedades geométricas de los perfiles de acero del archivo
Excel del IMCA tanto en Sistema Métrico (SI) como en Sistema Inglés (US).

Tipos de perfiles incluidos:
1. PERFIL LI: Ángulos de lados iguales (L)
2. PERFIL IR: Perfiles I de patín ancho (W / IPR / IR)
3. PERFIL CE: Canales estándar (C)
4. SOLERAS: Placas y pletinas comerciales (y soporte para placa a la medida)
"""

import os
import re
import pandas as pd
from unidades import IN2_A_CM2, IN_A_MM, IN_A_CM


def _limpiar_numero(val):
    """
    Convierte cualquier valor de celda a float, corrigiendo posibles
    errores tipográficos comunes en Excel (comas, dobles puntos '..', etc.).
    """
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace('..', '.').replace(',', '.')
    s = re.sub(r'[^0-9.-]', '', s)
    try:
        return float(s)
    except ValueError:
        return None


class CatalogoIMCA:
    """Clase principal para cargar y consultar perfiles del catálogo IMCA."""

    def __init__(self, ruta_excel=None):
        if ruta_excel is None:
            directorio_actual = os.path.dirname(os.path.abspath(__file__))
            self.ruta_excel = os.path.join(directorio_actual, "IMCA_MANUAL_CONSTRUCCION_EN_ACERO.xls")
        else:
            self.ruta_excel = ruta_excel

        self.perfiles_li = []
        self.perfiles_ir = []
        self.perfiles_ce = []
        self.soleras = []
        self._cargado = False

    def cargar(self):
        """Lee el archivo Excel y organiza los perfiles en memoria."""
        if not os.path.exists(self.ruta_excel):
            raise FileNotFoundError(f"No se encontró el archivo del IMCA en: {self.ruta_excel}")

        self._cargar_li()
        self._cargar_ir()
        self._cargar_ce()
        self._cargar_soleras()
        self._cargado = True

    def _cargar_li(self):
        """Carga ángulos de lados iguales (PERFIL LI / L)."""
        df = pd.read_excel(self.ruta_excel, sheet_name="PERFIL LI", header=None)
        for r in range(23, df.shape[0]):
            val_si = str(df.iloc[r, 1]).strip()
            if not val_si or val_si == "nan" or not val_si.upper().startswith("LI"):
                continue

            area_cm2 = _limpiar_numero(df.iloc[r, 12])
            if area_cm2 is None:
                continue

            # Parsear dimensiones desde 'LI 76 x 6'
            partes = val_si.upper().replace("LI", "").strip().split("X")
            try:
                d_mm = float(partes[0].strip())
                t_mm = float(partes[1].strip())
            except (ValueError, IndexError):
                continue

            desig_us_raw = str(df.iloc[r, 2]).strip()
            # En pulgadas suele llamarse L 3 x 3 x 1/4 o 3 x 1/4"
            desig_us = f"L {desig_us_raw}\""
            etiqueta_us = f"{desig_us:<14} ( {val_si} )"
            etiqueta_si = f"{val_si:<14} ( {desig_us} )"

            peso = _limpiar_numero(df.iloc[r, 3])
            gramil = _limpiar_numero(df.iloc[r, 6])
            x_bar_cm = _limpiar_numero(df.iloc[r, 16])

            d_in = d_mm / 25.4
            t_in = t_mm / 25.4
            try:
                partes_us = desig_us_raw.lower().split("x")
                d_in = float(partes_us[0].strip())
                frac = partes_us[-1].strip()
                if "/" in frac:
                    n_f, d_f = frac.split("/")
                    t_in = float(n_f) / float(d_f)
                else:
                    t_in = float(frac)
            except Exception:
                pass

            area_in2 = round(area_cm2 / IN2_A_CM2, 2)

            perfil = {
                "tipo": "LI",
                "designacion": val_si,
                "designacion_si": val_si,
                "designacion_us": desig_us,
                "designacion_us_raw": desig_us_raw,
                "etiqueta_us": etiqueta_us,
                "etiqueta_si": etiqueta_si,
                "d_mm": d_mm,
                "t_mm": t_mm,
                "d_in": d_in,
                "t_in": t_in,
                "area_cm2": area_cm2,
                "area_in2": area_in2,
                "peso_kg_m": peso,
                "gramil_mm": gramil,
                "gramil_in": (gramil / 25.4) if gramil else None,
                "x_bar_cm": x_bar_cm,
                "x_bar_in": (x_bar_cm / 2.54) if x_bar_cm is not None else None,
            }
            self.perfiles_li.append(perfil)

    def _cargar_ir(self):
        """Carga perfiles IR (W / IPR / Viga de patín ancho)."""
        df = pd.read_excel(self.ruta_excel, sheet_name="PERFIL IR", header=None)
        for r in range(25, df.shape[0]):
            val_si = str(df.iloc[r, 1]).strip()
            if not val_si or val_si == "nan" or not val_si.upper().startswith("IR"):
                continue

            area_cm2 = _limpiar_numero(df.iloc[r, 15])
            if area_cm2 is None:
                continue

            desig_us_raw = str(df.iloc[r, 2]).strip()
            # Convertir 'IR 8 x 18' a 'W 8 x 18' para estándar AISC
            desig_us = desig_us_raw.replace("IR ", "W ") if desig_us_raw.startswith("IR ") else desig_us_raw

            etiqueta_us = f"{desig_us:<15} ( {val_si} )"
            etiqueta_si = f"{val_si:<15} ( {desig_us} )"

            peso = _limpiar_numero(df.iloc[r, 3])
            d_mm = _limpiar_numero(df.iloc[r, 4])
            tw_mm = _limpiar_numero(df.iloc[r, 5])
            bf_mm = _limpiar_numero(df.iloc[r, 6])
            tf_mm = _limpiar_numero(df.iloc[r, 7])
            gramil = _limpiar_numero(df.iloc[r, 11])

            perfil = {
                "tipo": "IR",
                "designacion": val_si,
                "designacion_si": val_si,
                "designacion_us": desig_us,
                "designacion_us_raw": desig_us_raw,
                "etiqueta_us": etiqueta_us,
                "etiqueta_si": etiqueta_si,
                "d_mm": d_mm,
                "d_in": (d_mm / 25.4) if d_mm else None,
                "tw_mm": tw_mm,
                "tw_in": (tw_mm / 25.4) if tw_mm else None,
                "bf_mm": bf_mm,
                "bf_in": (bf_mm / 25.4) if bf_mm else None,
                "tf_mm": tf_mm,
                "tf_in": (tf_mm / 25.4) if tf_mm else None,
                "area_cm2": area_cm2,
                "area_in2": area_cm2 / IN2_A_CM2,
                "peso_kg_m": peso,
                "gramil_mm": gramil,
            }
            self.perfiles_ir.append(perfil)

    def _cargar_ce(self):
        """Carga canales estándar (PERFIL CE / C)."""
        df = pd.read_excel(self.ruta_excel, sheet_name="PERFIL CE", header=None)
        for r in range(18, df.shape[0]):
            val_si = str(df.iloc[r, 1]).strip()
            if not val_si or val_si == "nan" or not val_si.upper().startswith("CE"):
                continue

            area_cm2 = _limpiar_numero(df.iloc[r, 15])
            if area_cm2 is None:
                continue

            desig_us_raw = str(df.iloc[r, 2]).strip()
            # Convertir 'CE 3 x 4.10' a 'C 3 x 4.10'
            desig_us = desig_us_raw.replace("CE ", "C ") if desig_us_raw.startswith("CE ") else desig_us_raw

            etiqueta_us = f"{desig_us:<15} ( {val_si} )"
            etiqueta_si = f"{val_si:<15} ( {desig_us} )"

            peso = _limpiar_numero(df.iloc[r, 3])
            d_cm = _limpiar_numero(df.iloc[r, 4])
            d_mm = (d_cm * 10.0) if d_cm else None
            tw_mm = _limpiar_numero(df.iloc[r, 5])
            bf_mm = _limpiar_numero(df.iloc[r, 6])
            tf_mm = _limpiar_numero(df.iloc[r, 7])
            gramil = _limpiar_numero(df.iloc[r, 10])
            x_bar_mm = _limpiar_numero(df.iloc[r, 16])

            perfil = {
                "tipo": "CE",
                "designacion": val_si,
                "designacion_si": val_si,
                "designacion_us": desig_us,
                "designacion_us_raw": desig_us_raw,
                "etiqueta_us": etiqueta_us,
                "etiqueta_si": etiqueta_si,
                "d_mm": d_mm,
                "d_in": (d_mm / 25.4) if d_mm else None,
                "tw_mm": tw_mm,
                "tw_in": (tw_mm / 25.4) if tw_mm else None,
                "bf_mm": bf_mm,
                "bf_in": (bf_mm / 25.4) if bf_mm else None,
                "tf_mm": tf_mm,
                "tf_in": (tf_mm / 25.4) if tf_mm else None,
                "area_cm2": area_cm2,
                "area_in2": area_cm2 / IN2_A_CM2,
                "peso_kg_m": peso,
                "gramil_mm": gramil,
                "x_bar_cm": (x_bar_mm / 10.0) if x_bar_mm else None,
                "x_bar_in": (x_bar_mm / 25.4) if x_bar_mm else None,
            }
            self.perfiles_ce.append(perfil)

    def _cargar_soleras(self):
        """Carga soleras tabuladas de la hoja SOLERAS."""
        df = pd.read_excel(self.ruta_excel, sheet_name="SOLERAS", header=None)
        for r in range(16, df.shape[0]):
            w_in = _limpiar_numero(df.iloc[r, 4])
            t_in = _limpiar_numero(df.iloc[r, 5])
            if w_in is None or t_in is None:
                continue

            w_mm = _limpiar_numero(df.iloc[r, 2]) or (w_in * 25.4)
            t_mm = _limpiar_numero(df.iloc[r, 3]) or (t_in * 25.4)
            peso = _limpiar_numero(df.iloc[r, 6])

            desig_us = f"Solera {t_in:.3g}\" x {w_in:.3g}\""
            desig_si = f"Solera {t_mm:.1f} x {w_mm:.1f} mm"
            etiqueta_us = f"{desig_us:<20} ( {desig_si} )"
            etiqueta_si = f"{desig_si:<24} ( {desig_us} )"

            solera = {
                "tipo": "PLACA",
                "designacion": desig_us,
                "designacion_us": desig_us,
                "designacion_si": desig_si,
                "etiqueta_us": etiqueta_us,
                "etiqueta_si": etiqueta_si,
                "ancho_in": w_in,
                "espesor_in": t_in,
                "ancho_mm": w_mm,
                "espesor_mm": t_mm,
                "area_in2": w_in * t_in,
                "area_cm2": (w_in * t_in) * IN2_A_CM2,
                "peso_kg_m": peso,
            }
            self.soleras.append(solera)

    def obtener_lista_perfiles(self, tipo):
        """Devuelve la lista completa de diccionarios de perfil para un tipo dado."""
        tipo = tipo.upper()
        if tipo == "LI":
            return self.perfiles_li
        elif tipo == "IR":
            return self.perfiles_ir
        elif tipo == "CE":
            return self.perfiles_ce
        elif tipo in ("SOLERA", "SOLERAS", "PLACA"):
            return self.soleras
        return []

    def obtener_lista_etiquetas(self, tipo, sistema="US"):
        """
        Devuelve la lista de etiquetas para poblar menús desplegables.
        Si sistema == 'US', la designación en pulgadas va al frente.
        Si sistema == 'METRICO', la designación métrica va al frente.
        """
        perfiles = self.obtener_lista_perfiles(tipo)
        if sistema == "METRICO":
            return [p["etiqueta_si"] for p in perfiles]
        else:
            return [p["etiqueta_us"] for p in perfiles]

    def buscar_perfil(self, tipo, consulta):
        """
        Busca un perfil de forma flexible. Puede coincidir con:
        - Designación métrica (ej. 'LI 76 x 6', 'IR 203 x 26.6')
        - Designación en pulgadas (ej. '3 x 1/4', 'L 3 x 1/4', 'W 8 x 18', 'IR 8 x 18')
        - Etiqueta completa del menú desplegable.
        """
        if not consulta:
            return None

        perfiles = self.obtener_lista_perfiles(tipo)
        q_limpio = consulta.lower().replace(" ", "").replace("-", "").replace("\"", "").replace("'", "")

        # 1. Coincidencia exacta de etiqueta o nombres
        for p in perfiles:
            for campo in ["designacion_si", "designacion_us", "designacion_us_raw", "etiqueta_us", "etiqueta_si"]:
                val = str(p.get(campo, "")).lower().replace(" ", "").replace("-", "").replace("\"", "").replace("'", "")
                if val == q_limpio:
                    return p

        # 2. Coincidencia de subcadena
        for p in perfiles:
            for campo in ["designacion_si", "designacion_us", "etiqueta_us", "etiqueta_si"]:
                val = str(p.get(campo, "")).lower().replace(" ", "").replace("-", "").replace("\"", "").replace("'", "")
                if q_limpio in val or val in q_limpio:
                    return p

        return None

    @staticmethod
    def crear_placa_personalizada(ancho_in=None, espesor_in=None, ancho_cm=None, espesor_mm=None):
        """
        Crea una placa con dimensiones personalizadas.
        Se puede especificar en pulgadas (US) o en cm/mm (Métrico).
        """
        if ancho_in is not None and espesor_in is not None:
            w_in = float(ancho_in)
            t_in = float(espesor_in)
            w_mm = w_in * 25.4
            t_mm = t_in * 25.4
        elif ancho_cm is not None and espesor_mm is not None:
            w_mm = float(ancho_cm) * 10.0
            t_mm = float(espesor_mm)
            w_in = w_mm / 25.4
            t_in = t_mm / 25.4
        else:
            raise ValueError("Debes proporcionar las dimensiones en pulgadas o en cm/mm.")

        desig_us = f"Placa {t_in:.3g}\" x {w_in:.3g}\""
        desig_si = f"Placa {t_mm:.1f} mm x {w_mm / 10.0:.1f} cm"

        return {
            "tipo": "PLACA",
            "designacion": desig_us,
            "designacion_us": desig_us,
            "designacion_si": desig_si,
            "etiqueta_us": f"{desig_us}  [ {desig_si} ]",
            "etiqueta_si": f"{desig_si}  [ {desig_us} ]",
            "ancho_in": w_in,
            "espesor_in": t_in,
            "ancho_mm": w_mm,
            "espesor_mm": t_mm,
            "area_in2": w_in * t_in,
            "area_cm2": (w_in * t_in) * IN2_A_CM2,
            "peso_kg_m": (w_in * t_in) * 5.066,
        }
