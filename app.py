import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

# URL de conexión a la BD
DB_URL = "postgresql://neondb_owner:npg_dVXmnRM80Yah@ep-square-voice-a80aojxa-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

def run_query(query, params=None, fetch=False):
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        results = cursor.fetchall() if fetch else None
        conn.commit()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        st.error(f"Error en la base de datos: {e}")
        return None

def to_float(val):
    try:
        return float(val)
    except:
        return 0.0

st.title("Registro y Cálculo de Finanzas Mensuales")

# Seleccionar año
anio = st.number_input("Año", min_value=2000, max_value=2100, value=datetime.datetime.now().year)

# Meses
meses = [
    "Enero", "Febrero", "Marzo", "Abril",
    "Mayo", "Junio", "Julio", "Agosto",
    "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Inicializar session_state
if "mes_seleccionado" not in st.session_state:
    st.session_state.mes_seleccionado = None

# Si no hay mes seleccionado, mostrar botones
if st.session_state.mes_seleccionado is None:
    st.subheader("Seleccione el mes para ingresar los datos")
    col1, col2, col3, col4 = st.columns(4)

    for i, mes in enumerate(meses):
        if i % 4 == 0:
            col = col1
        elif i % 4 == 1:
            col = col2
        elif i % 4 == 2:
            col = col3
        else:
            col = col4

        if col.button(mes, key=f"mes_{i}"):
            st.session_state.mes_seleccionado = (mes, i + 1)
            st.query_params["mes"] = str(i + 1)

# Si aún no hay selección, detener
if st.session_state.mes_seleccionado is None:
    st.stop()

# Botón para regresar
if st.button("🔙 Volver a seleccionar mes"):
    st.session_state.mes_seleccionado = None
    st.stop()

selected_month = st.session_state.mes_seleccionado

# Buscar si ya existen datos
registro_existente = run_query(
    "SELECT * FROM finanzas_mensuales WHERE anio = %s AND mes = %s",
    (anio, selected_month[1]),
    fetch=True
)

datos = registro_existente[0] if registro_existente else {}

# Formulario de ingreso
st.header(f"Ingreso de datos para: {selected_month[0]} {anio}")

# Salarios semanales
st.subheader("Ingresar 5 salarios semanales")
salarios_semanales = []
for semana in range(1, 6):
    salario_sem = st.number_input(
        f"Salario Semana {semana}",
        min_value=0.0,
        format="%.2f",
        value=to_float(datos.get(f"salario_semana{semana}")),
        key=f"salario_{semana}"
    )
    salarios_semanales.append(salario_sem)

total_salario_mensual = sum(salarios_semanales)
st.write(f"**Total salario mensual: ₡{total_salario_mensual:.2f}**")

# Pensión alimenticia
pension_alimenticia = st.number_input(
    "Pensión Alimenticia", min_value=0.0, format="%.2f",
    value=to_float(datos.get("pension_alimenticia"))
)

total_ingresos = total_salario_mensual + pension_alimenticia
st.write(f"**Total ingresos (Salario mensual + Pensión): ₡{total_ingresos:.2f}**")

# Gastos fijos
st.subheader("Gastos Fijos")
cuota_carro = st.number_input("Cuota del carro", min_value=0.0, format="%.2f", value=to_float(datos.get("cuota_carro")))
cable_internet = st.number_input("Cable e internet", min_value=0.0, format="%.2f", value=to_float(datos.get("cable_internet")))
telefono = st.number_input("Teléfono", min_value=0.0, format="%.2f", value=to_float(datos.get("telefono")))
moto = st.number_input("Moto", min_value=0.0, format="%.2f", value=to_float(datos.get("moto")))

total_gastos_fijos = cuota_carro + cable_internet + telefono + moto
st.write(f"**Total gastos fijos: ₡{total_gastos_fijos:.2f}**")

disponible_real = total_ingresos - total_gastos_fijos

# Gastos variables
st.subheader("Gastos Variables")
ahorro = round(total_ingresos * 0.10, 2)
st.write(f"Ahorro (10% de ingresos): ₡{ahorro:.2f}")
alimentacion = st.number_input("Alimentación", min_value=0.0, format="%.2f", value=to_float(datos.get("alimentacion")))
transporte = st.number_input("Transporte", min_value=0.0, format="%.2f", value=to_float(datos.get("transporte")))
otros = st.number_input("Otros", min_value=0.0, format="%.2f", value=to_float(datos.get("otros")))
marchamo = st.number_input("Marchamo", min_value=0.0, format="%.2f", value=to_float(datos.get("marchamo")))

total_gastos_variables = ahorro + alimentacion + transporte + otros + marchamo
st.write(f"**Total gastos variables: ₡{total_gastos_variables:.2f}**")

disponible_final = disponible_real - total_gastos_variables

# Alerta si disponible final es muy bajo
if disponible_final < 5000:
    st.warning("⚠️ ¡Cuidado! El dinero disponible al final del mes es muy bajo.")

# Resumen final
st.markdown("---")
st.subheader("📊 Resumen Financiero del Mes")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Total ingresos:** ₡{total_ingresos:.2f}")
    st.write(f"**Total gastos fijos:** ₡{total_gastos_fijos:.2f}")
    st.write(f"**Ahorro automático:** ₡{ahorro:.2f}")
with col2:
    st.write(f"**Total gastos variables:** ₡{total_gastos_variables:.2f}")
    st.write(f"**Disponible real:** ₡{disponible_final:.2f}")

# Guardar
if st.button("Guardar registro en base de datos"):
    query = """
        INSERT INTO finanzas_mensuales (
            anio, mes, salario_semana1, salario_semana2, salario_semana3, salario_semana4, salario_semana5,
            pension_alimenticia, total_ingresos,
            cuota_carro, cable_internet, telefono, moto, total_gastos_fijos,
            disponible_real, ahorro, alimentacion, transporte, otros, marchamo,
            total_gastos_variables, disponible_antes_variables, concepto_fijos, concepto_variables
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (anio, mes) DO UPDATE SET
            salario_semana1 = EXCLUDED.salario_semana1,
            salario_semana2 = EXCLUDED.salario_semana2,
            salario_semana3 = EXCLUDED.salario_semana3,
            salario_semana4 = EXCLUDED.salario_semana4,
            salario_semana5 = EXCLUDED.salario_semana5,
            pension_alimenticia = EXCLUDED.pension_alimenticia,
            total_ingresos = EXCLUDED.total_ingresos,
            cuota_carro = EXCLUDED.cuota_carro,
            cable_internet = EXCLUDED.cable_internet,
            telefono = EXCLUDED.telefono,
            moto = EXCLUDED.moto,
            total_gastos_fijos = EXCLUDED.total_gastos_fijos,
            disponible_real = EXCLUDED.disponible_real,
            ahorro = EXCLUDED.ahorro,
            alimentacion = EXCLUDED.alimentacion,
            transporte = EXCLUDED.transporte,
            otros = EXCLUDED.otros,
            marchamo = EXCLUDED.marchamo,
            total_gastos_variables = EXCLUDED.total_gastos_variables,
            disponible_antes_variables = EXCLUDED.disponible_antes_variables,
            concepto_fijos = EXCLUDED.concepto_fijos,
            concepto_variables = EXCLUDED.concepto_variables
    """
    params = (
        anio, selected_month[1], *salarios_semanales,
        pension_alimenticia, total_ingresos,
        cuota_carro, cable_internet, telefono, moto, total_gastos_fijos,
        disponible_real, ahorro, alimentacion, transporte, otros, marchamo,
        total_gastos_variables, disponible_real, "Fijos", "Variables"
    )
    result = run_query(query, params)
    if result is None:
        st.success("Registro guardado exitosamente.")
    else:
        st.error("No se pudo guardar el registro.")

# Mostrar registros
if st.checkbox("Mostrar registros guardados"):
    registros = run_query("SELECT * FROM finanzas_mensuales ORDER BY anio DESC, mes DESC", fetch=True)
    if registros:
        st.write(registros)
    else:
        st.write("No hay registros guardados aún.")
