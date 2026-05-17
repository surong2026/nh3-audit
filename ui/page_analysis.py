import streamlit as st
from models.record import SampleResult, QCStandard, ParallelSample


def build_analysis_from_form() -> dict:
    """从表单构建分析条件与样品结果，返回字典"""
    data = {}

    st.subheader("仪器与测定条件")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        data['wavelength'] = st.number_input("波长 (nm)", value=420, min_value=300, max_value=800,
                                              step=10, key="an_wavelength")
        data['reference_solution'] = st.text_input("参比溶液", value="水", key="an_ref")
    with c2:
        data['cuvette_path'] = st.selectbox("比色皿 (mm)", [10, 20], index=1, key="an_cuvette")
        data['color_dev_time'] = st.number_input("显色时间 (min)", value=10, min_value=1,
                                                  max_value=60, key="an_color_time")
    with c3:
        data['nessler_method'] = st.selectbox("纳氏试剂配制法",
                                               ["HgI2-KI-NaOH", "HgCl2-KI-KOH", ""],
                                               key="an_nessler")
    with c4:
        data['tartrate_boiled'] = st.checkbox("酒石酸钾钠已煮沸除氨", value=True, key="an_tartrate")
        data['ammonia_free_water'] = st.checkbox("使用无氨水", value=True, key="an_ammfree")

    st.markdown("---")
    st.subheader("空白")
    cb1, cb2 = st.columns(2)
    with cb1:
        data['lab_blank_abs'] = st.number_input("实验室空白吸光度 Ab",
                                                value=0.029, step=0.001,
                                                format="%.4f", key="an_lab_blank")
    with cb2:
        has_field = st.checkbox("有全程序/现场空白", value=True, key="an_has_field")
        if has_field:
            data['field_blank_abs'] = st.number_input("全程序空白吸光度",
                                                       value=0.0, step=0.001,
                                                       format="%.4f", key="an_field_blank")
        else:
            data['field_blank_abs'] = None

    st.markdown("---")
    st.subheader("样品测定结果")
    n_samples = st.number_input("样品数量", min_value=0, max_value=50, value=8,
                                key="an_nsamples")
    samples = []
    for i in range(n_samples):
        with st.expander(f"样品 {i+1}", expanded=(i < 3)):
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            with sc1:
                sid = st.text_input("样品编号", key=f"an_sid_{i}", placeholder=f"YL{i+1:03d}")
            with sc2:
                sname = st.text_input("样品名称", key=f"an_sname_{i}", placeholder="点位名称")
            with sc3:
                sabs = st.number_input("吸光度", value=0.0, step=0.001,
                                        format="%.4f", key=f"an_sabs_{i}")
            with sc4:
                sdil = st.number_input("稀释倍数", value=1.0, step=1.0, key=f"an_sdil_{i}")
            with sc5:
                svol = st.number_input("取样体积 (mL)", value=50.0, step=1.0, key=f"an_svol_{i}")
            sconc = st.number_input("计算结果 ρN (mg/L)", value=0.0, step=0.001,
                                     format="%.4f", key=f"an_sconc_{i}")
            if sid:
                samples.append(SampleResult(
                    sample_id=sid, sample_name=sname, absorbance=sabs,
                    dilution_factor=sdil, sample_volume=svol,
                    calculated_conc=sconc))
    data['samples'] = samples

    st.markdown("---")
    st.subheader("质控标准样品")
    has_qc = st.checkbox("有质控标准样品", value=True, key="an_has_qc")
    qc_items = []
    if has_qc:
        n_qc = st.number_input("质控样数量", min_value=1, max_value=10, value=1, key="an_nqc")
        for i in range(n_qc):
            qc1, qc2, qc3 = st.columns(3)
            with qc1:
                qid = st.text_input("质控样编号", key=f"an_qid_{i}", placeholder=f"QC{i+1}")
            with qc2:
                qcert = st.number_input("标准值 (mg/L)", value=1.21 if i == 0 else 0.0,
                                        step=0.01, format="%.3f", key=f"an_qcert_{i}")
            with qc3:
                qmeas = st.number_input("测定值 (mg/L)", value=0.0, step=0.001,
                                         format="%.4f", key=f"an_qmeas_{i}")
            if qid:
                qc_items.append(QCStandard(qc_id=qid, certified_value=qcert, measured_value=qmeas))
    data['qc_standards'] = qc_items

    st.markdown("---")
    st.subheader("平行样")
    has_par = st.checkbox("有平行样", value=True, key="an_has_par")
    parallels = []
    if has_par:
        n_par = st.number_input("平行样组数", min_value=1, max_value=20, value=1, key="an_npar")
        for i in range(n_par):
            pc1, pc2, pc3, pc4 = st.columns(4)
            with pc1:
                oid = st.text_input("原样编号", key=f"an_poid_{i}", placeholder="原样")
            with pc2:
                pid = st.text_input("平行样编号", key=f"an_ppid_{i}", placeholder="平行样")
            with pc3:
                va = st.number_input("原样值 (mg/L)", value=0.0, step=0.001,
                                      format="%.4f", key=f"an_pva_{i}")
            with pc4:
                vb = st.number_input("平行值 (mg/L)", value=0.0, step=0.001,
                                      format="%.4f", key=f"an_pvb_{i}")
            if oid:
                parallels.append(ParallelSample(
                    original_id=oid, parallel_id=pid, value_a=va, value_b=vb))
    data['parallels'] = parallels

    return data
