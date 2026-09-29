import streamlit as st

st.set_page_config(page_title="Kalkulator Bilansu Wilgoci - Lębork 2026", layout="wide")
st.title("📊 Interaktywny Bilans Wilgoci Spalin - Kocioł Polytechnik nr 7")
st.subheader("Dane bazowe: Raport MADEX z dn. 13.04.2026 (100% obciążenia)")

st.sidebar.header("⚙️ Rzeczywiste parametry z raportu (13.04.2026)")
V_suchy_raport = st.sidebar.number_input("Strumień gazu suchego (Nm³/h u)", value=11568, disabled=True)
T_wlot_raport = st.sidebar.number_input("Temperatura spalin z kotła (°C)", value=163, disabled=True)
O2_raport = st.sidebar.number_input("Zawartość tlenu O₂ (%)", value=7.51, disabled=True)

st.sidebar.markdown("---")
st.sidebar.header("🔄 Zmienna symulacji (Parametr X)")
X_symulacja = st.sidebar.slider("Stopień zawilżenia gazu X (kg H₂O / kg suchego gazu)", min_value=0.030, max_value=0.160, value=0.044, step=0.002)

st.sidebar.markdown("---")
st.sidebar.header("🌡️ Cel nowej inwestycji")
T_wylot_skruber = st.sidebar.slider("Temperatura spalin za nowym skruberem (°C)", min_value=30, max_value=60, value=45, step=1)

Gęstość_suchy_N = 1.357
Cp_suchy = 1.05
Cp_para = 1.86
r_kondensacja = 2260

m_sucha = (V_suchy_raport * Gęstość_suchy_N) / 3600
m_para_wlot = m_sucha * X_symulacja
ilosc_wody_komin_h = m_para_wlot * 3600

p_total = 101.3
p_v = (X_symulacja) / (0.622 + X_symulacja) * p_total
T_dew = 100 * (p_v / 101.3) ** 0.25 + 25

delta_T_jawne = T_wlot_raport - T_wylot_skruber
Q_jawne = (m_sucha * Cp_suchy + m_para_wlot * Cp_para) * delta_T_jawne

if T_wylot_skruber < T_dew:
    X_wylot_sat = 0.622 * (10 ** ((7.5 * T_wylot_skruber) / (237.3 + T_wylot_skruber))) * 0.611 / p_total
    X_wylot = min(X_symulacja, X_wylot_sat)
    m_para_wylot = m_sucha * X_wylot
    m_skroplona = max(0.0, m_para_wlot - m_para_wylot)
    Q_utajone = m_skroplona * r_kondensacja
    ilosc_kondensatu_h = m_skroplona * 3600
else:
    Q_utajone = 0.0
    ilosc_kondensatu_h = 0.0

Q_calkowita = Q_jawne + Q_utajone

st.markdown("### 🔍 Wyniki analizy dla wybranego parametru X")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Ilość wody w spalinach uciekająca do komina", value=f"{ilosc_wody_komin_h:.1f} kg/h", delta=f"{(ilosc_wody_komin_h - 611.4):.1f} kg/h vs raport" if X_symulacja != 0.044 else None)
with col2:
    st.metric(label="Rzeczywisty Punkt Rosy", value=f"{T_dew:.1f} °C")
with col3:
    st.metric(label="Możliwa do odzyskania moc cieplna", value=f"{Q_calkowita:.1f} kW")

st.markdown("---")
st.subheader("💡 Kontekst do dyskusji z laboratorium MADEX:")
col_left, col_right = st.columns(2)
with col_left:
    st.info(f"**Stan wg sprawozdania (X = 0.044):**\n* Woda w spalinach: **611 kg/h**.\n* Punkt rosy: **38.4 °C**.")
with col_right:
    if X_symulacja >= 0.120:
        st.success(f"**Rzeczywisty stan oczekiwany (Twój suwak X = {X_symulacja:.3f}):**\n* Woda w spalinach: **{ilosc_wody_komin_h:.1f} kg/h**.\n* Punkt rosy: **{T_dew:.1f} °C**.\n* Wykroplony kondensat w nowym skruberze: **{ilosc_kondensatu_h:.1f} l/h**.\n* Moc odzysku: **{Q_calkowita:.1f} kW**.")
    else:
        st.warning("Przesuń suwak 'X' po lewej stronie do wartości 0.120 - 0.140, aby zobaczyć bilans dla mokrej zrębki.")
