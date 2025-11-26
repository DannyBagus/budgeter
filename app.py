import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time

# ---------------------------------------------------------
# 0. Konfiguration
# ---------------------------------------------------------
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
# 2. Sidebar: Daten-Import (Stabilisiert)
# ---------------------------------------------------------
st.sidebar.header("📥 Daten-Import")

# --- A. Session State initialisieren ---
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0
if 'staging_df' not in st.session_state:
    st.session_state.staging_df = None  # Hier parken wir die Daten vor dem Speichern

# --- B. Datei Uploader ---
uploaded_file = st.sidebar.file_uploader(
    "Neue CSV-Abrechnung hochladen", 
    type=['csv'], 
    key=f"uploader_{st.session_state.uploader_key}"
)

# --- C. Verarbeitungs-Logik (läuft sofort nach Upload) ---
if uploaded_file is not None and st.session_state.staging_df is None:
    try:
        temp_df = pd.read_csv(uploaded_file)
        
        # Check: Passen die Spalten?
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in temp_df.columns]
        
        if not missing_cols:
            # Fall 1: Perfekter Match -> Direkt in den Zwischenspeicher
            st.session_state.staging_df = temp_df
            st.rerun() # UI neu laden
            
        else:
            # Fall 2: Mapping nötig
            st.sidebar.warning("⚠️ Spalten zuweisen:")
            
            with st.sidebar.form("mapping_form"):
                col_map = {}
                for req_col in REQUIRED_COLUMNS:
                    # Versuch einer automatischen Zuordnung
                    default_idx = 0
                    for i, col_name in enumerate(temp_df.columns):
                        if req_col.lower() in col_name.lower():
                            default_idx = i
                            break
                    
                    col_map[req_col] = st.selectbox(
                        f"Ziel: '{req_col}'", 
                        options=temp_df.columns,
                        index=default_idx
                    )
                
                if st.form_submit_button("Mapping anwenden"):
                    # Umbenennen und in den Zwischenspeicher schieben
                    rename_dict = {v: k for k, v in col_map.items()}
                    mapped_df = temp_df.rename(columns=rename_dict)
                    st.session_state.staging_df = mapped_df[REQUIRED_COLUMNS]
                    st.rerun()

    except Exception as e:
        st.sidebar.error(f"Fehler beim Lesen: {e}")

# --- D. Speicher-Dialog (Nur sichtbar, wenn Daten im Zwischenspeicher sind) ---
if st.session_state.staging_df is not None:
    st.sidebar.success("Daten bereit zum Import! ✅")
    
    rows = len(st.session_state.staging_df)
    st.sidebar.caption(f"{rows} Zeilen erkannt.")
    
    # 1. Button: Speichern
    if st.sidebar.button("💾 In Master-Datei speichern"):
        try:
            master_df = load_master_data()
            new_data = st.session_state.staging_df.copy()
            
            # Datentypen erzwingen
            new_data['Datum'] = pd.to_datetime(new_data['Datum'], dayfirst=True, errors='coerce')
            
            def clean_money(val):
                if isinstance(val, str):
                    val = val.replace("'", "").replace(",", ".")
                return float(val)
            
            if new_data['Betrag CHF'].dtype == 'object':
                new_data['Betrag CHF'] = new_data['Betrag CHF'].apply(clean_money)
            
            # Zusammenfügen & Deduplizieren
            rows_before = len(master_df)
            combined_df = pd.concat([master_df, new_data])
            combined_df = combined_df.drop_duplicates(subset=['Datum', 'Detail', 'Betrag CHF'], keep='first')
            rows_added = len(combined_df) - rows_before
            
            # Speichern & Aufräumen
            save_to_master(combined_df)
            st.cache_data.clear() # Cache leeren wichtig!
            st.session_state.staging_df = None
            st.session_state.uploader_key += 1
            
            # Feedback
            msg = st.sidebar.empty()
            if rows_added > 0:
                msg.success(f"✅ {rows_added} Zeilen gespeichert!")
            else:
                msg.info("Keine neuen Zeilen (alles Duplikate).")
            
            time.sleep(2.0) # Zeit zum Lesen geben
            msg.empty()
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"Fehler beim Speichern: {e}")

    # 2. Button: Abbrechen
    if st.sidebar.button("❌ Abbrechen"):
        st.session_state.staging_df = None
        st.session_state.uploader_key += 1
        st.rerun()

st.sidebar.markdown("---")

# ---------------------------------------------------------
# 3. Dashboard Daten & Filter
# ---------------------------------------------------------

df = load_master_data()

if df.empty:
    st.info("👋 Willkommen! Noch keine Daten vorhanden. Bitte lade links deine erste CSV-Datei hoch.")
    st.stop()

df['Monat_Jahr'] = df['Datum'].dt.to_period('M').astype(str)

# --- Datumsfilter ---
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

mask = (df['Datum'] >= pd.to_datetime(start_date)) & (df['Datum'] <= pd.to_datetime(end_date))
df_filtered = df.loc[mask].copy()

# --- Daten Trennung ---
df_expenses = df_filtered[df_filtered['Betrag CHF'] > 0].copy()
df_income = df_filtered[df_filtered['Betrag CHF'] < 0].copy()

total_expenses = df_expenses['Betrag CHF'].sum()
total_income = df_income['Betrag CHF'].sum() * -1 
balance = total_income - total_expenses
savings_rate = (balance / total_income * 100) if total_income > 0 else 0

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Einnahmen", f"CHF {total_income:,.2f}", delta_color="normal")
c2.metric("Ausgaben", f"CHF {total_expenses:,.2f}", delta_color="inverse")
c3.metric("Bilanz", f"CHF {balance:,.2f}", delta=f"{savings_rate:.1f}% Sparquote")
c4.metric("Transaktionen", len(df_filtered))

