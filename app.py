from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from main import Appliance, DEFAULT_TARIFF, default_appliances, evaluate, genetic_algorithm, greedy_schedule

st.set_page_config(page_title="SmartHome Energy Optimization", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")

# ---------- Theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --bg:#071426; --panel:#0b1e35; --panel2:#102844; --line:#1e3b5e; --muted:#9db4d0; --text:#edf5ff; --blue:#3b9cff; --cyan:#39d4df; --green:#27d79a; --orange:#ffb547; }
.stApp { background: radial-gradient(ellipse at 75% 0%, #102c4b 0%, #071426 45%, #06111f 100%); color:var(--text); font-family:'DM Sans',sans-serif; }
[data-testid="stHeader"] { background:rgba(7,20,38,.82); }
[data-testid="stSidebar"] { background:#08182b; border-right:1px solid #1b3552; }
[data-testid="stSidebar"] * { color:var(--text); }
.block-container { padding-top:1.35rem; padding-bottom:1rem; max-width:1600px; }
h1,h2,h3,h4 { font-family:'Space Grotesk',sans-serif !important; color:#f4f8ff !important; }
p, label, .stMarkdown { color:#dbe9fb; }
.small-muted { color:#9db4d0; font-size:.86rem; }
.hero { padding:22px 26px; border:1px solid #21466d; border-radius:20px; background:linear-gradient(115deg,rgba(21,64,105,.86),rgba(10,30,53,.92) 58%,rgba(12,55,66,.72)); margin-bottom:18px; box-shadow:0 12px 34px rgba(0,0,0,.18); }
.hero-kicker { color:#59d8e7; text-transform:uppercase; letter-spacing:.16em; font-weight:700; font-size:.75rem; }
.hero h1 { font-size:2.05rem; margin:.35rem 0 .2rem; }
.hero p { color:#bdd1e9; margin:0; }
.metric-card { background:linear-gradient(145deg,rgba(15,39,66,.98),rgba(9,27,48,.98)); border:1px solid #1d4168; border-radius:16px; padding:17px 18px; min-height:123px; box-shadow:0 8px 20px rgba(0,0,0,.12); }
.metric-label { color:#b5c9e2; font-size:.84rem; margin-bottom:8px; }
.metric-value { font-family:'Space Grotesk',sans-serif; font-size:1.65rem; font-weight:700; color:#f5f9ff; line-height:1.1; }
.metric-sub { color:#42dfaa; font-size:.82rem; margin-top:9px; }
.section-card { background:rgba(9,27,48,.88); border:1px solid #1b3b5d; border-radius:16px; padding:17px 18px; margin-bottom:16px; }
.section-title { font-family:'Space Grotesk',sans-serif; font-size:1.05rem; font-weight:700; color:#f3f8ff; margin-bottom:4px; }
.section-desc { color:#96afcb; font-size:.82rem; margin-bottom:14px; }
div[data-testid="stTabs"] button { color:#adc4df; font-weight:600; }
div[data-testid="stTabs"] button[aria-selected="true"] { color:#60d8f0; border-bottom-color:#3b9cff; }
.stButton button[kind="primary"] { background:linear-gradient(90deg,#147ff4,#2bafff); border:0; color:white; border-radius:10px; font-weight:700; }
.stButton button { border-radius:10px; border-color:#2b4b6c; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border:1px solid #1b3b5d; border-radius:10px; overflow:hidden; }
[data-baseweb="input"] input, [data-baseweb="select"] > div, [data-baseweb="textarea"] textarea { background:#0b2038; color:#eef6ff; }
[data-testid="stNumberInput"] button { background:#153251; color:#dcecff; }
hr { border-color:#1d3a59; }
.footer { border-top:1px solid #1c3856; margin-top:22px; padding:16px 4px 4px; color:#809ab7; font-size:.78rem; display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; }
.status-pill { display:inline-block; border:1px solid #1b7057; background:rgba(22,144,102,.15); color:#48e0ac; border-radius:99px; padding:4px 10px; font-size:.76rem; font-weight:700; }
.stAlert { border-radius:12px; }
</style>
""", unsafe_allow_html=True)

HOURS = list(range(24))
CONFIG_PATH = Path(__file__).with_name("smarthome_config.json")


def load_configuration():
    """Load a previously saved local configuration, falling back safely to defaults."""
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            appliances = [Appliance(**item) for item in data.get("appliances", [])]
            tariffs = [float(rate) for rate in data.get("tariffs", DEFAULT_TARIFF)]
            if len(tariffs) == 24 and all(a.valid_starts() for a in appliances):
                return appliances or default_appliances(), tariffs
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    return default_appliances(), DEFAULT_TARIFF[:]


def save_configuration():
    """Persist appliance settings and tariffs locally; no cloud account is required."""
    payload = {
        "appliances": [
            {"name": a.name, "power_kw": a.power_kw, "duration": a.duration,
             "earliest": a.earliest, "latest": a.latest, "flexible": a.flexible}
            for a in st.session_state.appliances
        ],
        "tariffs": st.session_state.tariffs,
    }
    CONFIG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if "appliances" not in st.session_state or "tariffs" not in st.session_state:
    _loaded_appliances, _loaded_tariffs = load_configuration()
    if "appliances" not in st.session_state:
        st.session_state.appliances = _loaded_appliances
    if "tariffs" not in st.session_state:
        st.session_state.tariffs = _loaded_tariffs
if "result" not in st.session_state:
    st.session_state.result = None
if "baseline" not in st.session_state:
    st.session_state.baseline = None
if "last_settings" not in st.session_state:
    st.session_state.last_settings = None


def fmt_hour(h: int) -> str:
    return "24:00" if h == 24 else f"{h:02d}:00"


def appliance_frame():
    return pd.DataFrame([{
        "Enabled": True, "Appliance": a.name, "Power (kW)": float(a.power_kw),
        "Duration (h)": int(a.duration), "Earliest start": int(a.earliest),
        "Latest start": int(a.latest), "Flexible": bool(a.flexible)
    } for a in st.session_state.appliances])


def load_from_result(result):
    return result["load"]


def plot_layout(fig, height=300):
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#dbe9fb", family="DM Sans"), margin=dict(l=10,r=10,t=22,b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
    fig.update_xaxes(gridcolor="rgba(95,139,183,.14)", zerolinecolor="rgba(95,139,183,.18)")
    fig.update_yaxes(gridcolor="rgba(95,139,183,.14)", zerolinecolor="rgba(95,139,183,.18)")
    return fig


def metric(label, value, sub, icon):
    st.markdown(f'''<div class="metric-card"><div style="display:flex;justify-content:space-between;align-items:center"><div class="metric-label">{label}</div><div style="font-size:1.3rem">{icon}</div></div><div class="metric-value">{value}</div><div class="metric-sub">{sub}</div></div>''', unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("<div style='font-size:2rem'>🏠</div><div style='font-family:Space Grotesk;font-size:1.2rem;font-weight:700'>SmartHome</div><div style='color:#8ea9c7;font-size:.82rem;margin-bottom:20px'>ENERGY OPTIMIZATION</div>", unsafe_allow_html=True)
    page = st.radio("NAVIGATION", ["Dashboard", "Appliances", "Electricity Tariffs", "Optimization", "Reports", "About Project"], label_visibility="visible")
    st.markdown("<br><br><div style='padding:14px;background:#0d2741;border:1px solid #1d4266;border-radius:13px'><div style='font-size:1.2rem'>🌿</div><b>Save Energy</b><br><span style='color:#91abc7;font-size:.83rem'>Shift flexible loads to lower-cost hours.</span></div>", unsafe_allow_html=True)
    if st.button("💾 Save configuration", use_container_width=True):
        try:
            save_configuration()
            st.success("Appliances and tariffs saved locally.")
        except OSError as exc:
            st.error(f"Could not save configuration: {exc}")
    if st.button("↺ Restore default setup", use_container_width=True):
        st.session_state.appliances = default_appliances()
        st.session_state.tariffs = DEFAULT_TARIFF[:]
        st.session_state.result = None
        st.session_state.baseline = None
        try:
            save_configuration()
            st.success("Default setup restored.")
        except OSError as exc:
            st.error(f"Defaults restored for this session, but not saved: {exc}")
        st.rerun()
    st.markdown("<div style='color:#7895b4;font-size:.75rem;margin-top:22px'>SIMULATION MODE · NO HARDWARE CONNECTED</div>", unsafe_allow_html=True)

# Header
st.markdown("<div class='hero'><div class='hero-kicker'>Smart energy · Smarter schedules</div><h1>Smart Home Energy Optimization</h1><p>Genetic Algorithm based appliance scheduling · Daily simulation and cost analysis</p><div style='margin-top:13px'><span class='status-pill'>● System ready</span></div></div>", unsafe_allow_html=True)

appliances = st.session_state.appliances
tariffs = st.session_state.tariffs
baseline_starts = [a.valid_starts()[0] if a.valid_starts() else 0 for a in appliances]
baseline = evaluate(baseline_starts, appliances, tariffs, 5.0) if appliances else evaluate([], [], tariffs, 5.0)
result = st.session_state.result or baseline
base_cost = baseline["cost"]
current_cost = result["cost"]
savings = base_cost - current_cost
savings_pct = (savings / base_cost * 100) if base_cost else 0

if page == "Dashboard":
    c1,c2,c3,c4 = st.columns(4, gap="medium")
    with c1: metric("Daily energy requirement", f"{result['energy']:.2f} kWh", "Based on appliance power × duration", "⚡")
    with c2: metric("Estimated electricity cost", f"₹{current_cost:.2f}", f"{'Optimized schedule' if st.session_state.result else 'Baseline · run GA to optimize'}", "₹")
    with c3: metric("Peak hourly load", f"{result['peak']:.2f} kW", "Highest simultaneous demand", "◉")
    with c4: metric("Estimated cost difference", f"₹{savings:.2f}", f"{savings_pct:.1f}% vs baseline" if st.session_state.result else "Savings shown after optimization", "🌿")

    left, right = st.columns([1.55, 1], gap="medium")
    with left:
        st.markdown("<div class='section-card'><div class='section-title'>Hourly Energy Load Comparison</div><div class='section-desc'>Compare simultaneous appliance demand before and after optimization.</div>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=HOURS, y=baseline["load"], name="Baseline", mode="lines+markers", line=dict(color="#ffb547",width=2.5), marker=dict(size=4), fill="tozeroy", fillcolor="rgba(255,181,71,.08)"))
        if st.session_state.result:
            fig.add_trace(go.Scatter(x=HOURS, y=result["load"], name="Optimized", mode="lines+markers", line=dict(color="#329cff",width=3), marker=dict(size=4), fill="tozeroy", fillcolor="rgba(50,156,255,.10)"))
        fig.update_xaxes(title="Hour of day", tickmode="linear", dtick=2, range=[0,23])
        fig.update_yaxes(title="Load (kW)")
        st.plotly_chart(plot_layout(fig, 320), use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='section-card'><div class='section-title'>Energy Use by Appliance</div><div class='section-desc'>Estimated daily energy contribution of each device.</div>", unsafe_allow_html=True)
        energy_df = pd.DataFrame({"Appliance":[a.name for a in appliances],"Energy (kWh)":[a.power_kw*a.duration for a in appliances]})
        if not energy_df.empty:
            fig2 = px.pie(energy_df, names="Appliance", values="Energy (kWh)", hole=.62, color_discrete_sequence=["#328cff","#29c8d2","#ffae42","#a56bff","#f16c9a","#36c994"])
            fig2.update_traces(textposition="outside", textinfo="percent", marker=dict(line=dict(color="#0b1e35",width=2)))
            fig2.update_layout(showlegend=True, legend=dict(font=dict(size=10), orientation="v", x=1.0, y=.5))
            st.plotly_chart(plot_layout(fig2, 320), use_container_width=True, config={"displayModeBar":False})
        else: st.info("Add an appliance to view energy breakdown.")
        st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1,1], gap="medium")
    with left:
        st.markdown("<div class='section-card'><div class='section-title'>Appliance Overview</div><div class='section-desc'>Current devices and their configured operating windows.</div>", unsafe_allow_html=True)
        if appliances:
            rows = [{"Appliance":a.name,"Power (kW)":a.power_kw,"Duration (h)":a.duration,"Allowed start":f"{fmt_hour(a.earliest)}–{fmt_hour(a.latest)}","Flexible":"Yes" if a.flexible else "No"} for a in appliances]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else: st.info("Add an appliance from the Appliances page.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='section-card'><div class='section-title'>Quick Actions</div><div class='section-desc'>Manage your home simulation.</div>", unsafe_allow_html=True)
        qa1,qa2 = st.columns(2)
        with qa1:
            if st.button("＋ Add appliance", use_container_width=True): st.session_state.quick_add = True; st.rerun()
        with qa2:
            if st.button("⚙ Edit tariffs", use_container_width=True): st.session_state.jump_tariff = True; st.rerun()
        if st.button("🧬 Open optimization settings", type="primary", use_container_width=True):
            st.session_state.run_requested = True
            st.session_state.page_hint = "Optimization"
            st.info("Choose Optimization from the sidebar to run the Genetic Algorithm.")
        if st.session_state.result:
            st.success(f"Optimization complete. Estimated cost difference: ₹{savings:.2f} ({savings_pct:.1f}%).")
        else:
            st.caption("The charts show your baseline until you run the optimizer.")
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Appliances":
    st.markdown("## Appliance Manager")
    st.markdown("Customize the virtual appliances in your home. Power is measured in kW; 0.75 kW is equivalent to 750 W.")
    with st.expander("＋ Add a new appliance", expanded=bool(st.session_state.pop("quick_add", False))):
        with st.form("add_appliance_form", clear_on_submit=True):
            a1,a2,a3 = st.columns(3)
            with a1: name = st.text_input("Appliance name", placeholder="e.g. Clothes Dryer")
            with a2: power = st.number_input("Power consumption (kW)", min_value=.01, max_value=30.0, value=1.0, step=.1, help="Enter watts divided by 1000.")
            with a3: duration = st.number_input("Operating duration (hours)", min_value=1, max_value=24, value=1, step=1)
            a4,a5,a6 = st.columns(3)
            with a4: earliest = st.number_input("Earliest start hour", min_value=0, max_value=23, value=8, step=1, help="0 = midnight, 13 = 1 PM.")
            with a5: latest = st.number_input("Latest start hour", min_value=0, max_value=23, value=20, step=1)
            with a6: flexible = st.checkbox("Allow GA to shift this appliance", value=True)
            submitted = st.form_submit_button("Add appliance", type="primary", use_container_width=True)
        if submitted:
            candidate = Appliance(name.strip(), float(power), int(duration), int(earliest), int(latest), bool(flexible))
            if not name.strip(): st.error("Please enter an appliance name.")
            elif any(a.name.lower() == name.strip().lower() for a in appliances): st.error("Appliance names must be unique.")
            elif not candidate.valid_starts(): st.error("Invalid window: duration must fit before midnight and earliest start must not exceed latest start.")
            else:
                st.session_state.appliances.append(candidate); st.session_state.result = None; save_configuration(); st.success(f"Added {candidate.name}."); st.rerun()

    st.markdown("### Edit existing appliances")
    st.caption("Edit values directly in the table, then click Save appliance changes. Disable a row to remove it when saving.")
    editor = st.data_editor(appliance_frame(), key="appliance_editor", num_rows="dynamic", hide_index=True, use_container_width=True,
        column_config={"Enabled":st.column_config.CheckboxColumn("Keep", help="Uncheck to remove appliance"),
        "Appliance":st.column_config.TextColumn("Appliance name", required=True),
        "Power (kW)":st.column_config.NumberColumn("Power (kW)", min_value=.01, max_value=30, step=.1, format="%.2f"),
        "Duration (h)":st.column_config.NumberColumn("Duration (h)", min_value=1,max_value=24,step=1),
        "Earliest start":st.column_config.NumberColumn("Earliest start (0–23)", min_value=0,max_value=23,step=1),
        "Latest start":st.column_config.NumberColumn("Latest start (0–23)", min_value=0,max_value=23,step=1),
        "Flexible":st.column_config.CheckboxColumn("Schedule flexible")})
    if st.button("Save appliance changes", type="primary"):
        new_appliances=[]; names=set(); errors=[]
        for _,row in editor.iterrows():
            if not bool(row.get("Enabled", True)): continue
            nm=str(row["Appliance"]).strip()
            if not nm: errors.append("Every appliance needs a name."); continue
            if nm.lower() in names: errors.append(f"Duplicate appliance name: {nm}."); continue
            names.add(nm.lower())
            try:
                a=Appliance(nm,float(row["Power (kW)" ]),int(row["Duration (h)" ]),int(row["Earliest start"]),int(row["Latest start"]),bool(row["Flexible"]))
                if not a.valid_starts(): errors.append(f"Invalid time window for {nm}.")
                else: new_appliances.append(a)
            except (ValueError,TypeError): errors.append(f"Invalid values for {nm}.")
        if errors: st.error(" ".join(errors))
        elif not new_appliances: st.error("Keep at least one valid appliance.")
        else: st.session_state.appliances=new_appliances; st.session_state.result=None; save_configuration(); st.success("Appliance configuration saved. Run optimization again to refresh results."); st.rerun()
    st.markdown("### Appliance energy estimate")
    if appliances:
        st.dataframe(pd.DataFrame([{"Appliance":a.name,"Power (kW)":a.power_kw,"Duration (h)":a.duration,"Energy per day (kWh)":a.power_kw*a.duration,"Earliest start":fmt_hour(a.earliest),"Latest start":fmt_hour(a.latest)} for a in appliances]), hide_index=True, use_container_width=True)

elif page == "Electricity Tariffs":
    st.markdown("## Electricity Tariff Settings")
    st.write("Customize the price of electricity for every hour. Rates are in Indian rupees per kilowatt-hour (₹/kWh). The sample profile is illustrative, not an official utility tariff.")
    if st.button("Restore sample tariff profile"):
        st.session_state.tariffs=DEFAULT_TARIFF[:]; st.session_state.result=None; save_configuration(); st.rerun()
    tariff_df=pd.DataFrame({"Hour":HOURS,"Time":[fmt_hour(h) for h in HOURS],"Rate (₹/kWh)":tariffs})
    edited_tariffs=st.data_editor(tariff_df, hide_index=True, use_container_width=True, key="tariff_editor", height=540,
        column_config={"Hour":st.column_config.NumberColumn("Hour",disabled=True),"Time":st.column_config.TextColumn("Time",disabled=True),"Rate (₹/kWh)":st.column_config.NumberColumn("Rate (₹/kWh)",min_value=0,max_value=100,step=.1,format="₹%.2f")})
    if st.button("Save hourly tariff rates", type="primary"):
        rates=edited_tariffs["Rate (₹/kWh)"].astype(float).tolist()
        if len(rates)!=24 or any(r<0 for r in rates): st.error("Enter 24 non-negative hourly rates.")
        else: st.session_state.tariffs=rates; st.session_state.result=None; save_configuration(); st.success("Tariffs saved. Run optimization again to calculate results using the new rates."); st.rerun()
    tariff_fig=go.Figure(go.Bar(x=HOURS,y=tariffs,marker_color=["#ffb547" if v==max(tariffs) else "#328cff" for v in tariffs],hovertemplate="%{x}:00<br>₹%{y:.2f}/kWh<extra></extra>"))
    tariff_fig.update_xaxes(title="Hour of day",tickmode="linear",dtick=2); tariff_fig.update_yaxes(title="Tariff (₹/kWh)")
    st.plotly_chart(plot_layout(tariff_fig,280),use_container_width=True,config={"displayModeBar":False})

elif page == "Optimization":
    st.markdown("## Genetic Algorithm Controls")
    st.write("The algorithm searches appliance start-time combinations. It minimizes estimated electricity cost and adds a penalty when simultaneous load exceeds your preferred target.")
    left,right=st.columns([1.05,1],gap="large")
    with left:
        st.markdown("<div class='section-card'><div class='section-title'>Algorithm parameters</div><div class='section-desc'>Higher populations and generation counts explore more schedules but take longer.</div>",unsafe_allow_html=True)
        population=st.slider("Population size",min_value=20,max_value=250,value=80,step=10,help="Number of candidate schedules per generation.")
        generations=st.slider("Number of generations",min_value=20,max_value=500,value=150,step=10)
        mutation=st.slider("Mutation probability",min_value=0.01,max_value=0.60,value=0.12,step=0.01,help="Chance that an appliance start hour changes.")
        crossover=st.slider("Crossover probability",min_value=0.0,max_value=1.0,value=0.85,step=0.05)
        max_load=st.slider("Preferred maximum hourly load (kW)",min_value=1.0,max_value=15.0,value=5.0,step=0.5,help="Excess load is penalized, but cannot always be avoided if appliance windows overlap.")
        seed=st.number_input("Random seed (repeatable runs)",min_value=0,max_value=999999,value=42,step=1)
        st.markdown("</div>",unsafe_allow_html=True)
    with right:
        st.markdown("<div class='section-card'><div class='section-title'>Optimization objective</div><div class='section-desc'>How candidate schedules are evaluated.</div><div style='padding:13px;background:#0b2743;border-radius:10px;border:1px solid #1b4266;margin-bottom:10px'><b style='color:#58d8ee'>Fitness = Energy Cost + Load Penalty</b><br><span style='color:#a8c0db;font-size:.85rem'>Lower fitness is better. All appliances must fit inside their allowed time windows.</span></div><ul style='color:#bdd0e7;line-height:1.9'><li>Population initialization</li><li>Tournament selection</li><li>Uniform crossover</li><li>Random mutation</li><li>Elitism to preserve good solutions</li></ul>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
        st.markdown("<div class='section-card'><div class='section-title'>Run readiness</div><div class='section-desc'>Current inputs used for this simulation.</div>",unsafe_allow_html=True)
        st.write(f"**Appliances configured:** {len(appliances)}")
        st.write(f"**Tariff slots:** {len(tariffs)} hourly rates")
        st.write(f"**Daily energy requirement:** {sum(a.power_kw*a.duration for a in appliances):.2f} kWh")
        st.markdown("</div>",unsafe_allow_html=True)
    if st.button("🧬 Run Genetic Algorithm Optimization",type="primary",use_container_width=True):
        invalid=[a.name for a in appliances if not a.valid_starts()]
        if not appliances: st.error("Add at least one appliance before running optimization.")
        elif invalid: st.error("Fix invalid operating windows: "+", ".join(invalid))
        else:
            progress=st.progress(0,text="Preparing candidate schedules…")
            status=st.empty()
            for p in (15,35,60,82,100):
                progress.progress(p,text=f"Searching schedules · {p}%")
            try:
                base_starts=[a.valid_starts()[0] for a in appliances]
                base=evaluate(base_starts,appliances,tariffs,max_load)
                opt=genetic_algorithm(appliances,tariffs,max_load,int(population),int(generations),float(mutation),float(crossover),int(seed))
                st.session_state.baseline=base
                st.session_state.result=opt
                st.session_state.last_settings={"population":population,"generations":generations,"mutation":mutation,"crossover":crossover,"max_load":max_load,"seed":seed}
                progress.progress(100,text="Optimization complete")
                status.success("Best candidate schedule found. Review the results below or open Dashboard.")
                st.rerun()
            except Exception as e: st.error(f"Optimization failed: {e}")
    if st.session_state.result:
        base=st.session_state.baseline or baseline; opt=st.session_state.result
        st.markdown("### Optimization Results")
        r1,r2,r3,r4=st.columns(4)
        with r1: metric("Baseline cost",f"₹{base['cost']:.2f}","Earliest allowed start times","📋")
        with r2: metric("Optimized cost",f"₹{opt['cost']:.2f}","Genetic Algorithm output","🧬")
        with r3: metric("Cost difference",f"₹{base['cost']-opt['cost']:.2f}","Positive means lower cost","💰")
        with r4: metric("Optimized peak",f"{opt['peak']:.2f} kW","Maximum hourly demand","⚡")
        sched=[]
        for a,start in zip(appliances,opt["starts"]): sched.append({"Appliance":a.name,"Power (kW)":a.power_kw,"Duration (h)":a.duration,"Start time":fmt_hour(start),"End time":fmt_hour(start+a.duration),"Energy (kWh)":a.power_kw*a.duration})
        st.dataframe(pd.DataFrame(sched),hide_index=True,use_container_width=True)
        if opt.get("load_limit_met", True):
            st.success(f"Hourly load stayed within the configured {opt.get('max_load', 5.0):.2f} kW target.")
        else:
            st.warning(f"The configured load target was exceeded in {opt.get('overload_hours', 0)} hour(s). The target may be infeasible with these appliance windows.")
        hist=opt.get("history",[])
        if hist:
            fig=go.Figure(go.Scatter(x=list(range(1,len(hist)+1)),y=hist,mode="lines",line=dict(color="#38d5a1",width=3),fill="tozeroy",fillcolor="rgba(56,213,161,.10)"))
            fig.update_xaxes(title="Generation");fig.update_yaxes(title="Best fitness (lower is better)")
            st.plotly_chart(plot_layout(fig,260),use_container_width=True,config={"displayModeBar":False})

elif page == "Reports":
    st.markdown("## Reports & Schedule Analysis")
    if st.session_state.result is None:
        st.info("Run the Genetic Algorithm from Optimization to generate a report. You can still inspect your baseline schedule below.")
    base=st.session_state.baseline or baseline
    opt=st.session_state.result or baseline
    try:
        greedy = greedy_schedule(appliances, tariffs, float((st.session_state.last_settings or {}).get("max_load", 5.0))) if appliances else baseline
    except ValueError:
        greedy = baseline
    cost_df=pd.DataFrame({"Schedule":["Baseline","Greedy benchmark","Genetic Algorithm"],"Estimated cost (₹)":[base["cost"],greedy["cost"],opt["cost"]],"Peak load (kW)":[base["peak"],greedy["peak"],opt["peak"]],"Energy (kWh)":[base["energy"],greedy["energy"],opt["energy"]]})
    fig=go.Figure()
    fig.add_trace(go.Bar(x=cost_df["Schedule"],y=cost_df["Estimated cost (₹)"],name="Daily cost",marker_color=["#ffb547","#a56bff","#329cff"],text=[f"₹{v:.2f}" for v in cost_df["Estimated cost (₹)" ]],textposition="outside"))
    fig.update_yaxes(title="Estimated cost (₹)")
    st.plotly_chart(plot_layout(fig,280),use_container_width=True,config={"displayModeBar":False})
    hourly=pd.DataFrame({"Hour":HOURS,"Time":[fmt_hour(h) for h in HOURS],"Tariff (₹/kWh)":tariffs,"Baseline load (kW)":base["load"],"Optimized load (kW)":opt["load"],"Optimized hourly cost (₹)":opt["hourly_cost"]})
    st.caption("The greedy benchmark is a simple tariff-aware heuristic; the Genetic Algorithm is compared against both it and the earliest-start baseline.")
    st.markdown("### Hourly report")
    st.dataframe(hourly,hide_index=True,use_container_width=True)
    appliance_report=pd.DataFrame([{"Appliance":a.name,"Power (kW)":a.power_kw,"Duration (h)":a.duration,"Scheduled start":fmt_hour(opt["starts"][i]),"Scheduled end":fmt_hour(opt["starts"][i]+a.duration),"Energy (kWh)":a.power_kw*a.duration} for i,a in enumerate(appliances)])
    c1,c2=st.columns(2)
    with c1: st.download_button("⬇ Download hourly report CSV",hourly.to_csv(index=False).encode("utf-8"),"hourly_energy_report.csv","text/csv",use_container_width=True)
    with c2: st.download_button("⬇ Download appliance schedule CSV",appliance_report.to_csv(index=False).encode("utf-8"),"optimized_appliance_schedule.csv","text/csv",use_container_width=True)
    st.download_button("⬇ Download summary CSV",cost_df.to_csv(index=False).encode("utf-8"),"optimization_summary.csv","text/csv",use_container_width=True)

elif page == "About Project":
    st.markdown("## About the Project")
    st.markdown("""This project demonstrates a **Genetic Algorithm (GA)** for scheduling flexible household appliances to reduce estimated electricity cost while discouraging excessive simultaneous power demand.

**Chromosome representation:** one gene per appliance; the gene stores that appliance's start hour.

**Fitness function:** estimated electricity cost plus an overload penalty when total hourly load exceeds the configured target.

**Genetic operators:** tournament selection, uniform crossover, mutation, and elitism.

**Assumptions:** appliances run continuously for their specified whole-hour duration; each schedule must respect its allowed start window. Electricity tariffs are user-editable sample values. This is a simulation and does not connect to real smart meters or control hardware.""")
    st.markdown("### Energy calculation")
    st.latex(r"E_i = P_i \times D_i")
    st.markdown("where power is measured in kW and duration in hours, producing energy in kWh.")
    st.markdown("### Cost calculation")
    st.latex(r"C = \sum_{h=0}^{23} L_h \times T_h")
    st.markdown("where \(L_h\) is total load during hour h and \(T_h\) is the electricity tariff for that hour.")

st.markdown("<div class='footer'><span>© SmartHome Energy Optimization · Genetic Algorithm scheduling simulation</span><span>Python · Streamlit · Plotly &nbsp; | &nbsp; Educational project · No hardware connected</span></div>",unsafe_allow_html=True)
