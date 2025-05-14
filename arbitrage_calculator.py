import streamlit as st
import requests
from datetime import datetime # 新增导入

# 设置页面标题
st.markdown("<h1 style='text-align: center; margin-bottom: 0.2em;'>三角套利收益计算器</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: 0.1em; margin-bottom: 0.2em; padding-left: 0.8em;'>(AUD → USDT → CNY)</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin-top: 0.1em;'>by LOSTGE</p>", unsafe_allow_html=True)

# --- 默认回退汇率 ---
DEFAULT_AUD_USDT = 0.65 # Adjusted based on typical ranges, original was 0.55
DEFAULT_USDT_CNY = 7.2  # Adjusted based on typical ranges, original was 7.0
DEFAULT_AUD_CNY = 4.7   # Adjusted based on typical ranges, original was 4.8

# --- 缓存设置 ---
CACHE_TTL_SECONDS = 10 * 60  # 缓存10分钟

# --- 获取实时汇率的函数 (带缓存) ---
@st.cache_data(ttl=CACHE_TTL_SECONDS)
def fetch_realtime_rates_cached():
    rates = {
        'aud_usdt': DEFAULT_AUD_USDT,
        'usdt_cny': DEFAULT_USDT_CNY,
        'aud_cny': DEFAULT_AUD_CNY
    }
    fetched_any_successful = False
    errors = []
    api_timeout = 15 # API请求超时时间增加到15秒
    current_fetch_time = datetime.now() # 获取当前时间

    # 1. AUD/CNY from Frankfurter
    try:
        response = requests.get("https://api.frankfurter.app/latest?from=AUD&to=CNY", timeout=api_timeout)
        response.raise_for_status()
        data = response.json()
        if 'rates' in data and 'CNY' in data['rates']:
            rates['aud_cny'] = float(data['rates']['CNY'])
            fetched_any_successful = True
        else:
            errors.append("AUD/CNY rate not found in Frankfurter API response.")
    except requests.exceptions.RequestException as e:
        errors.append(f"Error fetching AUD/CNY from Frankfurter: {e}")
    except ValueError:
        errors.append("Invalid JSON response or rate format for AUD/CNY from Frankfurter.")

    # 2. USDT/CNY from CoinGecko
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=cny", timeout=api_timeout)
        response.raise_for_status()
        data = response.json()
        if 'tether' in data and 'cny' in data['tether']:
            rates['usdt_cny'] = float(data['tether']['cny'])
            fetched_any_successful = True
        else:
            errors.append("USDT/CNY rate not found in CoinGecko API response.")
    except requests.exceptions.RequestException as e:
        errors.append(f"Error fetching USDT/CNY from CoinGecko: {e}")
    except ValueError:
        errors.append("Invalid JSON response or rate format for USDT/CNY from CoinGecko.")

    # 3. AUD/USDT from CoinGecko (fetch USDT_AUD then invert)
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=aud", timeout=api_timeout)
        response.raise_for_status()
        data = response.json()
        if 'tether' in data and 'aud' in data['tether'] and data['tether']['aud'] != 0:
            usdt_aud_rate = float(data['tether']['aud'])
            rates['aud_usdt'] = 1 / usdt_aud_rate
            fetched_any_successful = True
        elif 'tether' in data and 'aud' in data['tether'] and data['tether']['aud'] == 0:
            errors.append("USDT/AUD rate from CoinGecko is zero, cannot calculate AUD/USDT.")
        else:
            errors.append("AUD/USDT rate (via USDT/AUD) not found in CoinGecko API response.")
    except requests.exceptions.RequestException as e:
        errors.append(f"Error fetching AUD/USDT from CoinGecko: {e}")
    except ValueError:
        errors.append("Invalid JSON response or rate format for AUD/USDT from CoinGecko.")
    except ZeroDivisionError:
        errors.append("Error calculating AUD/USDT: USDT/AUD rate was zero.")
        
    return rates, fetched_any_successful, errors, current_fetch_time

# --- 获取初始汇率 (调用缓存函数) ---
with st.spinner("正在获取最新汇率..."): # 使用 spinner
    fetched_rates, rates_successfully_fetched_any, fetch_errors, last_update_time = fetch_realtime_rates_cached()

# --- 显示获取状态 ---
if rates_successfully_fetched_any and not fetch_errors:
    st.success(f"✓ 汇率数据已处理！(数据更新于: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')}) 您仍可手动调整。")
elif rates_successfully_fetched_any and fetch_errors:
    st.info(f"部分汇率已加载 (数据更新于: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')})。其他使用默认值。您可手动调整。")
    for error in fetch_errors:
        st.warning(f"加载问题: {error}")
else: 
    st.error("✕ 无法加载实时汇率，已使用默认值。请检查网络连接或稍后再试。您可手动调整数值。")
    if fetch_errors: 
      for error in fetch_errors:
          st.caption(f"错误详情: {error}")

# --- Helper functions for synchronization ---
def create_sync_callbacks(rate_key_suffix, number_widget_key, slider_widget_key):
    def sync_from_number_input():
        st.session_state[f'{rate_key_suffix}_rate'] = st.session_state[number_widget_key]

    def sync_from_slider():
        st.session_state[f'{rate_key_suffix}_rate'] = st.session_state[slider_widget_key]
    return sync_from_number_input, sync_from_slider

