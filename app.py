import streamlit as st
import math

# Ustawienia strony Streamlit
st.set_page_config(page_title="Zaawansowany Bilans Stechiometryczny - Lębork", layout="wide")

st.title("🔥 Stechiometryczny Kalkulator Odzysku Ciepła ze Spalin")
st.subheader("Modelowanie parametrów spalin na bazie rzeczywistej wilgotności biomasy")

st.markdown("""
Aplikacja porzuca uproszczone dane z pomiarów emisyjnych na rzecz **czystej chemii i fizyki spalania**. 
Na podstawie wprowadzonych parametrów operacyjnych oraz wilgotności paliwa, program wylicza 
rzeczywisty stopień zawilżenia spalin, punkt rosy oraz całkowitą moc cieplną dla nowego skrubera.
""")

# --- PANEL BOCZNY: PARAMETRY WEJŚCIOWE ---
st.sidebar.header("⚙️ Rzeczywiste parametry operacyjne")

V_pomiaru = st.sidebar.number_input(
    "Strumień spalin w warunkach pomiaru (m³/h)", 
    min_value=5000, max_value=30000, value=19738, step=500,
    help="Rzeczywisty, gorący strumień spalin płynący w kanale (z raportu: 19 738 m³/h)"
)

T_wlot = st.sidebar.slider(
    "Temperatura spalin z kotła (°C)", 
    min_value=100, max_value=220, value=163, step=1,
    help="Temperatura spalin na wylocie z elektrofiltru (z raportu: 163°C)"
)

O2_stat = st.sidebar.slider(
    "Zawartość tlenu O₂ w spalinach (%)", 
    min_value=3.0, max_value=15.0, value=7.51, step=0.1,
    help="Zmierzony poziom tlenu resztkowego (z raportu: 7,51%)"
)

st.sidebar.markdown("---")
st.sidebar.header("🪵 Charakterystyka paliwa (Biomasa)")

W_paliwa = st.sidebar.slider(
    "Rzeczywista wilgotność biomasy (%)", 
    min_value=10, max_value=60, value=45, step=1,
    help="Wprowadź wilgotność roboczą zrębki/trocin trafiających na ruszt (np. 40-50%)"
)

st.sidebar.markdown("---")
st.sidebar.header("🌡️ Parametry nowego skrubera")

T_wylot_skruber = st.sidebar.slider(
    "Temperatura spalin za nowym skruberem (°C)", 
    min_value=25, max_value=60, value=45, step=1,
    help="Docelowa temperatura spalin po schłodzeniu w wieży natryskowej"
)

# --- MODEL MATEMATYCZNO-STECHIOMETRYCZNY (Spalanie drewna) ---
# Skład suchej masy biomasy (standardowe udziały masowe dla drewna):
# C = 50%, H = 6%, O = 43%, N = 1%
C_suche = 0.50
H_suche = 0.06
O_suche = 0.43

# Przeliczenie na 1 kg paliwa roboczego (z uwzględnieniem wilgotności W)
W_frac = W_paliwa / 100.0
C_rob = C_suche * (1.0 - W_frac)
H_rob = H_chemiczny = H_suche * (1.0 - W_frac)
O_rob = O_suche * (1.0 - W_frac)
W_rob = W_frac  # woda wolna z paliwa

# Minimalne zapotrzebowanie na tlen do spalenia 1 kg paliwa (kmol O2 / kg paliwa)
O2_min_kmol = (C_rob / 12.01) + (H_rob / 4.032) - (O_rob / 32.0)
V_pow_min_suchy = (O2_min_kmol / 0.21) * 22.414  # Nm³ suchego powietrza / kg paliwa

# Wyznaczenie współczynnika nadmiaru powietrza (lambda) na podstawie poziomu O2 ze suwaka
lambda_coeff = 21.0 / (21.0 - O2_stat)

# Objętość poszczególnych składników spalin z 1 kg paliwa roboczego (w warunkach normalnych)
V_CO2 = (C_rob / 12.01) * 22.414
V_N2 = V_pow_min_suchy * lambda_coeff * 0.79
V_O2_resztkowy = V_pow_min_suchy * (lambda_coeff - 1.0) * 0.21
V_suchych_spalin_1kg = V_CO2 + V_N2 + V_O2_resztkowy

# Masa pary wodnej z 1 kg paliwa roboczego:
# 1. Woda ze spalania wodoru: H_rob * (18.016 / 2.016)
# 2. Woda wolna (wilgotność paliwa): W_rob
m_H2O_1kg = H_rob * 8.9365 + W_rob  
V_H2O_1kg = (m_H2O_1kg / 18.016) * 22.414

# --- OBLICZENIE STOPNIA ZAWILŻENIA X ---
Masa_suchych_spalin_1kg = V_CO2 * (44.01/22.414) + V_N2 * (28.01/22.414) + V_O2_resztkowy * (32.0/22.414)
X_wyliczone = m_H2O_1kg / Masa_suchych_spalin_1kg  # kg H2O / kg suchego gazu

