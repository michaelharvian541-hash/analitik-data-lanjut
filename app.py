import math
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Analisis Perencanaan Agregat Manufaktur", layout="wide"
)

st.title("Aplikasi Analitik Perencanaan Agregat Produksi")
st.caption(
    "Simulasi Penentuan Strategi Produksi Optimal (Studi Kasus: Jason Enterprises)"
)

# Sidebar Input Parameter
st.sidebar.header("Parameter Biaya & Tenaga Kerja")
materials_cost = st.sidebar.number_input(
    "Biaya Material / Unit ($)", value=100
)
holding_cost = st.sidebar.number_input(
    "Holding Cost / Unit / Bulan ($)", value=10
)
backorder_cost = st.sidebar.number_input(
    "Backorder Cost / Unit / Bulan ($)", value=20
)
subcontract_cost = st.sidebar.number_input(
    "Subcontracting Cost / Unit ($)", value=100
)
hiring_cost = st.sidebar.number_input("Biaya Hiring / Pekerja ($)", value=50)
layoff_cost = st.sidebar.number_input("Biaya Layoff / Pekerja ($)", value=100)
wage_rate = st.sidebar.number_input("Upah / Jam ($)", value=12.50)
hrs_per_unit = st.sidebar.number_input("Jam Kerja / Unit", value=4)
init_inv = st.sidebar.number_input("Persediaan Awal (Unit)", value=200)

st.sidebar.subheader("Parameter Strategi B & C")
constant_workers = st.sidebar.number_input(
    "Jumlah Pekerja Konstan", value=10, step=1
)

# Data Default Demand & Hari Kerja
st.subheader("Data Permintaan & Hari Kerja Bulanan")
default_data = {
    "Bulan": ["Januari", "Februari", "Maret", "April", "Mei", "Juni"],
    "Demand": [500, 600, 650, 800, 900, 800],
    "Hari_Kerja": [22, 19, 21, 21, 22, 20],
}

df_input = pd.DataFrame(default_data)
edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

# -------------------------------------------------------------
# KALKULASI STRATEGI A: Chase Strategy (Vary Workforce)
# -------------------------------------------------------------
strat_a_list = []
prev_workers = 7
total_hire_a = 0
total_layoff_a = 0
total_labor_hrs_a = 0

for i, row in edited_df.iterrows():
    demand_val = float(row["Demand"]) if pd.notnull(row["Demand"]) else 0
    days_val = float(row["Hari_Kerja"]) if pd.notnull(row["Hari_Kerja"]) else 1

    # Kebutuhan produksi tidak boleh negatif
    if i == 0:
        req = max(0.0, demand_val - init_inv)
    else:
        req = max(0.0, demand_val)

    hrs_needed = req * hrs_per_unit
    hrs_per_worker = max(1.0, days_val * 8)  # Hindari pembagian dengan 0
    workers_needed = math.ceil(hrs_needed / hrs_per_worker)

    hired = max(0, workers_needed - prev_workers)
    laid_off = max(0, prev_workers - workers_needed)

    total_hire_a += hired
    total_layoff_a += laid_off
    total_labor_hrs_a += hrs_needed

    strat_a_list.append(
        {
            "Bulan": row["Bulan"],
            "Prod Req": req,
            "Jam Dibutuhkan": hrs_needed,
            "Pekerja": workers_needed,
            "Hiring": hired,
            "Layoff": laid_off,
            "Biaya Labor ($)": hrs_needed * wage_rate,
        }
    )
    prev_workers = workers_needed

cost_hiring_a = total_hire_a * hiring_cost
cost_layoff_a = total_layoff_a * layoff_cost
cost_labor_a = total_labor_hrs_a * wage_rate
total_cost_a = cost_hiring_a + cost_layoff_a + cost_labor_a

# -------------------------------------------------------------
# KALKULASI STRATEGI B: Level Strategy (Constant Workforce + Backorder)
# -------------------------------------------------------------
strat_b_list = []
curr_inv_b = float(init_inv)
total_backorder_cost_b = 0
total_holding_cost_b = 0
total_labor_cost_b = 0

