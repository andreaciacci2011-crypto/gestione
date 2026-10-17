import streamlit as st
import calendar
import os
import json
import pandas as pd

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Gestione Turni Web", page_icon="📅", layout="wide")

# Percorsi per i salvataggi
SAVE_DIR = "SALVATAGGI"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

ANAG_FILE = os.path.join(SAVE_DIR, "anagrafica.json")
SCHED_FILE = os.path.join(SAVE_DIR, "turni_salvati.json")

ITALIAN_MONTHS = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]
ITALIAN_DAYS = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]

# Generatore orari 24h
ALL_HOURS = ["--:--"]
for h in range(24):
    for m in [0, 30]:
        ALL_HOURS.append(f"{h:02d}:{m:02d}")

# Funzioni di caricamento e salvataggio dati
def load_data():
    operators = []
    clients = []
    if os.path.exists(ANAG_FILE):
        try:
            with open(ANAG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                operators = data.get("operators", [])
                clients = data.get("clients", [])
        except Exception:
            pass

    schedule_data = {}
    if os.path.exists(SCHED_FILE):
        try:
            with open(SCHED_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                for k, v in raw_data.items():
                    parts = k.split("|")
                    if len(parts) == 5:
                        client, y, m, d, off = parts[0], int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                        schedule_data[(client, y, m, d, off)] = v
        except Exception:
            pass
    return operators, clients, schedule_data

def save_data(operators, clients, schedule_data):
    try:
        with open(ANAG_FILE, "w", encoding="utf-8") as f:
            json.dump({"operators": operators, "clients": clients}, f, ensure_ascii=False, indent=4)
        
        raw_data = {}
        for k, v in schedule_data.items():
            client, y, m, d, off = k
            raw_data[f"{client}|{y}|{m}|{d}|{off}"] = v
        with open(SCHED_FILE, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Errore di salvataggio: {e}")

operators, clients, schedule_data = load_data()

# --- BARRA LATERALE (NAVIGAZIONE) ---
st.sidebar.title("📌 Menu Gestionale")
menu = st.sidebar.selectbox("Seleziona Sezione", ["Pianificazione Giornaliera", "Anagrafica", "Riepilogo Mensile"])

# ================= 1. ANAGRAFICA =================
if menu == "Anagrafica":
    st.title("👥 Gestione Anagrafica Operatori e Clienti")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Operatori")
        new_ops = []
        for i in range(15):
            val = operators[i] if i < len(operators) else ""
            op = st.text_input(f"Operatore {i+1}", value=val, key=f"op_{i}")
            if op.strip():
                new_ops.append(op.strip())

    with col2:
        st.subheader("Clienti")
        new_cl = []
        for i in range(15):
            val = clients[i] if i < len(clients) else ""
            cl = st.text_input(f"Cliente {i+1}", value=val, key=f"cl_{i}")
            if cl.strip():
                new_cl.append(cl.strip())

    if st.button("💾 Salva Anagrafica", type="primary"):
        save_data(new_ops, new_cl, schedule_data)
        st.success("Anagrafica salvata con successo! Ricarica la pagina.")

# ================= 2. PIANIFICAZIONE GIORNALIERA =================
elif menu == "Pianificazione Giornaliera":
    st.title("📅 Pianificazione Turni Giornaliera")
    
    active_clients = [c for c in clients if c]
    if not active_clients:
        st.warning("⚠️ Nessun cliente inserito. Vai prima nella sezione 'Anagrafica' a inserire i clienti.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            year = st.selectbox("Anno", [2026, 2027, 2028, 2029, 2030], index=0)
        with c2:
            month_str = st.selectbox("Mese", ITALIAN_MONTHS, index=9) # Ottobre di default
            month_idx = ITALIAN_MONTHS.index(month_str) + 1
        with c3:
            num_days = calendar.monthrange(year, month_idx)[1]
            day_options = [f"{d} - {ITALIAN_DAYS[calendar.weekday(year, month_idx, d)]}" for d in range(1, num_days + 1)]
            selected_day_str = st.selectbox("Giorno", day_options)
            day = int(selected_day_str.split(" - ")[0])

        st.markdown("---")
        st.markdown(f"### 📋 Turni del giorno: **{selected_day_str} {month_str} {year}**")

        op_choices = ["Nessuno"] + operators
        
        # Form per la modifica dei turni
        with st.form(key="schedule_form"):
            for client_idx, client_name in enumerate(active_clients):
                st.markdown(f"#### 👤 Cliente: `{client_name}`")
                
                for r_offset in range(3):
                    saved_op, saved_in, saved_out = schedule_data.get((client_name, year, month_idx, day, r_offset), ("", "", ""))
                    init_op = saved_op if saved_op in op_choices else "Nessuno"
                    init_in = saved_in if saved_in in ALL_HOURS else "--:--"
                    init_out = saved_out if saved_out in ALL_HOURS else "--:--"

                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    with col_a:
                        op_val = st.selectbox(f"Turno {r_offset+1} - Operatore ({client_name})", op_choices, index=op_choices.index(init_op), key=f"op_{client_idx}_{r_offset}")
                    with col_b:
                        in_val = st.selectbox(f"Entrata ({client_name} T{r_offset+1})", ALL_HOURS, index=ALL_HOURS.index(init_in), key=f"in_{client_idx}_{r_offset}")
                    with col_c:
                        out_val = st.selectbox(f"Uscita ({client_name} T{r_offset+1})", ALL_HOURS, index=ALL_HOURS.index(init_out), key=f"out_{client_idx}_{r_offset}")
                
                st.markdown("")

            submitted = st.form_submit_button("💾 Salva Turni del Giorno", type="primary")
            if submitted:
                for client_idx, client_name in enumerate(active_clients):
                    for r_offset in range(3):
                        op_v = st.session_state[f"op_{client_idx}_{r_offset}"]
                        in_v = st.session_state[f"in_{client_idx}_{r_offset}"]
                        out_v = st.session_state[f"out_{client_idx}_{r_offset}"]
                        
                        final_op = "" if op_v == "Nessuno" else op_v
                        final_in = "" if in_v == "--:--" else in_v
                        final_out = "" if out_v == "--:--" else out_v
                        
                        schedule_data[(client_name, year, month_idx, day, r_offset)] = (final_op, final_in, final_out)
                
                save_data(operators, clients, schedule_data)
                st.success("✅ Turni salvati correttamente!")

# ================= 3. RIEPILOGO MENSILE =================
elif menu == "Riepilogo Mensile":
    st.title("📊 Riepilogo Ore Mensili")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        sum_type = st.selectbox("Visualizza per", ["Clienti", "Operatori"])
    with c2:
        sum_year = st.selectbox("Anno", [2026, 2027, 2028, 2029, 2030], index=0)
    with c3:
        sum_month_str = st.selectbox("Mese", ITALIAN_MONTHS, index=9)
        sum_month_idx = ITALIAN_MONTHS.index(sum_month_str) + 1

    num_days = calendar.monthrange(sum_year, sum_month_idx)[1]
    targets = clients if sum_type == "Clienti" else operators
    active_targets = [t for t in targets if t]

    def time_to_hrs(t_str):
        if not t_str or ":" not in t_str: return 0.0
        try:
            p = t_str.split(":")
            return int(p[0]) + int(p[1])/60.0
        except: return 0.0

    def calc_hours(i_t, o_t):
        ih = time_to_hrs(i_t)
        oh = time_to_hrs(o_t)
        diff = oh - ih
        if diff < 0: diff += 24.0
        return diff if (i_t and o_t) else 0.0

    results = []
    for target in active_targets:
        tot_h = 0.0
        for day in range(1, num_days + 1):
            if sum_type == "Clienti":
                for off in range(3):
                    _, inv, outv = schedule_data.get((target, sum_year, sum_month_idx, day, off), ("", "", ""))
                    tot_h += calc_hours(inv, outv)
            else:
                for c_name in clients:
                    for off in range(3):
                        opv, inv, outv = schedule_data.get((c_name, sum_year, sum_month_idx, day, off), ("", "", ""))
                        if opv == target:
                            tot_h += calc_hours(inv, outv)
        results.append({"Nome": target, "Totale Ore": round(tot_h, 2)})

    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nessun dato disponibile per il periodo selezionato.")