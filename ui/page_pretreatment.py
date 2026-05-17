import streamlit as st
from datetime import date


def build_pretreatment_from_form() -> tuple:
    """从表单构建前处理信息，返回 (method, details, date)"""
    st.subheader("前处理方法")

    method_key = st.radio(
        "前处理方法选择",
        options=["絮凝沉淀法", "预蒸馏法", "预处理-蒸馏法"],
        horizontal=True, key="pret_method_radio"
    )

    details = ""
    if "絮凝沉淀" in method_key:
        st.markdown("**絮凝沉淀法 (HJ 535-2009 6.2.2)**")
        col1, col2 = st.columns(2)
        with col1:
            znso4 = st.checkbox("加入硫酸锌溶液 (100g/L)", value=True, key="pret_znso4")
            naoh = st.checkbox("加入氢氧化钠溶液 (250g/L)", value=True, key="pret_naoh")
        with col2:
            ph_val = st.text_input("调节pH值", value="10.5", key="pret_ph")
            settle_time = st.text_input("静置沉降时间", value="充分沉降", key="pret_settle")
        details = "絮凝沉淀法: "
        if znso4:
            details += "加入1.0mL硫酸锌溶液(100g/L), "
        if naoh:
            details += "加入NaOH溶液(250g/L)调节pH, "
        details += f"pH≈{ph_val}, 静置{settle_time}, 取上清液分析"
    else:
        st.markdown("**预蒸馏法 (HJ 535-2009 6.2.3)**")
        col1, col2 = st.columns(2)
        with col1:
            mgo = st.checkbox("加入轻质氧化镁 (MgO), 0.25g/50mL", value=True, key="pret_mgo")
            boric = st.checkbox("硼酸溶液吸收 (20g/L)", value=True, key="pret_boric")
        with col2:
            distill_vol = st.text_input("馏出液收集体积 (mL)", value="200", key="pret_distill_vol")
            sample_vol = st.text_input("蒸馏取样体积 (mL)", value="50", key="pret_sample_vol")
        details = "预蒸馏法: "
        if mgo:
            details += f"取{sample_vol}mL水样, 加入0.25g轻质氧化镁, "
        details += "加热蒸馏, "
        if boric:
            details += "以硼酸溶液(20g/L)吸收, "
        details += f"收集约{distill_vol}mL馏出液"

    pret_date = st.date_input("前处理日期", key="pret_date")

    additional = st.text_area("操作备注 (可选)", key="pret_notes",
                              placeholder="记录前处理过程中的特殊情况...")
    if additional:
        details += "。备注: " + additional

    return method_key, details, pret_date
