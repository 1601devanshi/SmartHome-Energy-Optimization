from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from main import Appliance, DEFAULT_TARIFF, default_appliances, evaluate, genetic_algorithm, greedy_schedule

st.set_page_config(page_title="SmartHome Energy Optimization", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")

# ---------- Theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --bg:#071426; --panel:#0b1e35; --panel2:#102844; --line:#1e3b5e; --muted:#9db4d0; --text:#edf5ff; --blue:#3b9cff; --cyan:#39d4df; --green:#27d79a; --orange:#ffb547; }
.stApp { background:radial-gradient(ellipse at 75% 0%, #102c4b 0%, #071426 45%, #06111f 100%); color:var(--text); font-family:'DM Sans',sans-serif; }
[data-testid="stHeader"] { background:rgba(7,20,38,.82); }
[data-testid="stSidebar"] { background:#08182b; border-right:1px solid #1b3552; }
[data-testid="stSidebar"] * { color:var(--text); }
.block-container { padding-top:1.35rem; padding-bottom:1rem; max-width:1600px; }
h1,h2,h3,h4 { font-family:'Space Grotesk',sans-serif !important; color:#f4f8ff !important; }
p,label,.stMarkdown { color:#dbe9fb; }
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
.stButton button[kind="primary"] { background:linear-gradient(90deg,#147ff4,#2bafff); border:0; color:white; border-radius:10px; font-weight:700; }
.stButton button { border-radius:10px; border-color:#2b4b6c; }
[data-testid="stDataFrame"],[data-testid="stDataEditor"] { border:1px solid #1b3b5d; border-radius:10px; overflow:hidden; }
[data-baseweb="input"] input,[data-baseweb="select"] > div,[data-baseweb="textarea"] textarea { background:#0b2038; color:#eef6ff; }
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
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            appliances = [Appliance(**item) for item in data.get("appliances", [])]
            tariffs = [float(rate) for rate in data.get("tariffs", DEFAULT_TARIFF)]
            solar_settings = data.get("solar", {})
            if len(tariffs) == 24 and all(a.valid_starts() for a in appliances):
                return (appliances or default_appliances(), tariffs,
                        float(solar_settings.get("capacity_kw", 4.0)),
                        float(solar_settings.get("generation_factor", 0.8)),
                        bool(solar_settings.get("enabled", True)))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    return default_appliances(), DEFAULT_TARIFF[:], 4.0, 0.8, True


if "appliances" not in st.session_state:
    loaded = load_configuration()
    st.session_state.appliances, st.session_state.tariffs = loaded[0], loaded[1]
    st.session_state.solar_capacity = loaded[2]
    st.session_state.solar_factor = loaded[3]
    st.session_state.solar_enabled = loaded[4]
if "tariffs" not in st.session_state:
    st.session_state.tariffs = DEFAULT_TARIFF[:]
for key, value in {"result": None, "baseline": None, "last_settings": None, "appliance_editor_version": 0}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def save_configuration():
    payload = {
        "appliances": [{"name": a.name, "power_kw": a.power_kw, "duration": a.duration,
                        "earliest": a.earliest, "latest": a.latest, "flexible": a.flexible}
                       for a in st.session_state.appliances],
        "tariffs": st.session_state.tariffs,
        "solar": {"capacity_kw": st.session_state.solar_capacity,
                  "generation_factor": st.session_state.solar_factor,
                  "enabled": st.session_state.solar_enabled},
    }
    CONFIG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def fmt_hour(h: int) -> str:
    return "24:00" if h == 24 else f"{h:02d}:00"


def make_solar_profile(capacity_kw: float, generation_factor: float, enabled: bool = True) -> list[float]:
    """Create a transparent illustrative 24-hour solar profile (no weather data/API)."""
    if not enabled:
        return [0.0] * 24
    peak = max(0.0, float(capacity_kw) * float(generation_factor))
    profile = []
    for hour in HOURS:
        # Smooth daylight-only curve: generation rises after 06:00 and falls by 18:00.
        daylight_position = (hour - 6) / 12
        value = peak * math.sin(math.pi * daylight_position) if 0 < daylight_position < 1 else 0.0
        profile.append(round(max(0.0, value), 3))
    return profile


def appliance_frame():
    return pd.DataFrame([{"Enabled": True, "Appliance": a.name, "Power (kW)": float(a.power_kw),
                          "Duration (h)": int(a.duration), "Earliest start": int(a.earliest),
                          "Latest start": int(a.latest), "Flexible": bool(a.flexible)}
                         for a in st.session_state.appliances])


def plot_layout(fig, height=300):
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#dbe9fb", family="DM Sans"), margin=dict(l=10, r=10, t=22, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
    fig.update_xaxes(gridcolor="rgba(95,139,183,.14)", zerolinecolor="rgba(95,139,183,.18)")
    fig.update_yaxes(gridcolor="rgba(95,139,183,.14)", zerolinecolor="rgba(95,139,183,.18)")
    return fig


def metric(label, value, sub, icon):
    st.markdown(f'''<div class="metric-card"><div style="display:flex;justify-content:space-between;align-items:center"><div class="metric-label">{label}</div><div style="font-size:1.3rem">{icon}</div></div><div class="metric-value">{value}</div><div class="metric-sub">{sub}</div></div>''', unsafe_allow_html=True)


def clear_results():
    st.session_state.result = None
    st.session_state.baseline = None
    st.session_state.last_settings = None


def go_to_page(target: str):
    """Navigate from dashboard quick-action buttons via the sidebar radio state."""
    st.session_state["navigation_page"] = target


# Sidebar navigation
with st.sidebar:
    st.markdown("<div style='font-size:2rem'>🏠</div><div style='font-family:Space Grotesk;font-size:1.2rem;font-weight:700'>SmartHome</div><div style='color:#8ea9c7;font-size:.82rem;margin-bottom:20px'>ENERGY OPTIMIZATION</div>", unsafe_allow_html=True)
    page = st.radio("NAVIGATION", ["Dashboard", "Appliances", "Electricity Tariffs", "Solar Energy", "Optimization", "Reports", "About Project"], key="navigation_page")
    st.markdown("<br><br><div style='padding:14px;background:#0d2741;border:1px solid #1d4266;border-radius:13px'><div style='font-size:1.2rem'>🌿</div><b>Optimize Energy</b><br><span style='color:#91abc7;font-size:.83rem'>Schedule flexible loads around tariffs and simulated solar generation.</span></div>", unsafe_allow_html=True)
    if st.button("💾 Save configuration", use_container_width=True):
        try:
            save_configuration(); st.success("Configuration saved locally.")
        except OSError as exc:
            st.error(f"Could not save configuration: {exc}")
    if st.button("↺ Restore default setup", use_container_width=True):
        st.session_state.appliances = default_appliances()
        st.session_state.tariffs = DEFAULT_TARIFF[:]
        st.session_state.solar_capacity = 4.0
        st.session_state.solar_factor = 0.8
        st.session_state.solar_enabled = True
        clear_results()
        try:
            save_configuration(); st.success("Default setup restored.")
        except OSError as exc:
            st.warning(f"Defaults restored for this session, but not saved: {exc}")
        st.rerun()
    st.markdown("<div style='color:#7895b4;font-size:.75rem;margin-top:22px'>SIMULATION MODE · NO HARDWARE CONNECTED</div>", unsafe_allow_html=True)

st.markdown("<div class='hero'><div class='hero-kicker'>Smart energy · Smarter schedules</div><h1>Smart Home Energy Optimization</h1><p>Genetic Algorithm based appliance scheduling · Solar-aware daily simulation and cost analysis</p><div style='margin-top:13px'><span class='status-pill'>● Simulation ready</span></div></div>", unsafe_allow_html=True)

appliances = st.session_state.appliances
tariffs = st.session_state.tariffs
solar_profile = make_solar_profile(st.session_state.solar_capacity, st.session_state.solar_factor, st.session_state.solar_enabled)
solar_for_eval = solar_profile if st.session_state.solar_enabled else [0.0] * 24
baseline_starts = [a.valid_starts()[0] if a.valid_starts() else 0 for a in appliances]
if appliances:
    current_baseline = evaluate(baseline_starts, appliances, tariffs, 5.0, solar_generation=solar_for_eval)
else:
    current_baseline = evaluate([], [], tariffs, 5.0, solar_generation=solar_for_eval)
baseline = st.session_state.baseline if st.session_state.result is not None and st.session_state.baseline else current_baseline
result = st.session_state.result or current_baseline
base_cost = baseline["cost"]
current_cost = result["cost"]
savings = base_cost - current_cost
savings_pct = savings / base_cost * 100 if base_cost else 0.0

if page == "Dashboard":
    st.markdown("### Quick actions")
    qa1, qa2, qa3 = st.columns([1, 1, 1.4], gap="medium")
    with qa1:
        st.button("＋ Add appliance", key="dashboard_add_appliance", type="primary", use_container_width=True,
                  on_click=go_to_page, args=("Appliances",))
    with qa2:
        st.button("✎ Edit tariffs", key="dashboard_edit_tariffs", use_container_width=True,
                  on_click=go_to_page, args=("Electricity Tariffs",))
    with qa3:
        st.button("☀ Solar settings", key="dashboard_solar_settings", use_container_width=True,
                  on_click=go_to_page, args=("Solar Energy",))

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1: metric("Daily appliance demand", f"{result['energy']:.2f} kWh", "Power × operating duration", "⚡")
    with c2: metric("Estimated grid bill", f"₹{current_cost:.2f}", "After direct solar use" if st.session_state.solar_enabled else "Solar disabled", "₹")
    with c3: metric("Peak appliance load", f"{result['peak']:.2f} kW", "Highest simultaneous demand", "◉")
    with c4: metric("Solar used directly", f"{result['solar_used_kwh']:.2f} kWh", f"{result['solar_utilization_pct']:.1f}% of generated solar used", "☀️")

    left, right = st.columns([1.55, 1], gap="medium")
    with left:
        st.markdown("<div class='section-card'><div class='section-title'>Hourly Appliance Load</div><div class='section-desc'>Baseline and optimized simultaneous appliance demand.</div>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=HOURS, y=current_baseline["load"], name="Baseline", mode="lines+markers", line=dict(color="#ffb547", width=2.5), marker=dict(size=4)))
        if st.session_state.result:
            fig.add_trace(go.Scatter(x=HOURS, y=result["load"], name="GA optimized", mode="lines+markers", line=dict(color="#329cff", width=3), marker=dict(size=4)))
        fig.update_xaxes(title="Hour of day", tickmode="linear", dtick=2, range=[0, 23]); fig.update_yaxes(title="Appliance load (kW)")
        st.plotly_chart(plot_layout(fig, 320), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='section-card'><div class='section-title'>Appliance Energy Use</div><div class='section-desc'>Daily energy contribution of each device.</div>", unsafe_allow_html=True)
        energy_df = pd.DataFrame({"Appliance": [a.name for a in appliances], "Energy (kWh)": [a.power_kw * a.duration for a in appliances]})
        if not energy_df.empty:
            fig2 = px.pie(energy_df, names="Appliance", values="Energy (kWh)", hole=.62, color_discrete_sequence=["#328cff", "#29c8d2", "#ffae42", "#a56bff", "#f16c9a", "#36c994"])
            fig2.update_traces(textposition="outside", textinfo="percent", marker=dict(line=dict(color="#0b1e35", width=2)))
            st.plotly_chart(plot_layout(fig2, 320), use_container_width=True, config={"displayModeBar": False})
        else: st.info("Add an appliance to view energy breakdown.")
        st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown("<div class='section-card'><div class='section-title'>Appliance Overview</div><div class='section-desc'>Current operating windows.</div>", unsafe_allow_html=True)
        if appliances:
            st.dataframe(pd.DataFrame([{"Appliance": a.name, "Power (kW)": a.power_kw, "Duration (h)": a.duration, "Allowed start": f"{fmt_hour(a.earliest)}–{fmt_hour(a.latest)}", "Flexible": "Yes" if a.flexible else "No"} for a in appliances]), hide_index=True, use_container_width=True)
        else: st.info("Add an appliance from the Appliances page.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='section-card'><div class='section-title'>Energy Summary</div><div class='section-desc'>Current simulation assumptions.</div>", unsafe_allow_html=True)
        st.write(f"**Solar generation:** {result['solar_generated_kwh']:.2f} kWh/day")
        st.write(f"**Grid import:** {result['grid_import_kwh']:.2f} kWh/day")
        st.write(f"**Estimated grid bill:** ₹{result['cost']:.2f}")
        if st.session_state.result: st.success(f"GA run complete. Cost difference from earliest-start baseline: ₹{savings:.2f} ({savings_pct:.1f}%).")
        else: st.caption("Run the GA from Optimization to create an optimized schedule.")
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Appliances":
    st.markdown("## Appliance Manager")
    st.write("Manage virtual appliances, power ratings, operating duration and allowed start windows.")
    with st.expander("＋ Add a new appliance"):
        with st.form("add_appliance_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1: name = st.text_input("Appliance name", placeholder="e.g. Clothes Dryer")
            with c2: power = st.number_input("Power consumption (kW)", min_value=.01, max_value=30.0, value=1.0, step=.1)
            with c3: duration = st.number_input("Operating duration (hours)", min_value=1, max_value=24, value=1, step=1)
            c4, c5, c6 = st.columns(3)
            with c4: earliest = st.number_input("Earliest start hour", min_value=0, max_value=23, value=8, step=1)
            with c5: latest = st.number_input("Latest start hour", min_value=0, max_value=23, value=20, step=1)
            with c6: flexible = st.checkbox("Allow GA to shift this appliance", value=True)
            submitted = st.form_submit_button("Add appliance", type="primary", use_container_width=True)
        if submitted:
            candidate = Appliance(name.strip(), float(power), int(duration), int(earliest), int(latest), bool(flexible))
            if not name.strip(): st.error("Please enter an appliance name.")
            elif any(a.name.lower() == name.strip().lower() for a in appliances): st.error("Appliance names must be unique.")
            elif not candidate.valid_starts(): st.error("Invalid window: duration must fit before midnight and earliest must not exceed latest.")
            else:
                st.session_state.appliances.append(candidate); st.session_state.appliance_editor_version += 1; clear_results()
                try: save_configuration()
                except OSError: pass
                st.success(f"Added {candidate.name}."); st.rerun()
    st.markdown("### Edit existing appliances")
    st.caption("Edit the table and click Save appliance changes. Uncheck Keep to remove a row.")
    editor = st.data_editor(appliance_frame(), key=f"appliance_editor_{st.session_state.appliance_editor_version}", num_rows="dynamic", hide_index=True, use_container_width=True,
        column_config={"Enabled": st.column_config.CheckboxColumn("Keep"), "Appliance": st.column_config.TextColumn("Appliance name", required=True),
        "Power (kW)": st.column_config.NumberColumn("Power (kW)", min_value=.01, max_value=30, step=.1, format="%.2f"),
        "Duration (h)": st.column_config.NumberColumn("Duration (h)", min_value=1, max_value=24, step=1),
        "Earliest start": st.column_config.NumberColumn("Earliest start", min_value=0, max_value=23, step=1),
        "Latest start": st.column_config.NumberColumn("Latest start", min_value=0, max_value=23, step=1),
        "Flexible": st.column_config.CheckboxColumn("Schedule flexible")})
    if st.button("Save appliance changes", type="primary"):
        new_appliances, names, errors = [], set(), []
        for _, row in editor.iterrows():
            if not bool(row.get("Enabled", True)): continue
            nm = str(row.get("Appliance", "")).strip()
            try:
                if not nm: raise ValueError("Every appliance needs a name.")
                if nm.lower() in names: raise ValueError(f"Duplicate appliance name: {nm}.")
                a = Appliance(nm, float(row["Power (kW)"]), int(row["Duration (h)"]), int(row["Earliest start"]), int(row["Latest start"]), bool(row["Flexible"]))
                if not a.valid_starts(): raise ValueError(f"Invalid time window for {nm}.")
                names.add(nm.lower()); new_appliances.append(a)
            except (ValueError, TypeError, KeyError) as exc: errors.append(str(exc) or f"Invalid values for {nm}.")
        if errors: st.error(" ".join(errors))
        elif not new_appliances: st.error("Keep at least one valid appliance.")
        else:
            st.session_state.appliances = new_appliances; st.session_state.appliance_editor_version += 1; clear_results()
            try: save_configuration()
            except OSError: pass
            st.success("Appliance configuration saved."); st.rerun()
    st.markdown("### Daily energy estimate")
    st.dataframe(pd.DataFrame([{"Appliance": a.name, "Power (kW)": a.power_kw, "Duration (h)": a.duration, "Energy per day (kWh)": a.power_kw * a.duration, "Earliest start": fmt_hour(a.earliest), "Latest start": fmt_hour(a.latest)} for a in appliances]), hide_index=True, use_container_width=True)

elif page == "Electricity Tariffs":
    st.markdown("## Electricity Tariff Settings")
    st.write("Customize the price of electricity for every hour. The sample values are illustrative, not an official utility tariff.")
    if st.button("Restore sample tariff profile"):
        st.session_state.tariffs = DEFAULT_TARIFF[:]; clear_results()
        try: save_configuration()
        except OSError: pass
        st.rerun()
    tariff_df = pd.DataFrame({"Hour": HOURS, "Time": [fmt_hour(h) for h in HOURS], "Rate (₹/kWh)": tariffs})
    edited_tariffs = st.data_editor(tariff_df, hide_index=True, use_container_width=True, key="tariff_editor", height=540,
        column_config={"Hour": st.column_config.NumberColumn("Hour", disabled=True), "Time": st.column_config.TextColumn("Time", disabled=True),
        "Rate (₹/kWh)": st.column_config.NumberColumn("Rate (₹/kWh)", min_value=0, max_value=100, step=.1, format="₹%.2f")})
    if st.button("Save hourly tariff rates", type="primary"):
        try: rates = edited_tariffs["Rate (₹/kWh)"].astype(float).tolist()
        except (ValueError, TypeError): rates = []
        if len(rates) != 24 or any(r < 0 for r in rates): st.error("Enter 24 non-negative hourly rates.")
        else:
            st.session_state.tariffs = rates; clear_results()
            try: save_configuration()
            except OSError: pass
            st.success("Tariffs saved. Run optimization again."); st.rerun()
    tariff_fig = go.Figure(go.Bar(x=HOURS, y=tariffs, marker_color=["#ffb547" if v == max(tariffs) else "#328cff" for v in tariffs], hovertemplate="%{x}:00<br>₹%{y:.2f}/kWh<extra></extra>"))
    tariff_fig.update_xaxes(title="Hour of day", tickmode="linear", dtick=2); tariff_fig.update_yaxes(title="Tariff (₹/kWh)")
    st.plotly_chart(plot_layout(tariff_fig, 280), use_container_width=True, config={"displayModeBar": False})

elif page == "Solar Energy":
    st.markdown("## Solar Energy Settings")
    st.write("Solar generation is simulated using a simple daylight curve. It is not a weather forecast and does not use real solar sensor data.")
    with st.form("solar_settings_form"):
        enabled = st.checkbox("Enable solar generation in optimization", value=st.session_state.solar_enabled)
        capacity = st.slider("Installed solar capacity (kW)", min_value=0.5, max_value=15.0, value=float(st.session_state.solar_capacity), step=0.5, help="Illustrative peak capacity for the simulation.")
        factor = st.slider("Generation factor", min_value=0.2, max_value=1.0, value=float(st.session_state.solar_factor), step=0.05, help="Scales the simulated peak output to represent different conditions.")
        applied = st.form_submit_button("Apply solar settings", type="primary", use_container_width=True)
    if applied:
        st.session_state.solar_enabled = bool(enabled)
        st.session_state.solar_capacity = float(capacity)
        st.session_state.solar_factor = float(factor)
        clear_results()
        try: save_configuration()
        except OSError: st.warning("Settings applied for this session but could not be saved to the local configuration file.")
        st.success("Solar settings applied. Run GA again to evaluate the updated profile."); st.rerun()
    solar_profile = make_solar_profile(st.session_state.solar_capacity, st.session_state.solar_factor, st.session_state.solar_enabled)
    generated = sum(solar_profile)
    m1, m2, m3 = st.columns(3)
    with m1: metric("Solar status", "Enabled" if st.session_state.solar_enabled else "Disabled", "Simulation setting", "☀️")
    with m2: metric("Peak simulated output", f"{max(solar_profile):.2f} kW", "Approximate midday peak", "⚡")
    with m3: metric("Daily simulated generation", f"{generated:.2f} kWh", "Sum of hourly profile values", "🌞")
    solar_fig = go.Figure()
    solar_fig.add_trace(go.Bar(x=HOURS, y=solar_profile, name="Solar generation", marker_color="#ffb547"))
    solar_fig.update_xaxes(title="Hour of day", tickmode="linear", dtick=2); solar_fig.update_yaxes(title="Simulated solar output (kW)")
    st.plotly_chart(plot_layout(solar_fig, 330), use_container_width=True, config={"displayModeBar": False})
    st.info("Solar is used directly against appliance demand first. This version does not model batteries, grid export, export credits, panel losses beyond the generation factor, or real weather conditions.")
    st.markdown("### Hourly solar profile")
    st.dataframe(pd.DataFrame({"Hour": HOURS, "Time": [fmt_hour(h) for h in HOURS], "Simulated solar output (kW)": solar_profile}), hide_index=True, use_container_width=True)

elif page == "Optimization":
    st.markdown("## Genetic Algorithm Controls")
    st.write("The GA searches appliance start-time combinations. It minimizes grid electricity cost after direct solar use and adds a penalty when appliance demand exceeds the configured load target.")
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown("<div class='section-card'><div class='section-title'>Algorithm parameters</div><div class='section-desc'>Adjust parameters to explore the search behaviour.</div>", unsafe_allow_html=True)
        population = st.slider("Population size", min_value=20, max_value=250, value=80, step=10, help="Number of candidate schedules per generation.")
        generations = st.slider("Number of generations", min_value=20, max_value=500, value=150, step=10)
        mutation = st.slider("Mutation probability", min_value=0.01, max_value=0.60, value=0.12, step=0.01)
        crossover = st.slider("Crossover probability", min_value=0.0, max_value=1.0, value=0.85, step=0.05)
        max_load = st.slider("Preferred maximum appliance load (kW)", min_value=1.0, max_value=15.0, value=5.0, step=0.5, help="Excess appliance demand is penalized, not always prevented.")
        overload_penalty = st.slider("Overload penalty weight", min_value=1.0, max_value=100.0, value=25.0, step=1.0, help="Higher values make overload violations more costly to the fitness function.")
        seed = st.number_input("Random seed", min_value=0, max_value=999999, value=42, step=1, help="Same inputs and seed should produce repeatable results.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='section-card'><div class='section-title'>Fitness function</div><div class='section-desc'>How candidate schedules are scored.</div><div style='padding:13px;background:#0b2743;border-radius:10px;border:1px solid #1b4266;margin-bottom:10px'><b style='color:#58d8ee'>Fitness = Grid Cost + Overload Penalty</b><br><span style='color:#a8c0db;font-size:.85rem'>Lower fitness is better. Solar lowers grid import; the load penalty uses total appliance demand.</span></div><ul style='color:#bdd0e7;line-height:1.9'><li>Random valid population</li><li>Tournament selection (3 contestants)</li><li>Uniform crossover</li><li>Random valid-gene mutation</li><li>Elitism preserves top candidates</li></ul>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-card'><div class='section-title'>Run readiness</div><div class='section-desc'>Current simulation inputs.</div>", unsafe_allow_html=True)
        st.write(f"**Appliances:** {len(appliances)}")
        st.write(f"**Tariff slots:** {len(tariffs)} hourly rates")
        st.write(f"**Daily demand:** {sum(a.power_kw * a.duration for a in appliances):.2f} kWh")
        st.write(f"**Solar:** {'Enabled' if st.session_state.solar_enabled else 'Disabled'} · {sum(solar_for_eval):.2f} kWh/day")
        st.markdown("</div>", unsafe_allow_html=True)
    if st.button("🧬 Run Genetic Algorithm Optimization", type="primary", use_container_width=True):
        invalid = [a.name for a in appliances if not a.valid_starts()]
        if not appliances: st.error("Add at least one appliance before running optimization.")
        elif invalid: st.error("Fix invalid operating windows: " + ", ".join(invalid))
        else:
            try:
                with st.spinner("Evaluating candidate schedules and evolving the population..."):
                    base_starts = [a.valid_starts()[0] for a in appliances]
                    base = evaluate(base_starts, appliances, tariffs, max_load, overload_penalty, solar_for_eval)
                    opt = genetic_algorithm(appliances, tariffs, max_load, int(population), int(generations), float(mutation), float(crossover), int(seed), solar_for_eval, float(overload_penalty))
                    st.session_state.baseline = base
                    st.session_state.result = opt
                    st.session_state.last_settings = {"population": population, "generations": generations, "mutation": mutation, "crossover": crossover, "max_load": max_load, "overload_penalty": overload_penalty, "seed": seed}
                st.success("Optimization complete. Results below are calculated by the GA.")
            except Exception as exc:
                st.error(f"Optimization failed: {exc}")
    if st.session_state.result:
        base = st.session_state.baseline or current_baseline
        opt = st.session_state.result
        st.markdown("### Optimization Results")
        r1, r2, r3, r4 = st.columns(4)
        with r1: metric("Baseline grid cost", f"₹{base['cost']:.2f}", "Earliest valid starts", "📋")
        with r2: metric("GA grid cost", f"₹{opt['cost']:.2f}", "After direct solar use", "🧬")
        with r3: metric("Cost difference", f"₹{base['cost'] - opt['cost']:.2f}", "Positive means lower bill", "💰")
        with r4: metric("Peak appliance load", f"{opt['peak']:.2f} kW", "Before solar offset", "⚡")
        sched = [{"Appliance": a.name, "Power (kW)": a.power_kw, "Duration (h)": a.duration, "Start time": fmt_hour(start), "End time": fmt_hour(start + a.duration), "Energy (kWh)": a.power_kw * a.duration} for a, start in zip(appliances, opt["starts"])]
        st.dataframe(pd.DataFrame(sched), hide_index=True, use_container_width=True)
        if opt["load_limit_met"]: st.success(f"Appliance load stayed within the {opt['max_load']:.2f} kW target.")
        else: st.warning(f"The load target was exceeded in {opt['overload_hours']} hour(s). This target may be infeasible for the configured appliance windows.")
        st.write(f"**Solar generated:** {opt['solar_generated_kwh']:.2f} kWh · **Solar used:** {opt['solar_used_kwh']:.2f} kWh · **Grid import:** {opt['grid_import_kwh']:.2f} kWh")
        hist = opt.get("history", [])
        if hist:
            conv = go.Figure()
            conv.add_trace(go.Scatter(x=list(range(1, len(hist) + 1)), y=hist, mode="lines", name="Best-so-far fitness", line=dict(color="#38d5a1", width=3)))
            avg_hist = opt.get("average_history", [])
            if avg_hist: conv.add_trace(go.Scatter(x=list(range(1, len(avg_hist) + 1)), y=avg_hist, mode="lines", name="Average population fitness", line=dict(color="#329cff", width=2, dash="dot")))
            conv.update_xaxes(title="Generation"); conv.update_yaxes(title="Fitness (lower is better)")
            st.markdown("### GA Convergence")
            st.caption("Best-so-far fitness should not increase because elitism and best-so-far tracking preserve the strongest solution found.")
            st.plotly_chart(plot_layout(conv, 300), use_container_width=True, config={"displayModeBar": False})
        with st.expander("View hourly grid and solar calculation"):
            st.dataframe(pd.DataFrame({"Time": [fmt_hour(h) for h in HOURS], "Appliance load (kW)": opt["load"], "Solar generation (kW)": opt["solar_generation"], "Solar used (kW)": opt["solar_used"], "Grid import (kW)": opt["grid_import"], "Tariff (₹/kWh)": tariffs, "Grid cost (₹)": opt["hourly_cost"]}), hide_index=True, use_container_width=True)

elif page == "Reports":
    st.markdown("## Reports & Schedule Analysis")
    if st.session_state.result is None:
        st.info("Run the Genetic Algorithm from Optimization to generate a report. The baseline and greedy benchmark are still available below.")
    base = st.session_state.baseline or current_baseline
    opt = st.session_state.result or current_baseline
    settings = st.session_state.last_settings or {}
    report_max_load = float(settings.get("max_load", 5.0))
    report_penalty = float(settings.get("overload_penalty", 25.0))
    try:
        greedy = greedy_schedule(appliances, tariffs, report_max_load, solar_for_eval, report_penalty) if appliances else current_baseline
    except ValueError:
        greedy = current_baseline
    no_solar = [0.0] * 24
    base_no_solar = evaluate(base["starts"], appliances, tariffs, report_max_load, report_penalty, no_solar)
    greedy_no_solar = evaluate(greedy["starts"], appliances, tariffs, report_max_load, report_penalty, no_solar)
    opt_no_solar = evaluate(opt["starts"], appliances, tariffs, report_max_load, report_penalty, no_solar)
    solar_cost_reduction = [base_no_solar["cost"] - base["cost"], greedy_no_solar["cost"] - greedy["cost"], opt_no_solar["cost"] - opt["cost"]]
    cost_df = pd.DataFrame({"Schedule": ["Baseline", "Load-aware greedy", "Genetic Algorithm"],
        "Grid cost with current solar (₹)": [base["cost"], greedy["cost"], opt["cost"]],
        "Grid cost without solar (₹)": [base_no_solar["cost"], greedy_no_solar["cost"], opt_no_solar["cost"]],
        "Solar bill reduction (₹)": solar_cost_reduction,
        "Peak appliance load (kW)": [base["peak"], greedy["peak"], opt["peak"]],
        "Energy demand (kWh)": [base["energy"], greedy["energy"], opt["energy"]],
        "Grid import (kWh)": [base["grid_import_kwh"], greedy["grid_import_kwh"], opt["grid_import_kwh"]],
        "Solar used (kWh)": [base["solar_used_kwh"], greedy["solar_used_kwh"], opt["solar_used_kwh"]]})
    fig = go.Figure(go.Bar(x=cost_df["Schedule"], y=cost_df["Grid cost with current solar (₹)"], marker_color=["#ffb547", "#a56bff", "#329cff"], text=[f"₹{v:.2f}" for v in cost_df["Grid cost with current solar (₹)" ]], textposition="outside"))
    fig.update_yaxes(title="Estimated grid cost (₹)")
    st.plotly_chart(plot_layout(fig, 300), use_container_width=True, config={"displayModeBar": False})
    st.markdown("### Comparison table")
    st.dataframe(cost_df, hide_index=True, use_container_width=True)
    st.caption("All schedules use the same appliance definitions, tariffs and solar profile. The baseline uses each appliance's earliest valid start; greedy is a load-aware heuristic; GA is the evolutionary search.")
    st.markdown("### Hourly report")
    hourly = pd.DataFrame({"Hour": HOURS, "Time": [fmt_hour(h) for h in HOURS], "Tariff (₹/kWh)": tariffs,
        "Appliance load (kW)": opt["load"], "Solar generation (kW)": opt["solar_generation"], "Solar used (kW)": opt["solar_used"],
        "Grid import (kW)": opt["grid_import"], "Grid cost (₹)": opt["hourly_cost"]})
    st.dataframe(hourly, hide_index=True, use_container_width=True)
    appliance_report = pd.DataFrame([{"Appliance": a.name, "Power (kW)": a.power_kw, "Duration (h)": a.duration, "Scheduled start": fmt_hour(opt["starts"][i]), "Scheduled end": fmt_hour(opt["starts"][i] + a.duration), "Energy (kWh)": a.power_kw * a.duration} for i, a in enumerate(appliances)])
    c1, c2 = st.columns(2)
    with c1: st.download_button("⬇ Download hourly report CSV", hourly.to_csv(index=False).encode("utf-8"), "hourly_energy_report.csv", "text/csv", use_container_width=True)
    with c2: st.download_button("⬇ Download appliance schedule CSV", appliance_report.to_csv(index=False).encode("utf-8"), "optimized_appliance_schedule.csv", "text/csv", use_container_width=True)
    st.download_button("⬇ Download comparison summary CSV", cost_df.to_csv(index=False).encode("utf-8"), "optimization_summary.csv", "text/csv", use_container_width=True)

elif page == "About Project":
    st.markdown("## About the Project")
    st.markdown("""This project demonstrates a **Genetic Algorithm (GA)** for scheduling flexible household appliances to reduce estimated grid electricity cost while discouraging excessive simultaneous appliance demand. A simulated solar profile can offset grid imports during daylight hours.

**Chromosome representation:** one gene per appliance; each gene stores its start hour.

**Initial population:** candidate schedules are created by randomly choosing a valid start hour for each appliance.

**Fitness function:** estimated grid electricity cost after direct solar use plus a penalty for appliance load exceeding the configured limit. Lower fitness is better.

**Selection:** tournament selection chooses the best of three randomly sampled candidates.

**Crossover:** uniform crossover swaps genes between two parent schedules with the configured crossover probability.

**Mutation:** each gene has a configured chance of changing to another valid start hour.

**Elitism:** the best candidates are copied to the next generation to preserve good solutions.

**Comparison methods:** earliest-valid-start baseline, a load-aware greedy heuristic, and the GA. Comparisons use the same tariffs, appliances and solar profile.

**Solar assumptions:** the solar profile is a simple illustrative daylight curve. Solar offsets appliance demand directly; this version does not model batteries, export credits, actual weather, panel orientation, or real hardware. Tariffs are editable sample values, not official utility rates.

**Limitations:** the overload condition is penalized, not guaranteed impossible. The GA is a heuristic search and is not guaranteed to find the global optimum for every run.""")
    st.markdown("### Core calculations")
    st.latex(r"E_i = P_i \times D_i")
    st.markdown("Daily appliance energy is power multiplied by operating duration.")
    st.latex(r"G_h = \max(0, L_h - S_h)")
    st.markdown("Grid import in hour h is the appliance load minus available solar generation, with a lower bound of zero.")
    st.latex(r"C_{grid} = \sum_{h=0}^{23} G_h T_h")
    st.markdown("Fitness adds an overload penalty to this grid electricity cost.")

st.markdown("<div class='footer'><span>© SmartHome Energy Optimization · GA scheduling simulation</span><span>Python · Streamlit · Pandas · Plotly · Educational project · No hardware connected</span></div>", unsafe_allow_html=True)