# --- PRZELICZENIE STRUMIENI NA PODSTAWIE STRUMIENIA POMIAROWEGO (V_pomiaru) ---
# Przeliczenie rzeczywistych m³/h przy temperaturze T_wlot na warunki normalne (wilgotne)
T_K = T_wlot + 273.15
V_normalny_wilgotny = V_pomiaru * (273.15 / T_K)  # Nm³/h wilgotnych

# Udział objętościowy pary wodnej w spalinach
vol_fraction_H2O = V_H2O_1kg / (V_suchych_spalin_1kg + V_H2O_1kg)
V_suchy_normalny = V_normalny_wilgotny * (1.0 - vol_fraction_H2O)  # Nm³/h suchego gazu

# Strumienie masowe dla bilansu energii
Gęstość_suchy_N = 1.357  # kg/m³u
m_sucha_sekunda = (V_suchy_normalny * Gęstość_suchy_N) / 3600  # kg/s
m_para_wlot_sekunda = m_sucha_sekunda * X_wyliczone  # kg/s
produkcja_wody_kocioł_h = m_para_wlot_sekunda * 3600  # kg/h (litry/h)

# --- PUNKT ROSY ---
p_total = 101.3  # kPa
p_v = (X_wyliczone) / (0.622 + X_wyliczone) * p_total
T_dew = 100 * (p_v / 101.3) ** 0.25 + 25

# --- BILANS ENERGETYCZNY NOWEGO SKRUBERA ---
Cp_suchy = 1.05
Cp_para = 1.86
r_kondensacja = 2260

delta_T_jawne = T_wlot - T_wylot_skruber
Q_jawne = (m_sucha_sekunda * Cp_suchy + m_para_wlot_sekunda * Cp_para) * delta_T_jawne

if T_wylot_skruber < T_dew:
    # Wilgotność nasycenia na wylocie ze skrubera
    X_wylot_sat = 0.622 * (10 ** ((7.5 * T_wylot_skruber) / (237.3 + T_wylot_skruber))) * 0.611 / p_total
    X_wylot = min(X_wyliczone, X_wylot_sat)
    m_para_wylot = m_sucha_sekunda * X_wylot
    m_skroplona = max(0.0, m_para_wlot_sekunda - m_para_wylot)
    Q_utajone = m_skroplona * r_kondensacja
    ilosc_kondensatu_h = m_skroplona * 3600
else:
    Q_utajone = 0.0
    ilosc_kondensatu_h = 0.0

Q_calkowita = Q_jawne + Q_utajone

# --- PREZENTACJA WYNIKÓW TERMOMEDYCZNYCH ---
st.markdown("### 🔍 Wyniki rzeczywistego bilansu stechiometrycznego")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Rzeczywisty parametr X (wyliczony)", value=f"{X_wyliczone:.4f} kg/kg")
with col2:
    st.metric(label="Rzeczywisty Punkt Rosy", value=f"{T_dew:.1f} °C")
with col3:
    st.metric(label="Fizyczny strumień wody w rurze", value=f"{produkcja_wody_kocioł_h:.1f} kg/h")
with col4:
    st.metric(label="Łączna moc odzysku cieplnego", value=f"{Q_calkowita:.1f} kW", delta=f"{(Q_calkowita - 600.0):.1f} kW vs baza")

st.markdown("---")

# Interaktywny komentarz inżynierski
st.subheader("📊 Analiza i wnioski do rozmowy z projektantami:")
col_l, col_r = st.columns(2)

with col_l:
    st.info(f"""
    **Porównanie z raportem MADEX:**
    * Wykazane zawilżenie w raporcie: **0.044 kg/kg** (Punkt rosy: **38.4°C**).
    * Wyliczone chemicznie zawilżenie dla zrębki {W_paliwa}%: **{X_wyliczone:.4f} kg/kg** (Punkt rosy: **{T_dew:.1f}°C**).
    * *Różnica masowa:* W każdej godzinie w spalinach płynie **{produkcja_wody_kocioł_h:.1f} kg** wody. Raport laboratoryjny "widział" tylko **611 kg**, gubiąc resztę pary przegrzanej!
    """)

with col_r:
    if Q_utajone > 0:
        st.success(f"""
        **Status pracy nowego skrubera:**
        * Przy powrocie glikolu ze schematu (38°C), Twój układ schładza spaliny do {T_wylot_skruber}°C, czyli **poniżej punktu rosy**.
        * Ilość odzyskiwanego ciepła kondensacji (utajonego): **{Q_utajone:.1f} kW**.
        * Produkcja czystego kondensatu w wieży: **{ilosc_kondensatu_h:.1f} litrów/godzinę**.
        """)
    else:
        st.warning(f"""
        **Status pracy nowego skrubera:**
        * Obecnie schładzasz spaliny do {T_wylot_skruber}°C, co przy punkcie rosy {T_dew:.1f}°C oznacza **pracę całkowicie suchą**.
        * Aby uruchomić kondensację i drastycznie podnieść moc układu, obniż suwakiem temperaturę wylotową ze skrubera poniżej {T_dew:.1f}°C.
        """)

st.caption("Aplikacja zaktualizowana 30 września 2026 r. Model fizykochemiczny oparty na stechiometrii spalania celulozy leśnej.")
