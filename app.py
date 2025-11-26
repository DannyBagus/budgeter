import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Datei-Pfad für die "Master-Datenbank"
MASTER_FILE = 'master_ausgaben.csv'

# Erwartete Spaltenstruktur
REQUIRED_COLUMNS = ['Datum', 'Detail', 'Betrag CHF', 'Kategorie']

st.set_page_config(page_title="Finanz-Dashboard 360°", layout="wide")
st.title("💰 Finanz-Cockpit & Daten-Manager")

# ---------------------------------------------------------
# 1. Hilfsfunktionen (Backend-Logik)
# ---------------------------------------------------------

def load_master_data():
    """Lädt die Master-CSV oder erstellt eine leere, falls nicht vorhanden."""
    if os.path.exists(MASTER_FILE):
        try:
            df = pd.read_csv(MASTER_FILE)
            # Datumsformat sicherstellen
            df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y', errors='coerce')
            return df
        except Exception as e:
            st.error(f"Fehler beim Laden der Master-Datei: {e}")
            return pd.DataFrame(columns=REQUIRED_COLUMNS)
    else:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def save_to_master(df):
    """Speichert den DataFrame zurück in die CSV (Datum wieder als String)."""
    df_save = df.copy()
    df_save['Datum'] = df_save['Datum'].dt.strftime('%d.%m.%Y')
    df_save.to_csv(MASTER_FILE, index=False)

# ---------------------------------------------------------
# 2. Sidebar: Datei-Upload & Daten-Management
# ---------------------------------------------------------
st.sidebar.header("📥 Daten-Import")

uploaded_file = st.sidebar.file_uploader("Neue CSV hochladen", type=['csv'])

if uploaded_file is not None:
    try:
        new_df = pd.read_csv(uploaded_file)
        
        # Prüfung: Sind alle Spalten da?
        if not set(REQUIRED_COLUMNS).issubset(new_df.columns):
            st.sidebar.error(f"Fehler: CSV benötigt Spalten: {REQUIRED_COLUMNS}")
        else:
            master_df = load_master_data()
            
            # Datenaufbereitung der NEUEN Daten
            new_df['Datum'] = pd.to_datetime(new_df['Datum'], format='%d.%m.%Y', errors='coerce')
            
            # Betrag bereinigen (Falls Strings mit ' kommen)
            if new_df['Betrag CHF'].dtype == 'object':
                new_df['Betrag CHF'] = new_df['Betrag CHF'].str.replace("'", "").astype(float)
            
            rows_before = len(master_df)
            
            # Merge & Duplikate entfernen
            combined_df = pd.concat([master_df, new_df])
            combined_df = combined_df.drop_duplicates(subset=['Datum', 'Detail', 'Betrag CHF'], keep='first')
            
            rows_added = len(combined_df) - rows_before
            
            if st.sidebar.button(f"{rows_added} neue Zeilen speichern?"):
                save_to_master(combined_df)
                st.sidebar.success("Gespeichert! Bitte Seite neu laden (F5).")
                
    except Exception as e:
        st.sidebar.error(f"Fehler beim Verarbeiten: {e}")

st.sidebar.markdown("---")

# ---------------------------------------------------------
# 3. Das Dashboard (Visualisierung)
# ---------------------------------------------------------

df = load_master_data()

if df.empty:
    st.info("👋 Willkommen! Noch keine Daten vorhanden. Bitte lade links deine erste CSV-Datei hoch.")
    st.stop()

# Hilfsspalten
df['Monat_Jahr'] = df['Datum'].dt.to_period('M').astype(str)

# --- A. Datumsfilter ---
st.sidebar.subheader("🔎 Zeit-Filter")
min_date = df['Datum'].min()
max_date = df['Datum'].max()

if pd.isnull(min_date) or pd.isnull(max_date):
    st.warning("Keine gültigen Datumsangaben gefunden.")
    st.stop()

