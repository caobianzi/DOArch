"""
查询已退市期权合约的小工具 delisted-options-archives(简称DOArch)，
用于准确定位要找的合约。
"""
import streamlit as st
import pandas as pd
# from datetime import datetime
import os, time
import tushare as ts
from sqlalchemy import create_engine

st.set_page_config(
    page_title="DOArch-退市期权档案库",  # 网页标题
    page_icon="🔱",                   # 方案A：直接使用Emoji
    layout="wide"
)

st.title('退市期权合约查询 DO ARCHIVE')
st.caption("© 2025 [樊沛涵]. https://github.com/caobianzi/DOArch")  # All rights reserved.
# 获取当前脚本所在的目录
current_path = os.path.dirname(os.path.abspath(__file__))
# 获取当前脚本所在的项目根目录
root_path = os.path.dirname(current_path)
doarch_engine = create_engine(r"sqlite:///" + root_path + "\\DOArch\\doarch.db")  # 本地数据引擎
# doarch_engine = create_engine(r"doarch.db?mode=ro", connect_args={"uri": True})  # 在streamlit clound发布时，按此配置mode=ro为只读

# token = 'ec776ec032145e26891a3ef86941ca5ff938380e936ecef30f14cc08'
# pro = ts.pro_api(token)

# st.set_page_config(layout="wide")  # layout="centered"  730px 内容居中，左右留白.旨在提升移动端和小屏设备的可读性

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    exchange = st.selectbox('交易所:', ('SSE', 'SZSE', 'all'), key="exchange_name")
with col2:
    call_put = st.selectbox('期权类型:', ('C', 'P', 'all'), key="callorput")
with col3:
    s_month = st.text_input('结算月:', placeholder='例如: 202401')
with col4:
    list_date = st.text_input('开始交易日期:', placeholder='例如: 20240120')
    # list_date = st.date_input('开始交易日期(格式: yyyymmdd):')
with col5:
    delist_date = st.text_input('最后交易日期:', placeholder='例如: 20240120')
with col6:
    o_name = st.text_input('合约名称:')

repaint_button = st.button("已退市期权合约查询", disabled=False, use_container_width=True, type="primary")

if repaint_button:
    df_sh = pd.read_sql("select * from option_contract_shanghai ;", doarch_engine)
    df_sz = pd.read_sql("select * from option_contract_shenzhen ;", doarch_engine)
    df_o = pd.concat([df_sh, df_sz], ignore_index=True)
    df_o['list_date'] = pd.to_datetime(df_o['list_date'])#.dt.date
    df_o['delist_date'] = pd.to_datetime(df_o['delist_date'])#.dt.date
    df_o['last_edate'] = pd.to_datetime(df_o['last_edate'])#.dt.date
    df_o['last_ddate'] = pd.to_datetime(df_o['last_ddate'])#.dt.date

    if exchange == 'SSE':
        c1 = (df_o['exchange'] == 'SSE')
    elif exchange == 'SZSE':
        c1 = (df_o['exchange'] == 'SZSE')
    elif exchange == 'all':
        c1 = ((df_o['exchange'] == 'SSE') | (df_o['exchange'] == 'SZSE'))
    # 期权类型
    if call_put == 'C':  # or exchange == 'P':
        c2 = (df_o['call_put'] == 'C')
    elif call_put == 'P':
        c2 = (df_o['call_put'] == 'P')
    elif call_put == 'all':
        c2 = ((df_o['call_put'] == 'C') | (df_o['call_put'] == 'P'))

    if s_month != "":
        c3 = (df_o['s_month'] == s_month)  # 合约到期月份
    else:
        c3 = True

    df_os = df_o[c1 & c2 & c3].copy()

    if list_date != '':  # 开始交易日 pd.to_datetime(list_date, format='%Y%m%d')
        df_os = df_os[(df_os['list_date'] >= pd.to_datetime(list_date, format="%Y%m%d"))]

    if delist_date != '':  # 最后交易日期
        df_os = df_os[(df_os['delist_date'] <= pd.to_datetime(delist_date, format='%Y%m%d'))]

    if o_name != '':  # 如果o_name不为空，筛选合约名称
        df_os = df_os[df_os['name'].str.contains(o_name, na=False)]

    # df_os.to_excel("f:/退市option.xlsx")

    df_os.drop(columns=['index', 'per_unit', 'exercise_type', 'opt_type', 'quote_unit', 'min_price_chg'], inplace=True)
    df_os.rename(columns={"ts_code": "代码", "exchange": "交易所", "name":"名称", "opt_code": "标准合约代码",
                         "call_put": "期权类型", "exercise_price": "行权价", "s_month": "结算月", "maturity_date": "到期日",
                         "list_price": "挂牌基准价", "list_date": "开始交易日期", "delist_date": "最后交易日期",
                         "last_edate": "行权日期", "last_ddate": "交割日期"}, inplace=True)


    st.dataframe(df_os)
    st.caption("数量:" + str(len(df_os)))
    st.caption("300ETF期权最早于20191223上市交易，50ETF期权最早于20150209上市交易，创业板ETF期权最早于20220919上市交易，"
               "中证500ETF期权最早于20220919上市交易，科创板50ETF最早于20230605上市交易")


# # --- 数据更新区域 ---

with st.expander("数据更新"):
    repaint_button_sh = st.button("更新上交所[退市]期权合约信息", disabled=False, use_container_width=True, type="primary")
    st.warning("按Tushare要求, 两次更新需间隔1分钟以上, 否则报错! ")
    repaint_button_sz = st.button("更新深交所[退市]期权合约信息", disabled=False, use_container_width=True, type="primary")

    # df_o = pd.read_sql("select * from option_contract", con=gl.qf_finance_engine)

    if repaint_button_sh:
        sh_option_delisted = pro.opt_basic(exchange='SSE', list_status='D')  # 上交所退市期权
        sh_option_delisted.to_sql('option_contract_shanghai', doarch_engine, index=True, if_exists='replace',chunksize=10000)
        # 创建一个占位符用于显示状态文本
        status_text = st.empty()
        # 创建进度条
        progress_bar = st.progress(0)
        for i in range(60):
            # 计算进度百分比
            progress = (i + 1) / 60
            # 更新进度条
            progress_bar.progress(progress)
            # 更新状态文本（显示剩余时间）
            status_text.text(f"剩余时间: {60 - (i + 1)} 秒")
            # 暂停 1 秒
            time.sleep(1)

        status_text.text("✅ 1分钟计时完成！")
        st.balloons()

    if repaint_button_sz:
        sz_option_delisted = pro.opt_basic(exchange='SZSE', list_status='D')  # 深交所退市期权
        sz_option_delisted.to_sql('option_contract_shenzhen', doarch_engine, index=True, if_exists='replace', chunksize=10000)
        # 创建一个占位符用于显示状态文本
        status_text = st.empty()
        # 创建进度条
        progress_bar = st.progress(0)
        for i in range(60):
            # 计算进度百分比
            progress = (i + 1) / 60
            # 更新进度条
            progress_bar.progress(progress)
            # 更新状态文本（显示剩余时间）
            status_text.text(f"剩余时间: {60 - (i + 1)} 秒")
            # 暂停 1 秒
            time.sleep(1)

        status_text.text("✅ 1分钟计时完成！")
        st.balloons()


