import streamlit as st

# 设置页面标题
st.title('三角套利收益计算器 (AUD → USDT → CNY)')

# 输入汇率
st.header('输入汇率')

# AUD/USDT 汇率
aud_usdt_rate = st.slider('AUD/USDT 汇率', min_value=0.4, max_value=0.6, value=0.5, step=0.001)

# USDT/CNY 汇率
usdt_cny_rate = st.slider('USDT/CNY 汇率', min_value=6.5, max_value=7.5, value=7.0, step=0.01)

# AUD/CNY 汇率
aud_cny_rate = st.slider('AUD/CNY 汇率 (直接)', min_value=4.0, max_value=6.0, value=4.8, step=0.01)

# 计算
st.header('计算结果')

# 假设初始投入为 1 AUD
initial_aud = 1

# 通过套利路径 (AUD → USDT → CNY)
cny_via_arbitrage = initial_aud * aud_usdt_rate * usdt_cny_rate

# 通过直接路径 (AUD → CNY)
cny_direct = initial_aud * aud_cny_rate

st.write(f"通过 AUD → USDT → CNY 路径可兑换: {cny_via_arbitrage:.4f} CNY")
st.write(f"通过 AUD → CNY 直接兑换可得: {cny_direct:.4f} CNY")

# 计算收益率
if cny_direct == 0: # 避免除以零错误
    profit_percentage = 0
else:
    profit_percentage = ((cny_via_arbitrage - cny_direct) / cny_direct) * 100

st.write(f"套利收益率: {profit_percentage:.2f}%")

# 根据收益率显示提示信息
if profit_percentage > 0:
    st.success("存在套利机会")
else:
    st.error("当前没有套利空间") 