st.divider()

# ---------------------------------------------------------
# 4. Interaktive Grafiken (Bar Chart statt Pie Chart)
# ---------------------------------------------------------

# --- Session State für Filter initialisieren ---
if "selected_cat_filter" not in st.session_state:
    st.session_state.selected_cat_filter = "Alle"

# Callback für Selectbox (leer lassen, State wird automatisch gehandelt)
def update_filter_from_box():
    pass

col_chart1, col_chart2 = st.columns(2)

# --- A. Ausgaben nach Kategorie (Horizontal Bar) ---
with col_chart1:
    st.subheader("Ausgaben nach Kategorie (Top)")
    
    if not df_expenses.empty:
        # 1. Daten aggregieren und sortieren
        df_cat_view = df_expenses.groupby('Kategorie', as_index=False)['Betrag CHF'].sum()
        df_cat_view = df_cat_view.sort_values(by='Betrag CHF', ascending=True) # Sortierung für Chart
        
        # 2. Bar Chart erstellen (Besser klickbar als Pie)
        fig_cat = px.bar(
            df_cat_view, 
            x='Betrag CHF', 
            y='Kategorie', 
            orientation='h', # Horizontal ist besser lesbar
            text_auto='.2s', # Zeigt Werte direkt an
            color='Kategorie', # Färbung für Wiedererkennung
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        # 3. Layout aufräumen (Keine Legende, da Labels an der Achse stehen)
        fig_cat.update_layout(
            showlegend=False, # WICHTIG: Verhindert die Verwirrung mit der Legende!
            margin=dict(l=0, r=0, t=0, b=0),
            clickmode='event+select'
        )
        
        # 4. Chart rendern & Event abfangen
        # key="cat_chart" ist wichtig für den State
        event = st.plotly_chart(
            fig_cat, 
            use_container_width=True, 
            on_select="rerun", 
            selection_mode="points", 
            key="cat_chart"
        )
        
        # 5. Klick-Logik auswerten
        if event and len(event.selection["points"]) > 0:
            try:
                # Bei Bar Charts ist "y" die Kategorie (da horizontal)
                first_point = event.selection["points"][0]
                clicked_category = first_point["y"]
                
                # Filter setzen, wenn abweichend
                if st.session_state.selected_cat_filter != clicked_category:
                    st.session_state.selected_cat_filter = clicked_category
                    st.rerun()
            except Exception:
                pass # Fehler ignorieren
        
        # Deselektieren (Klick in Leere) -> Reset auf Alle
        elif event and len(event.selection["points"]) == 0:
            if st.session_state.selected_cat_filter != "Alle":
                st.session_state.selected_cat_filter = "Alle"
                st.rerun()

    else:
        st.info("Keine Ausgaben im Zeitraum.")

# --- B. Trend Chart (Bleibt gleich) ---
with col_chart2:
    st.subheader("Trend: Einnahmen vs. Ausgaben")
    
    monthly_exp = df_expenses.groupby('Monat_Jahr')['Betrag CHF'].sum().reset_index()
    monthly_exp['Typ'] = 'Ausgaben'
    
    monthly_inc = df_income.groupby('Monat_Jahr')['Betrag CHF'].sum().reset_index()
    monthly_inc['Betrag CHF'] = monthly_inc['Betrag CHF'] * -1 
    monthly_inc['Typ'] = 'Einnahmen'
    
    df_trend = pd.concat([monthly_exp, monthly_inc])
    
    if not df_trend.empty:
        fig_bar = px.bar(
            df_trend, 
            x='Monat_Jahr', 
            y='Betrag CHF', 
            color='Typ',
            barmode='group',
            color_discrete_map={'Einnahmen': '#2ecc71', 'Ausgaben': '#e74c3c'}
        )
        fig_bar.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Keine Daten für Trend.")

# ---------------------------------------------------------
# 5. Drill-Down Tabelle (Synchronisiert)
# ---------------------------------------------------------
st.divider()

col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.subheader("🔍 Details")
with col_head2:
    if st.button("Filter zurücksetzen"):
        st.session_state.selected_cat_filter = "Alle"
        st.rerun()

cats = ["Alle"] + sorted(df_filtered['Kategorie'].astype(str).unique().tolist())

# Validierung: Ist der Filter noch gültig?
if st.session_state.selected_cat_filter not in cats:
    st.session_state.selected_cat_filter = "Alle"

# Selectbox (Synchronisiert)
sel_cat = st.selectbox(
    "Kategorie filtern:", 
    options=cats,
    key="selected_cat_filter",
    on_change=update_filter_from_box
)

if sel_cat != "Alle":
    df_display = df_filtered[df_filtered['Kategorie'] == sel_cat]
    st.info(f"Zeige Details für: **{sel_cat}**")
else:
    df_display = df_filtered

def color_amounts(val):
    color = 'red' if val > 0 else 'green'
    return f'color: {color}'

st.dataframe(
    df_display.sort_values(by="Datum", ascending=False).style.map(color_amounts, subset=['Betrag CHF']),
    column_config={
        "Betrag CHF": st.column_config.NumberColumn(format="CHF %.2f"),
        "Datum": st.column_config.DateColumn(format="DD.MM.YYYY"),
    },
    use_container_width=True,
    hide_index=True
)