# Aplicación de Diseño de Elementos de Acero en Tensión (AISC LRFD)
### Catálogo Oficial Manual IMCA (5.ª Edición) — Soporte Dual Sistema Inglés y Métrico

Esta aplicación en Python realiza la revisión estructural completa de miembros de acero sometidos a tensión según la especificación **AISC 360 (LRFD)**.

---

## 🌐 Soporte Dual de Sistemas de Unidades

La aplicación puede alternar dinámicamente entre dos sistemas:

| Parámetro | 🇺🇸 Sistema Inglés (US) | 🇲🇽 / 🌐 Sistema Métrico (SI) |
| :--- | :--- | :--- |
| **Esfuerzos ($F_y, F_u$)** | $\text{ksi}$ ($\text{kips/in}^2$) | $\text{kg/cm}^2$ (con referencia en $\text{MPa}$) |
| **Resistencias ($P_n, \phi P_n, R_n$)** | $\text{kips}$ | $\text{toneladas métricas}$ y $\text{kg}$ |
| **Dimensiones de sección y tornillos** | $\text{pulgadas}$ ($\text{in}$) | $\text{cm}$ y $\text{mm}$ |
| **Áreas ($A_g, A_n, A_e, A_{gv}, A_{nv}$)** | $\text{in}^2$ | $\text{cm}^2$ |

> [!NOTE]
> Cada memoria de cálculo muestra el valor principal en el sistema seleccionado y el valor equivalente del otro sistema entre corchetes, para facilitar la comparación con literatura técnica nacional e internacional.

---

## 📐 Estados Límite Evaluados (AISC 360 LRFD)

1. **Fluencia en la sección bruta (AISC D2-1):**
   $$\phi P_n = 0.90 \cdot F_y \cdot A_g$$

2. **Ruptura / Fractura en la sección neta (AISC D2-2 y B4.3b):**
   $$\phi P_n = 0.75 \cdot F_u \cdot A_e$$
   - Barreno de cálculo: $d_p = d_{tornillo} + \frac{1}{8}''$ (AISC B4.3b).
   - **Líneas de falla con perforaciones alternadas (tresbolillo):**
     $$A_n = A_g - \sum (d_p \cdot t) + \sum \left( \frac{s^2}{4g} \right) \cdot t$$
     donde:
     - $s$ = paso longitudinal entre perforaciones adyacentes.
     - $g$ = gramil o separación transversal entre líneas de gramil.
     - El programa evalúa múltiples trayectorias ($T_1, T_2, T_3, \dots$) y selecciona automáticamente la **trayectoria crítica que produce el menor $A_n$**.
   - Área neta efectiva: $A_e = U \cdot A_n$.

3. **Ruptura por bloque de cortante (AISC J4.3):**
   $$R_n = 0.60 F_u A_{nv} + U_{bs} F_u A_{nt} \le 0.60 F_y A_{gv} + U_{bs} F_u A_{nt}$$
   $$\phi R_n = 0.75 \cdot R_n$$

---

## 🏷️ Selección de Perfiles en Pulgadas y Métrico

Los perfiles se muestran con su designación comercial en pulgadas y su equivalente del IMCA en milímetros:
* **Ángulos (LI / L):** `L 3 x 1/4"  ( LI 76 x 6 )`
* **Vigas I (IR / W):** `W 8 x 18  ( IR 203 x 26.6 )`
* **Canales (CE / C):** `C 3 x 4.10  ( CE-76 X 6.10 )`
* **Soleras y Placas:** Selección directa en pulgadas (`Solera 3/8" x 8"`) o placa a la medida.

---

## 📂 Archivos del Proyecto

* **[unidades.py](file:///C:/Users/USER/.gemini/antigravity/scratch/calculo_tension_acero/unidades.py)**: Factores de conversión exactos y formateadores bilingües.
* **[lector_imca.py](file:///C:/Users/USER/.gemini/antigravity/scratch/calculo_tension_acero/lector_imca.py)**: Carga las hojas del Excel `IMCA_MANUAL_CONSTRUCCION_EN_ACERO.xls` y organiza las propiedades en ambos sistemas.
* **[aceros.py](file:///C:/Users/USER/.gemini/antigravity/scratch/calculo_tension_acero/aceros.py)**: Materiales con $F_y$ y $F_u$ (A36, A529-50, A992 o personalizado).
* **[motor_calculo.py](file:///C:/Users/USER/.gemini/antigravity/scratch/calculo_tension_acero/motor_calculo.py)**: Núcleo analítico que revisa fluencia, ruptura y bloque de cortante, indicando el estado gobernante.
* **[interfaz_grafica.py](file:///C:/Users/USER/.gemini/antigravity/scratch/calculo_tension_acero/interfaz_grafica.py)**: Aplicación con ventana gráfica de escritorio (Tkinter).
* **[main.py](file:///C:/Users/USER/.gemini/antigravity/scratch/calculo_tension_acero/main.py)**: Aplicación interactiva para consola / terminal.

---

## 🚀 Ejecución en VS Code

Abre la terminal en VS Code (`Ctrl + ñ`):

### 1. Interfaz Gráfica (Recomendada)
```bash
python interfaz_grafica.py
```
* Selecciona con un clic entre **Sistema Inglés** o **Sistema Métrico**.
* Al cambiar el sistema, los campos y las listas de perfiles se actualizan automáticamente.
* Presiona **⚡ CALCULAR CAPACIDAD** para generar la memoria.

### 2. Terminal Interactiva
```bash
python main.py
```
* Te solicitará elegir tu sistema de unidades al inicio y te guiará paso a paso.
