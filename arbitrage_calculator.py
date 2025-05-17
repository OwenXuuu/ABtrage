import streamlit as st
import requests
from datetime import datetime

# 必须第一个 Streamlit 命令
st.set_page_config(
    page_title="三角套利计算器",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== session_state 初始化 ==========
if 'rates_last_update' not in st.session_state:
    st.session_state.rates_last_update = '未刷新'
if 'aud_usdt_rate' not in st.session_state:
    st.session_state.aud_usdt_rate = 0.65
if 'usdt_cny_rate' not in st.session_state:
    st.session_state.usdt_cny_rate = 7.2
if 'aud_cny_rate' not in st.session_state:
    st.session_state.aud_cny_rate = 4.7
if 'aud_usdt_target_profit' not in st.session_state:
    st.session_state.aud_usdt_target_profit = 1.2
if 'usdt_cny_target_profit' not in st.session_state:
    st.session_state.usdt_cny_target_profit = 1.2
if 'aud_cny_target_profit' not in st.session_state:
    st.session_state.aud_cny_target_profit = 1.2
if 'initial_aud_input' not in st.session_state:
    st.session_state.initial_aud_input = 100000.0
if 'fixed_profit_mode' not in st.session_state:
    st.session_state.fixed_profit_mode = '不开启'

# ========== 回调和API函数定义 ==========
def on_user_modify():
    st.session_state.rates_user_modified = True

def fetch_realtime_rates():
    rates = {'aud_usdt': 0.65, 'usdt_cny': 7.2, 'aud_cny': 4.7}
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=AUD&to=CNY", timeout=10)
        if r.ok:
            data = r.json()
            if 'rates' in data and 'CNY' in data['rates']:
                rates['aud_cny'] = float(data['rates']['CNY'])
    except: pass
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=cny", timeout=10)
        if r.ok:
            data = r.json()
            if 'tether' in data and 'cny' in data['tether']:
                rates['usdt_cny'] = float(data['tether']['cny'])
    except: pass
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=aud", timeout=10)
        if r.ok:
            data = r.json()
            if 'tether' in data and 'aud' in data['tether'] and data['tether']['aud'] != 0:
                rates['aud_usdt'] = 1 / float(data['tether']['aud'])
    except: pass
    return rates, datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# ========== 页面主标题 ==========
st.markdown("<h1 style='text-align: center; margin-bottom: 0.2em;'>三角套利收益计算器</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: 0.1em; margin-bottom: 0.2em; padding-left: 0.8em;'>(AUD → USDT → CNY)</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin-top: 0.1em;'>by LOSTGE</p>", unsafe_allow_html=True)

# ========== 顶部汇率更新时间+刷新按钮 ==========
col_time, col_btn = st.columns([8, 1])
with col_time:
    st.info(f"汇率数据更新时间：{st.session_state.rates_last_update}")
with col_btn:
    refresh_style = """
    <style>
    div[data-testid=\"column\"] > div {
        height: 100%;
        display: flex;
        align-items: flex-start;  /* 顶部对齐 */
    }
    .stButton>button {
        flex: 1 1 auto;
        width: 100% !important;
        height: 100% !important;
        min-height: 56px !important;
        font-size: 1.25em !important;
        background: #eaf4ff !important;
        border: 1px solid #b3d8fd !important;
        border-radius: 8px !important;
        color: #2563eb !important;
        padding: 0 !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em;
        margin-top: -6px !important; /* 适当上移，可微调 */
    }
    @media (max-width: 600px) {
        .stButton>button {min-height: 44px !important;}
    }
    </style>
    """
    st.markdown(refresh_style, unsafe_allow_html=True)
    if st.button("刷新数据", help="刷新汇率（API）", key="refresh_api_btn"):
        rates, fetch_time = fetch_realtime_rates()
        st.session_state.aud_usdt_rate = rates['aud_usdt']
        st.session_state.usdt_cny_rate = rates['usdt_cny']
        st.session_state.aud_cny_rate = rates['aud_cny']
        st.session_state.rates_last_update = fetch_time

# ========== 固定利润模式互斥选择 ==========
fixed_profit_options = [
    '不开启',
    'AUD/USDT 固定利润',
    'USDT/CNY 固定利润',
    'AUD/CNY 固定利润'
]
fixed_profit_mode = st.radio(
    '选择固定利润模式（每次只允许一个汇率对开启）',
    fixed_profit_options,
    index=fixed_profit_options.index(st.session_state.fixed_profit_mode) if 'fixed_profit_mode' in st.session_state else 0,
    key='fixed_profit_mode',
    horizontal=True
)

# ========== 汇率获取状态提示（移到最上方） ==========
with st.container():
    pass  # 保留结构，后续可扩展

# ========== 汇率输入区 ==========
with st.expander("调整汇率和初始金额", expanded=True):
    st.header('输入参数')
    if fixed_profit_mode == 'AUD/USDT 固定利润':
        usdt_cny = st.number_input('USDT/CNY 汇率', min_value=6.0, max_value=8.0, step=0.0001, format="%.4f", key='usdt_cny_rate', on_change=on_user_modify)
        aud_cny = st.number_input('AUD/CNY 汇率 (直接)', min_value=3.0, max_value=6.0, step=0.0001, format="%.4f", key='aud_cny_rate', on_change=on_user_modify)
        aud_usdt_target_profit = st.number_input(
            '目标套利利润率(%)',
            min_value=-5.0, max_value=5.0, step=0.01, format="%.2f",
            key='aud_usdt_target_profit', help='输入目标套利利润率', on_change=on_user_modify
        )
        aud_usdt = (aud_cny * (1 + aud_usdt_target_profit/100)) / usdt_cny
        st.text_input('AUD/USDT 汇率', value=f"{aud_usdt:.4f}", disabled=True)
    elif fixed_profit_mode == 'USDT/CNY 固定利润':
        aud_usdt = st.number_input('AUD/USDT 汇率', min_value=0.4, max_value=0.9, step=0.0001, format="%.4f", key='aud_usdt_rate', on_change=on_user_modify)
        aud_cny = st.number_input('AUD/CNY 汇率 (直接)', min_value=3.0, max_value=6.0, step=0.0001, format="%.4f", key='aud_cny_rate', on_change=on_user_modify)
        usdt_cny_target_profit = st.number_input(
            '目标套利利润率(%)',
            min_value=-5.0, max_value=5.0, step=0.01, format="%.2f",
            key='usdt_cny_target_profit', help='输入目标套利利润率', on_change=on_user_modify
        )
        usdt_cny = (aud_cny * (1 + usdt_cny_target_profit/100)) / aud_usdt
        st.text_input('USDT/CNY 汇率', value=f"{usdt_cny:.4f}", disabled=True)
    elif fixed_profit_mode == 'AUD/CNY 固定利润':
        aud_usdt = st.number_input('AUD/USDT 汇率', min_value=0.4, max_value=0.9, step=0.0001, format="%.4f", key='aud_usdt_rate', on_change=on_user_modify)
        usdt_cny = st.number_input('USDT/CNY 汇率', min_value=6.0, max_value=8.0, step=0.0001, format="%.4f", key='usdt_cny_rate', on_change=on_user_modify)
        aud_cny_target_profit = st.number_input(
            '目标套利利润率(%)',
            min_value=-5.0, max_value=5.0, step=0.01, format="%.2f",
            key='aud_cny_target_profit', help='输入目标套利利润率', on_change=on_user_modify
        )
        aud_cny = aud_usdt * usdt_cny / (1 + aud_cny_target_profit/100)
        st.text_input('AUD/CNY 汇率 (直接)', value=f"{aud_cny:.4f}", disabled=True)
    else:
        aud_usdt = st.number_input('AUD/USDT 汇率', min_value=0.4, max_value=0.9, step=0.0001, format="%.4f", key='aud_usdt_rate', on_change=on_user_modify)
        usdt_cny = st.number_input('USDT/CNY 汇率', min_value=6.0, max_value=8.0, step=0.0001, format="%.4f", key='usdt_cny_rate', on_change=on_user_modify)
        aud_cny = st.number_input('AUD/CNY 汇率 (直接)', min_value=3.0, max_value=6.0, step=0.0001, format="%.4f", key='aud_cny_rate', on_change=on_user_modify)
    st.divider()
    initial_aud_input = st.number_input('输入初始澳元 (AUD) 金额', min_value=1.0, step=1000.0, help="输入您计划用于套利的澳元数量", key="initial_aud_input", on_change=on_user_modify)

# ========== 计算与结果 ==========
st.header('计算结果')
if fixed_profit_mode == 'AUD/USDT 固定利润':
    usdt_cny = st.session_state.usdt_cny_rate
    aud_cny = st.session_state.aud_cny_rate
    aud_usdt_target_profit = st.session_state.aud_usdt_target_profit
    aud_usdt = (aud_cny * (1 + aud_usdt_target_profit/100)) / usdt_cny
elif fixed_profit_mode == 'USDT/CNY 固定利润':
    aud_usdt = st.session_state.aud_usdt_rate
    aud_cny = st.session_state.aud_cny_rate
    usdt_cny_target_profit = st.session_state.usdt_cny_target_profit
    usdt_cny = (aud_cny * (1 + usdt_cny_target_profit/100)) / aud_usdt
elif fixed_profit_mode == 'AUD/CNY 固定利润':
    aud_usdt = st.session_state.aud_usdt_rate
    usdt_cny = st.session_state.usdt_cny_rate
    aud_cny_target_profit = st.session_state.aud_cny_target_profit
    aud_cny = aud_usdt * usdt_cny / (1 + aud_cny_target_profit/100)
else:
    aud_usdt = st.session_state.aud_usdt_rate
    usdt_cny = st.session_state.usdt_cny_rate
    aud_cny = st.session_state.aud_cny_rate

initial_aud = initial_aud_input
cny_via_arbitrage = initial_aud * aud_usdt * usdt_cny
cny_direct = initial_aud * aud_cny
st.write(f"通过 AUD → USDT → CNY 路径可兑换: **{cny_via_arbitrage:,.4f} CNY**")
st.write(f"通过 AUD → CNY 直接兑换可得: **{cny_direct:,.4f} CNY**")
if cny_direct == 0:
    profit_percentage = 0.0
else:
    profit_percentage = ((cny_via_arbitrage - cny_direct) / cny_direct) * 100
st.write(f"套利收益率: **{profit_percentage:.5f}%**")
if profit_percentage > 0.00001:
    st.success(f"存在套利机会！盈利 { (cny_via_arbitrage - cny_direct):,.4f} CNY (每 {initial_aud:,.0f} AUD)")
elif profit_percentage < -0.00001:
    st.warning(f"反向套利可能更有利 (直接兑换优于三角套利)，亏损 {(cny_direct - cny_via_arbitrage):,.4f} CNY (每 {initial_aud:,.0f} AUD)")
else:
    st.info("当前没有明显的套利空间或收益/亏损极小。")
# 固定利润模式下显示目标达成情况
if fixed_profit_mode != '不开启':
    if fixed_profit_mode == 'AUD/USDT 固定利润':
        target = st.session_state.aud_usdt_target_profit
    elif fixed_profit_mode == 'USDT/CNY 固定利润':
        target = st.session_state.usdt_cny_target_profit
    elif fixed_profit_mode == 'AUD/CNY 固定利润':
        target = st.session_state.aud_cny_target_profit
    else:
        target = None
    if target is not None:
        diff = abs(profit_percentage - target)
        if diff < 0.01:
            st.success(f"✓ 已达到目标利润率 {target:.2f}%")
        else:
            st.info(f"当前利润率 {profit_percentage:.2f}% 与目标 {target:.2f}% 的差距: {diff:.2f}%")
st.caption("请注意：实际交易中会产生手续费、滑点等成本，本计算器未包含这些因素。汇率实时变动，请以实际交易平台为准。")