# --- Initialize session state for rates ---
# 使用获取到的汇率或默认值来初始化 session_state
if 'aud_usdt_rate' not in st.session_state:
    st.session_state.aud_usdt_rate = fetched_rates['aud_usdt']
if 'usdt_cny_rate' not in st.session_state:
    st.session_state.usdt_cny_rate = fetched_rates['usdt_cny']
if 'aud_cny_rate' not in st.session_state:
    st.session_state.aud_cny_rate = fetched_rates['aud_cny']
    
# 使用 Expander 来组织输入
with st.expander("调整汇率和初始金额", expanded=True):
    st.header('输入参数') 

    # --- AUD/USDT 汇率 ---
    st.subheader("AUD/USDT 汇率")
    aud_usdt_sync_num, aud_usdt_sync_slider = create_sync_callbacks('aud_usdt', 'aud_usdt_num_widget', 'aud_usdt_slider_widget')
    st.number_input(
        '设定值',
        min_value=0.4, max_value=0.9, # Broader range
        value=st.session_state.aud_usdt_rate,
        step=0.0001, format="%.4f",
        key='aud_usdt_num_widget',
        on_change=aud_usdt_sync_num,
        help="直接输入 AUD/USDT 汇率"
    )
    st.slider(
        '通过滑块调整',
        min_value=0.4, max_value=0.9, # Broader range
        value=st.session_state.aud_usdt_rate,
        step=0.0001, format="%.4f",
        key='aud_usdt_slider_widget',
        on_change=aud_usdt_sync_slider
    )
    aud_usdt_rate = st.session_state.aud_usdt_rate
    st.divider()

    # --- USDT/CNY 汇率 ---
    st.subheader("USDT/CNY 汇率")
    usdt_cny_sync_num, usdt_cny_sync_slider = create_sync_callbacks('usdt_cny', 'usdt_cny_num_widget', 'usdt_cny_slider_widget')
    st.number_input(
        '设定值',
        min_value=6.0, max_value=8.0, # Broader range
        value=st.session_state.usdt_cny_rate,
        step=0.0001, format="%.4f",
        key='usdt_cny_num_widget',
        on_change=usdt_cny_sync_num,
        help="直接输入 USDT/CNY 汇率"
    )
    st.slider(
        '通过滑块调整',
        min_value=6.0, max_value=8.0, # Broader range
        value=st.session_state.usdt_cny_rate,
        step=0.0001, format="%.4f",
        key='usdt_cny_slider_widget',
        on_change=usdt_cny_sync_slider
    )
    usdt_cny_rate = st.session_state.usdt_cny_rate
    st.divider()

    # --- AUD/CNY 汇率 ---
    st.subheader("AUD/CNY 汇率 (直接)")
    aud_cny_sync_num, aud_cny_sync_slider = create_sync_callbacks('aud_cny', 'aud_cny_num_widget', 'aud_cny_slider_widget')
    st.number_input(
        '设定值',
        min_value=3.0, max_value=6.0, # Broader range
        value=st.session_state.aud_cny_rate,
        step=0.0001, format="%.4f",
        key='aud_cny_num_widget',
        on_change=aud_cny_sync_num,
        help="直接输入 AUD/CNY 汇率"
    )
    st.slider(
        '通过滑块调整',
        min_value=3.0, max_value=6.0, # Broader range
        value=st.session_state.aud_cny_rate,
        step=0.0001, format="%.4f",
        key='aud_cny_slider_widget',
        on_change=aud_cny_sync_slider
    )
    aud_cny_rate = st.session_state.aud_cny_rate
    st.divider()

    # --- 初始金额输入 ---
    st.subheader("初始投资金额")
    initial_aud_input = st.number_input('输入初始澳元 (AUD) 金额', min_value=1.0, value=100000.0, step=1000.0, help="输入您计划用于套利的澳元数量")

# 计算 (保持在 Expander 外部，使其一直可见)
st.header('计算结果')

# 初始投入 AUD
initial_aud = initial_aud_input

# 通过套利路径 (AUD → USDT → CNY)
cny_via_arbitrage = initial_aud * aud_usdt_rate * usdt_cny_rate

# 通过直接路径 (AUD → CNY)
cny_direct = initial_aud * aud_cny_rate

st.write(f"通过 AUD → USDT → CNY 路径可兑换: **{cny_via_arbitrage:,.4f} CNY**")
st.write(f"通过 AUD → CNY 直接兑换可得: **{cny_direct:,.4f} CNY**")

# 计算收益率
if cny_direct == 0: 
    profit_percentage = 0.0
else:
    profit_percentage = ((cny_via_arbitrage - cny_direct) / cny_direct) * 100

st.write(f"套利收益率: **{profit_percentage:.5f}%**") 

# 根据收益率显示提示信息
if profit_percentage > 0.00001: 
    st.success(f"存在套利机会！盈利 { (cny_via_arbitrage - cny_direct):,.4f} CNY (每 {initial_aud:,.0f} AUD)")
elif profit_percentage < -0.00001:
    st.warning(f"反向套利可能更有利 (直接兑换优于三角套利)，亏损 {(cny_direct - cny_via_arbitrage):,.4f} CNY (每 {initial_aud:,.0f} AUD)")
else:
    st.info("当前没有明显的套利空间或收益/亏损极小。")

st.caption("请注意：实际交易中会产生手续费、滑点等成本，本计算器未包含这些因素。汇率实时变动，请以实际交易平台为准。") 