start_date, end_date = st.sidebar.date_input(
    "Zeitraum",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Filtern
mask = (df['Datum'] >= pd.to_datetime(start_date)) & (df['Datum'] <= pd.to_datetime(end_date))
df_filtered = df.loc[mask].copy()

# ---------------------------------------------------------
# 4. Logik für Einnahmen vs. Ausgaben
# ---------------------------------------------------------
# Konvention aus Prompt:
# Ausgaben > 0 (Positiv)
# Einnahmen < 0 (Negativ)

# Wir trennen die Dataframes für einfachere Berechnung
df_expenses = df_filtered[df_filtered['Betrag CHF'] > 0].copy()
df_income = df_filtered[df_filtered['Betrag CHF'] < 0].copy()

# Summen berechnen
# Bei Income drehen wir das Vorzeichen für die Anzeige um (* -1), damit es "positiv" aussieht
total_expenses = df_expenses['Betrag CHF'].sum()
total_income = df_income['Betrag CHF'].sum() * -1 
balance = total_income - total_expenses
savings_rate = (balance / total_income * 100) if total_income > 0 else 0

# --- B. KPIs ---
col1, col2, col3, col4 = st.columns(4)

col1.metric("Einnahmen", f"CHF {total_income:,.2f}", delta_color="normal")
col2.metric("Ausgaben", f"CHF {total_expenses:,.2f}", delta_color="inverse") # Inverse macht Rot bei hohen Werten
col3.metric("Bilanz (Sparbetrag)", f"CHF {balance:,.2f}", delta=f"{savings_rate:.1f}% Sparquote")
col4.metric("Transaktionen", len(df_filtered))

st.divider()

# --- C. Grafiken ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Ausgaben nach Kategorie")
    if not df_expenses.empty:
        fig_pie = px.pie(
            df_expenses, 
            values='Betrag CHF', 
            names='Kategorie', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Keine Ausgaben im gewählten Zeitraum.")

with col_chart2:
    st.subheader("Einnahmen vs. Ausgaben (Trend)")
    
    # Wir müssen Einnahmen und Ausgaben pro Monat gruppieren
    monthly_exp = df_expenses.groupby('Monat_Jahr')['Betrag CHF'].sum().reset_index()
    monthly_exp['Typ'] = 'Ausgaben'
    
    monthly_inc = df_income.groupby('Monat_Jahr')['Betrag CHF'].sum().reset_index()
    monthly_inc['Betrag CHF'] = monthly_inc['Betrag CHF'] * -1 # Vorzeichen drehen für Chart
    monthly_inc['Typ'] = 'Einnahmen'
    
    # Zusammenfügen für Plotly
    df_trend = pd.concat([monthly_exp, monthly_inc])
    
    if not df_trend.empty:
        fig_bar = px.bar(
            df_trend, 
            x='Monat_Jahr', 
            y='Betrag CHF', 
            color='Typ',
            barmode='group', # Nebeneinander
            color_discrete_map={'Einnahmen': '#2ecc71', 'Ausgaben': '#e74c3c'} # Grün / Rot
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Keine Daten für Trend.")

# --- D. Drill Down Tabelle ---
st.divider()
st.subheader("Details")

cats = ["Alle"] + sorted(df_filtered['Kategorie'].astype(str).unique().tolist())
sel_cat = st.selectbox("Kategorie filtern:", cats)

if sel_cat != "Alle":
    df_display = df_filtered[df_filtered['Kategorie'] == sel_cat]
else:
    df_display = df_filtered

# Styling Funktion für die Tabelle (Rot/Grün)
def color_amounts(val):
    color = 'red' if val > 0 else 'green' # >0 sind Ausgaben (Rot), <0 Einnahmen (Grün)
    return f'color: {color}'

# Tabelle anzeigen
st.dataframe(
    df_display.sort_values(by="Datum", ascending=False).style.map(color_amounts, subset=['Betrag CHF']),
    column_config={
        "Betrag CHF": st.column_config.NumberColumn(format="CHF %.2f"),
        "Datum": st.column_config.DateColumn(format="DD.MM.YYYY"),
    },
    use_container_width=True,
    hide_index=True
)