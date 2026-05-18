import streamlit as st
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import json
import tempfile
from datetime import datetime

SHEET_URL = "https://docs.google.com/spreadsheets/d/1LqbZ9-4opDOr3slOkj457zx3Bh2xgC0kr2yskHPiWOI/edit"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def google_bejelentkezes():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if "gcp" in st.secrets:
                client_secret_dict = json.loads(st.secrets["gcp"]["client_secret_json"])
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    json.dump(client_secret_dict, f)
                    temp_path = f.name
                flow = InstalledAppFlow.from_client_secrets_file(temp_path, SCOPES)
            else:
                flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return gspread.authorize(creds)

st.set_page_config(page_title="Pannon Borbolt – Borértékelő", layout="centered")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700;900&display=swap');
        html, body, [class*="css"] { font-family: 'Noto Sans', sans-serif; }
        h1, h2, h3 { font-family: 'Noto Sans', sans-serif; font-weight: 900; }
        .stButton > button { font-family: 'Noto Sans', sans-serif; font-weight: 700; }
        .stTextInput > label, .stSelectbox > label,
        .stSlider > label, .stNumberInput > label,
        .stTextArea > label { font-family: 'Noto Sans', sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.image("assets/PB-main-logoRGB.png", width=300)
st.title("Borértékelő")

st.subheader("Alap adatok")
pince = st.text_input("Pincészet", placeholder="pl. Bock")
bornev = st.text_input("Bor neve", placeholder="pl. Cuvée")
evjarat = st.text_input("Évjárat", placeholder="pl. 2019")
bortipus = st.selectbox("Bortípus", ["Vörösbor", "Fehérbor", "Rozé", "Pezsgő / gyöngyöző"])
helyszin = st.text_input("Helyszín", placeholder="pl. Budapest")

st.subheader("Megjegyzés")
megjegyzes = st.text_area("Szabad szöveges megjegyzés a borról...", height=100)

st.subheader("Értékelési szempontok")
reszletes = st.toggle("Részletes értékelés")

if reszletes:
    szin = st.slider("Szín és tisztaság", min_value=1, max_value=10, value=5)
    illat = st.slider("Illat intenzitása", min_value=1, max_value=10, value=5)
    gyumolcs = st.slider("Gyümölcsösség", min_value=1, max_value=10, value=5)
    alkohol = st.slider("Alkoholérzet", min_value=1, max_value=10, value=5)
    savak = st.slider("Savérzet", min_value=1, max_value=10, value=5)
    asvanyok = st.slider("Ásványosság", min_value=1, max_value=10, value=5)
    izhosszusag = st.slider("Ízhosszúság", min_value=1, max_value=10, value=5)
    testesseg = st.slider("Testesség", min_value=1, max_value=10, value=5)
    if bortipus == "Vörösbor":
        tanninok = st.slider("Tanninok", min_value=1, max_value=10, value=5, key="tanninok")
    else:
        tanninok = None
    if bortipus == "Pezsgő / gyöngyöző":
        st.subheader("Buborék jellemzők")
        buborek_finoms = st.slider("Buborék finomsága", min_value=1, max_value=10, value=5, key="buborek_finoms")
        buborek_allando = st.slider("Buborék állandósága", min_value=1, max_value=10, value=5, key="buborek_allando")
        buborek_menny = st.slider("Buborék mennyisége", min_value=1, max_value=10, value=5, key="buborek_menny")
    else:
        buborek_finoms = None
        buborek_allando = None
        buborek_menny = None
else:
    szin = illat = gyumolcs = alkohol = savak = asvanyok = izhosszusag = testesseg = None
    tanninok = buborek_finoms = buborek_allando = buborek_menny = None

st.subheader("Végső pontszám")
kizart = st.checkbox("Kizárt / hibás bor")

if kizart:
    vegso_pont = "X"
    verdict = "Kizárt"
    st.error("❌ Kizárt / hibás bor")
else:
    vegso_pont = st.number_input("Pontszám (50–100)", min_value=50, max_value=100, value=85, step=1)

    if vegso_pont >= 95:
        verdict = "Kiemelkedő, briliáns bor"
    elif vegso_pont >= 90:
        verdict = "Egyedi, elegáns, nagy bor"
    elif vegso_pont >= 85:
        verdict = "Nagyon jó bor"
    elif vegso_pont >= 80:
        verdict = "Jó bor"
    elif vegso_pont >= 75:
        verdict = "Megbízható"
    else:
        verdict = "Nem elfogadható, gyenge bor"

    st.metric(label="Értékelés", value=f"{vegso_pont} pont", delta=verdict)

if st.button("💾 Mentés Google Sheetsbe"):
    if bornev.strip() == "":
        st.warning("Kérlek add meg a bor nevét!")
    else:
        try:
            gc = google_bejelentkezes()
            sheet = gc.open_by_url(SHEET_URL).sheet1
            sor = [
                datetime.now().strftime("%Y-%m-%d"),
                helyszin,
                pince,
                bornev,
                evjarat,
                bortipus,
                vegso_pont,
                megjegyzes,
                szin if szin is not None else "",
                illat if illat is not None else "",
                gyumolcs if gyumolcs is not None else "",
                alkohol if alkohol is not None else "",
                asvanyok if asvanyok is not None else "",
                savak if savak is not None else "",
                izhosszusag if izhosszusag is not None else "",
                testesseg if testesseg is not None else "",
                tanninok if tanninok is not None else "",
                buborek_finoms if buborek_finoms is not None else "",
                buborek_allando if buborek_allando is not None else "",
                buborek_menny if buborek_menny is not None else ""
            ]
            sheet.append_row(sor)
            st.success(f"{bornev} sikeresen mentve! ({vegso_pont} pont)")
        except Exception as e:
            st.error(f"Hiba részletei: {type(e).__name__}: {e}")