import streamlit as st
from datetime import date
from models.record import StandardSolution, CalibrationPoint, CalibrationCurve
from ui.components import render_audit_results
from config import CALIBRATION_POINTS


def build_calibration_curve_from_form() -> CalibrationCurve:
    """从表单构建校准曲线数据"""
    cc = CalibrationCurve()
    ss = StandardSolution()

    st.subheader("标准溶液信息")
    col1, col2, col3 = st.columns(3)
    with col1:
        conc_options = ["500", "1000"]
        stock_conc = st.selectbox("贮备液浓度 (μg/mL)", conc_options,
                                  index=0, key="cc_stock_conc")
        ss.stock_concentration = float(stock_conc)
        ss.stock_id = st.text_input("标准溶液编号", key="cc_stock_id")
    with col2:
        ss.stock_prep_date = st.date_input("贮备液配制日期", key="cc_stock_prep")
        ss.stock_expiry_date = st.date_input("贮备液有效期至", key="cc_stock_expiry")
    with col3:
        ss.working_concentration = st.number_input("使用液浓度 (μg/mL)",
                                                    value=10.0, step=1.0, key="cc_working_conc")
        ss.working_prep_date = st.date_input("使用液配制日期", key="cc_working_prep")
    cc.standard_solution = ss

    st.markdown("---")
    st.subheader("校准系列配制")

    col_h = st.columns([0.4, 1.2, 1.2, 1.2, 3])
    col_h[0].markdown("**序号**")
    col_h[1].markdown("**NH₃-N含量 (μg)**")
    col_h[2].markdown("**取用体积 (mL)**")
    col_h[3].markdown("**定容体积 (mL)**")
    col_h[4].markdown("**吸光度 A**")

    default_abs = ["", "0.048", "0.075", "0.144", "0.286", "0.427", "0.576", "0.720"]
    points = []
    for i, mass in enumerate(CALIBRATION_POINTS):
        cols = st.columns([0.4, 1.2, 1.2, 1.2, 3])
        cols[0].markdown(f"**{i}**")
        cols[1].markdown(f"{mass:.0f}")
        vol = mass / ss.working_concentration if ss.working_concentration else 0
        cols[2].markdown(f"{vol:.2f}")
        total_vol = st.session_state.get('cc_total_vol', 50.0)
        cols[3].markdown(f"{total_vol:.2f}")

        abs_val = cols[4].text_input(
            f"A{i}", value=default_abs[i] if i < len(default_abs) else "",
            key=f"cc_abs_{i}", label_visibility="collapsed",
            placeholder="吸光度值")

        try:
            absorbance = float(abs_val) if abs_val.strip() else 0.0
        except ValueError:
            absorbance = 0.0

        a_minus_a0 = None
        if i == 0:
            if absorbance > 0:
                a_minus_a0 = 0.0
            else:
                a_minus_a0 = 0.0
        elif absorbance is not None and points:
            a0 = points[0].absorbance
            a_minus_a0 = round(absorbance - a0, 4)

        points.append(CalibrationPoint(
            point_id=i, nh3_mass=mass, volume_taken=vol,
            working_conc=ss.working_concentration,
            absorbance=absorbance, a_minus_a0=a_minus_a0))

    cc.points = points
    cc.total_volume = total_vol
    return cc


def show_calibration_results(cc: CalibrationCurve):
    """显示回归计算结果"""
    if cc.regression_a is not None and cc.regression_b is not None:
        st.markdown("---")
        st.subheader("📈 回归计算结果")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("截距 a", f"{cc.regression_a:.5f}")
        col2.metric("斜率 b", f"{cc.regression_b:.5f}")
        r_val = cc.correlation_r or 0
        delta = f"{'✅' if r_val >= 0.999 else '❌'}"
        col3.metric("相关系数 r", f"{r_val:.5f}", delta=delta)
        col4.metric("回归方程", f"y={cc.regression_b:.4f}x+{cc.regression_a:.4f}")

        a0_val = cc.points[0].absorbance if cc.points else 0
        st.caption("A-A₀ 值:" + " | ".join(
            f"点{i}: {p.a_minus_a0:.4f}" if p.a_minus_a0 is not None else f"点{i}: —"
            for i, p in enumerate(cc.points)))
        if a0_val > 0.065:
            st.warning(f"空白吸光度 A₀={a0_val:.4f} 偏高，建议检查试剂和水质。")
