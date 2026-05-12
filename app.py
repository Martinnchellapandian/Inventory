import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ----------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------
st.set_page_config(
    page_title="Smart Inventory Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# SESSION STATE CALLBACKS (For 2-Way Demand Binding)
# ----------------------------------------------------
# 1. Initialize the starting values in session state
if 'monthly_demand' not in st.session_state:
    st.session_state.monthly_demand = 1000.0
if 'annual_demand' not in st.session_state:
    st.session_state.annual_demand = 12000.0

# 2. Create the callback functions to sync the values
def sync_annual():
    st.session_state.annual_demand = st.session_state.monthly_demand * 12.0

def sync_monthly():
    st.session_state.monthly_demand = st.session_state.annual_demand / 12.0

# ----------------------------------------------------
# CUSTOM CSS FOR PREMIUM DARK UI & GLASSMORPHISM
# ----------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 15px; padding: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5); margin-bottom: 20px;
    }
    .kpi-title { font-size: 14px; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .kpi-value { font-size: 32px; font-weight: 700; color: #00d2ff; text-shadow: 0 0 10px rgba(0, 210, 255, 0.5); }
    .ai-banner {
        background: linear-gradient(135deg, rgba(0, 210, 255, 0.1) 0%, rgba(58, 123, 213, 0.1) 100%);
        border-left: 5px solid #00d2ff; border-radius: 10px; padding: 25px; margin: 20px 0;
        box-shadow: 0 0 20px rgba(0, 210, 255, 0.2);
    }
    .ai-title { color: #00d2ff; font-size: 20px; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
    .alert-critical { border-left: 5px solid #ff4b4b; background: rgba(255, 75, 75, 0.1); padding: 15px; border-radius: 8px; color: #ff4b4b; font-weight: bold; }
    .alert-warning { border-left: 5px solid #faca15; background: rgba(250, 202, 21, 0.1); padding: 15px; border-radius: 8px; color: #faca15; font-weight: bold; }
    .alert-success { border-left: 5px solid #22c55e; background: rgba(34, 197, 94, 0.1); padding: 15px; border-radius: 8px; color: #22c55e; font-weight: bold; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# SIDEBAR INPUTS
# ----------------------------------------------------
st.sidebar.markdown("## ⚙️ Dashboard Controls")

st.sidebar.markdown("### 📊 1. Demand Inputs")

# 3. Attach the keys and callbacks directly to the number inputs
st.sidebar.number_input("Forecasted Monthly Demand", min_value=1.0, key="monthly_demand", on_change=sync_annual)
st.sidebar.number_input("Forecasted Annual Demand", min_value=12.0, key="annual_demand", on_change=sync_monthly)

# Extract the final annual demand for all mathematical calculations
annual_demand = st.session_state.annual_demand

current_stock = st.sidebar.number_input("Current Inventory Stock", min_value=0, value=1500)

st.sidebar.markdown("### 📦 2. Inventory & Weight Inputs")
order_cost = st.sidebar.number_input("Ordering Cost ($)", min_value=1.0, value=500.0)
unit_cost = st.sidebar.number_input("Unit Cost ($)", min_value=0.1, value=50.0)
carrying_cost_pct = st.sidebar.number_input("Carrying Cost (%)", min_value=1.0, value=20.0) / 100
warehouse_capacity = st.sidebar.number_input("Warehouse Capacity (Units)", min_value=1, value=5000)

st.sidebar.markdown("---")
st.sidebar.markdown("⚖️ **Unit to KG Conversion**")
weight_per_unit = st.sidebar.number_input("1 Unit = How many Kilograms (KG)?", min_value=0.01, value=5.0, step=0.5)

st.sidebar.markdown("### 🚢 3. Seaways Inputs")
sea_freight_cost = st.sidebar.number_input("Sea Freight Cost/KG ($)", min_value=0.1, value=1.5)
sea_lead_time = st.sidebar.number_input("Sea Lead Time (Days)", min_value=1, value=30)

st.sidebar.markdown("### ✈️ 4. Airways Inputs")
air_freight_cost = st.sidebar.number_input("Air Freight Cost/KG ($)", min_value=0.1, value=8.5)
air_lead_time = st.sidebar.number_input("Air Lead Time (Days)", min_value=1, value=5)

# ----------------------------------------------------
# BUSINESS LOGIC & CALCULATIONS
# ----------------------------------------------------
holding_cost = unit_cost * carrying_cost_pct
eoq = np.sqrt((2 * annual_demand * order_cost) / holding_cost) if holding_cost > 0 else 0

total_weight_kg = eoq * weight_per_unit
st.sidebar.info(f"📦 **Batch Weight (EOQ):** {total_weight_kg:,.2f} KG")

orders_per_year = annual_demand / eoq if eoq > 0 else 0
reorder_interval = 365 / orders_per_year if orders_per_year > 0 else 0
order_class = "Rare Order Quantity" if orders_per_year < 6 else "Frequent Order"

# Simplified Reorder Point using flat daily average
daily_demand = annual_demand / 365.0
rop_sea = daily_demand * sea_lead_time
rop_air = daily_demand * air_lead_time

transport_cost_sea = total_weight_kg * sea_freight_cost
transport_cost_air = total_weight_kg * air_freight_cost

if current_stock < rop_air:
    transport_rec = "Airways"
    rec_message = "Use Airways immediately due to critically low inventory levels to prevent stockouts."
    alert_status = "critical"
elif current_stock < rop_sea:
    transport_rec = "Airways"
    rec_message = "Inventory below sea route ROP. Use Airways to ensure timely replenishment."
    alert_status = "warning"
else:
    alert_status = "healthy"
    if transport_cost_sea < transport_cost_air:
        transport_rec = "Seaways"
        rec_message = "Use Seaways for cost-efficient bulk inventory transportation. Time permits."
    else:
        transport_rec = "Airways"
        rec_message = "Use Airways. Air freight is more cost-effective based on your EOQ and unit weight."

# ----------------------------------------------------
# DASHBOARD UI RENDER
# ----------------------------------------------------
st.title("🌐 Supply Chain & Logistics Optimizer")
st.markdown("Intelligent Inventory & Freight Analytics System")

col1, col2, col3, col4 = st.columns(4)
def kpi_card(title, value, suffix=""):
    return f'<div class="glass-card"><div class="kpi-title">{title}</div><div class="kpi-value">{value:,.0f}{suffix}</div></div>'

with col1: st.markdown(kpi_card("Economic Order Qty", eoq), unsafe_allow_html=True)
with col2: st.markdown(kpi_card("Orders Per Year", orders_per_year), unsafe_allow_html=True)
with col3: st.markdown(kpi_card("Reorder Interval", reorder_interval, " Days"), unsafe_allow_html=True)
with col4:
    font_size = "20px" if order_class == "Rare Order Quantity" else "24px"
    st.markdown(f'<div class="glass-card"><div class="kpi-title">Order Strategy</div><div class="kpi-value" style="font-size: {font_size};">{order_class}</div></div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="ai-banner">
    <div class="ai-title">🤖 AI Optimization Insight</div>
    <div style="font-size: 18px;"><b>Recommended Method:</b> {transport_rec}</div>
    <div style="color: #cbd5e1; margin-top: 5px;">{rec_message}</div>
</div>
""", unsafe_allow_html=True)

if alert_status == "critical":
    st.markdown('<div class="alert-critical">⚠️ CRITICAL: Inventory level below Air Route Reorder Point! Stockout imminent.</div>', unsafe_allow_html=True)
elif alert_status == "warning":
    st.markdown('<div class="alert-warning">⚡ WARNING: Inventory approaching reorder level (Below Sea Route ROP).</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="alert-success">✅ HEALTHY: Inventory levels are sufficient. Standard replenishment advised.</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_viz1, col_viz2 = st.columns((2, 1))
with col_viz1:
    st.markdown("### 📊 Transportation Cost Comparison (Per EOQ Batch)")
    fig_cost = go.Figure(data=[
        go.Bar(name='Seaways', x=['Freight Cost'], y=[transport_cost_sea], marker_color='#00d2ff'),
        go.Bar(name='Airways', x=['Freight Cost'], y=[transport_cost_air], marker_color='#ff4b4b')
    ])
    fig_cost.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#ffffff', barmode='group', margin=dict(l=0, r=0, t=30, b=0), height=300)
    st.plotly_chart(fig_cost, use_container_width=True)

with col_viz2:
    st.markdown("### 🏢 Warehouse Utilization")
    utilization_pct = (current_stock / warehouse_capacity) * 100
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=utilization_pct, number={'suffix': "%", 'font': {'color': '#ffffff'}},
        gauge={'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"}, 'bar': {'color': "#00d2ff"}, 'bgcolor': "rgba(255,255,255,0.1)", 'steps': [{'range': [0, 50], 'color': "rgba(34, 197, 94, 0.3)"}, {'range': [50, 85], 'color': "rgba(250, 202, 21, 0.3)"}, {'range': [85, 100], 'color': "rgba(255, 75, 75, 0.3)"}]}
    ))
    fig_gauge.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#ffffff', margin=dict(l=20, r=20, t=30, b=20), height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

col_tbl1, col_tbl2 = st.columns((2, 1))
with col_tbl1:
    st.markdown("### 📋 Transport Routing Analysis")
    table_data = {
        "Metric": ["Lead Time", "Reorder Point (ROP)", "Transport Cost (EOQ)"],
        "🚢 Seaways": [f"{sea_lead_time} Days", f"{rop_sea:,.0f} Units", f"${transport_cost_sea:,.2f}"],
        "✈️ Airways": [f"{air_lead_time} Days", f"{rop_air:,.0f} Units", f"${transport_cost_air:,.2f}"]
    }
    st.dataframe(pd.DataFrame(table_data), hide_index=True, use_container_width=True)

with col_tbl2:
    st.markdown("### 🧠 Smart Insights")
    st.markdown(f"""
    <div class="glass-card" style="padding: 15px;">
        <ul style="list-style-type: none; padding-left: 0; line-height: 1.8;">
            <li>📦 <b>Current Stock:</b> {current_stock:,} Units</li>
            <li>⚖️ <b>Total Batch Weight:</b> {total_weight_kg:,.2f} KG</li>
            <li>💰 <b>Holding Cost per Unit:</b> ${holding_cost:,.2f}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 14px;'>"
    "Smart Inventory Analytics Dashboard — Built with Streamlit & Plotly<br>"
    "<i>System Local Time: Tuesday, May 12, 2026 at 2:02:33 PM IST | Madurai, TN, India</i>"
    "</div>", 
    unsafe_allow_html=True
)