for i, row in edited_df.iterrows():
    demand_val = float(row["Demand"]) if pd.notnull(row["Demand"]) else 0
    days_val = float(row["Hari_Kerja"]) if pd.notnull(row["Hari_Kerja"]) else 1

    hrs_avail = days_val * 8 * constant_workers
    actual_prod = hrs_avail / hrs_per_unit
    labor_cost = hrs_avail * wage_rate
    total_labor_cost_b += labor_cost

    end_inv = curr_inv_b + actual_prod - demand_val
    backorder = abs(end_inv) if end_inv < 0 else 0
    excess = end_inv if end_inv > 0 else 0

    b_cost = backorder * backorder_cost
    h_cost = excess * holding_cost

    total_backorder_cost_b += b_cost
    total_holding_cost_b += h_cost

    strat_b_list.append(
        {
            "Bulan": row["Bulan"],
            "Jam Tersedia": hrs_avail,
            "Produksi": actual_prod,
            "Demand": demand_val,
            "Ending Inv": end_inv,
            "Backorder": backorder,
            "Biaya Backorder ($)": b_cost,
            "Biaya Holding ($)": h_cost,
        }
    )
    curr_inv_b = end_inv

total_cost_b = (
    total_labor_cost_b + total_backorder_cost_b + total_holding_cost_b
)

# -------------------------------------------------------------
# KALKULASI STRATEGI C: Level Strategy (Constant Workforce + Subcontracting)
# -------------------------------------------------------------
strat_c_list = []
curr_inv_c = float(init_inv)
total_subcontract_cost_c = 0
total_labor_cost_c = 0

for i, row in edited_df.iterrows():
    demand_val = float(row["Demand"]) if pd.notnull(row["Demand"]) else 0
    days_val = float(row["Hari_Kerja"]) if pd.notnull(row["Hari_Kerja"]) else 1

    hrs_avail = days_val * 8 * constant_workers
    actual_prod = hrs_avail / hrs_per_unit
    labor_cost = hrs_avail * wage_rate
    total_labor_cost_c += labor_cost

    net_req = demand_val - curr_inv_c
    units_subcontract = max(0.0, net_req - actual_prod)
    sub_cost = units_subcontract * subcontract_cost
    total_subcontract_cost_c += sub_cost

    curr_inv_c = max(0.0, actual_prod + curr_inv_c - demand_val)

    strat_c_list.append(
        {
            "Bulan": row["Bulan"],
            "Req Netto": net_req,
            "Produksi Reguler": actual_prod,
            "Subcontract (Unit)": units_subcontract,
            "Biaya Subcontract ($)": sub_cost,
        }
    )

total_cost_c = total_labor_cost_c + total_subcontract_cost_c

# -------------------------------------------------------------
# RINGKASAN & VISUALISASI HASIL
# -------------------------------------------------------------
st.header("Ringkasan Hasil Perbandingan Biaya")

summary_df = pd.DataFrame(
    {
        "Strategi": [
            "Strategi A (Chase / Vary Workforce)",
            "Strategi B (Level + Backorder)",
            "Strategi C (Level + Subcontracting)",
        ],
        "Biaya Labor ($)": [cost_labor_a, total_labor_cost_b, total_labor_cost_c],
        "Hiring/Layoff ($)": [cost_hiring_a + cost_layoff_a, 0, 0],
        "Holding/Backorder ($)": [
            0,
            total_backorder_cost_b + total_holding_cost_b,
            0,
        ],
        "Subcontracting ($)": [0, 0, total_subcontract_cost_c],
        "Total Biaya ($)": [total_cost_a, total_cost_b, total_cost_c],
    }
)

st.dataframe(summary_df, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        summary_df,
        x="Strategi",
        y="Total Biaya ($)",
        color="Strategi",
        title="Perbandingan Total Biaya Antar Strategi",
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    best_strat = summary_df.loc[summary_df["Total Biaya ($)"].idxmin()]
    st.success(
        f"**Rekomendasi Strategi Optimal:**\n\n"
        f"**{best_strat['Strategi']}** merupakan strategi paling hemat dengan total biaya **${best_strat['Total Biaya ($)']:,.2f}**."
    )

# Expander Detail Rincian
with st.expander("Lihat Detail Rincian Strategi A"):
    st.dataframe(pd.DataFrame(strat_a_list))

with st.expander("Lihat Detail Rincian Strategi B"):
    st.dataframe(pd.DataFrame(strat_b_list))

with st.expander("Lihat Detail Rincian Strategi C"):
    st.dataframe(pd.DataFrame(strat_c_list))
