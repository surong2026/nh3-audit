import streamlit as st
import json
from datetime import date, datetime
from pathlib import Path

from models.record import AnalysisRecord, CalibrationCurve
from ui.components import record_info_form
from ui.page_standard_curve import build_calibration_curve_from_form, show_calibration_results
from ui.page_pretreatment import build_pretreatment_from_form
from ui.page_analysis import build_analysis_from_form
from ui.page_report import show_report
from engine.auditor import Auditor
from utils.pdf_parser import parse_pdf

st.set_page_config(
    page_title="氨氮分析记录审核系统 — HJ 535-2009",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data" / "saved_records"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def init_session_state():
    defaults = {
        "record": AnalysisRecord(),
        "calibration_curve": CalibrationCurve(),
        "audit_results": {},
        "full_report": None,
        "current_tab": "标准曲线",
        "pdf_parsed": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def save_record(record: AnalysisRecord, filename: str):
    path = DATA_DIR / f"{filename}.json"
    path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def load_record(path: str) -> AnalysisRecord:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return AnalysisRecord.from_dict(data)


def run_audit_for_category(record: AnalysisRecord, category: str):
    auditor = Auditor()
    return auditor.audit_category(record, category)


def run_full_audit(record: AnalysisRecord):
    auditor = Auditor()
    st.session_state.full_report = auditor.audit(record)


def main():
    init_session_state()

    with st.sidebar:
        st.title("🧪 氨氮分析审核")
        st.caption("HJ 535-2009 纳氏试剂分光光度法")
        st.markdown("---")

        tab = st.radio("导航", ["1. 校准曲线", "2. 前处理", "3. 分析与结果",
                                "4. 📋 审核报告"],
                        key="nav_radio",
                        format_func=lambda x: x.split(". ", 1)[-1])

        if tab == "4. 📋 审核报告":
            st.markdown("---")
            if st.button("🔄 执行全部审核", use_container_width=True, type="primary"):
                run_full_audit(st.session_state.record)
                st.success("审核完成！")

        st.markdown("---")
        st.caption("📤 PDF 上传审核")

        pdf_file = st.file_uploader("上传分析记录 PDF", type=["pdf"],
                                    key="pdf_uploader",
                                    help="上传 HJ 535-2009 氨氮分析记录 PDF，系统自动提取数据并审核")

        if pdf_file is not None:
            try:
                record = parse_pdf(pdf_file.getvalue(), pdf_file.name)
                st.session_state.record = record
                st.session_state.pdf_parsed = True

                st.success(f"✅ 已解析: {pdf_file.name}")
                with st.expander("📊 查看提取数据"):
                    st.caption(f"**日期**: {record.analysis_date}")
                    st.caption(f"**分析人**: {record.analyst}")
                    st.caption(f"**方法**: {record.method_reference}")
                    st.caption(f"**仪器**: {record.instrument_model}")
                    st.caption(f"**波长/比色皿/显色**: {record.wavelength}nm / {record.cuvette_path}mm / {record.color_dev_time}min")
                    st.caption(f"**校准曲线**: {len(record.calibration_curve.points)}点, "
                              f"r={record.calibration_curve.correlation_r or '未提取'}")
                    st.caption(f"**样品**: {len(record.samples)}个")
                    st.caption(f"**质控样**: {len(record.qc_standards)}个")
                    st.caption(f"**平行样**: {len(record.parallels)}个")

                if st.button("⚡ 一键审核此 PDF", use_container_width=True, type="primary",
                            key="pdf_audit_btn"):
                    if not record.calibration_curve.points:
                        st.error("未从 PDF 中提取到校准曲线数据，请检查 PDF 是否完整")
                    else:
                        run_full_audit(record)
                        st.rerun()

            except Exception as e:
                st.error(f"PDF 解析失败: {e}")
                st.info("请确认上传的是 HJ 535-2009 氨氮分析记录 PDF。也可手动填写各Tab页数据。")

        st.markdown("---")
        st.caption("💾 数据管理")
        save_name = st.text_input("保存名称", key="save_name", placeholder="如: 20260508-氨氮")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 保存记录", use_container_width=True):
                record = st.session_state.record
                name = save_name or (record.analysis_date.isoformat() if record.analysis_date else "record")
                path = save_record(record, name)
                st.success(f"已保存: {path}")
        with col_s2:
            json_file = st.file_uploader("加载 JSON 记录", type=["json"], key="load_json")
            if json_file:
                record = AnalysisRecord.from_dict(json.load(json_file))
                st.session_state.record = record
                st.session_state.pdf_parsed = False
                st.success(f"已加载: {record.record_id or json_file.name}")

        st.markdown("---")
        st.caption("© 2026 实验室分析记录审核系统 v1.0")

    # --- Tab 1: 校准曲线 ---
    if tab == "1. 校准曲线":
        st.header("1. 标准曲线配制与审核")
        st.caption("依据 HJ 535-2009 7.1 校准曲线的绘制")

        analyst, analysis_date, inst_model, inst_id, temp, humidity = record_info_form()

        cc = build_calibration_curve_from_form()
        st.session_state.calibration_curve = cc

        st.markdown("---")
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            audit_clicked = st.button("▶ 审核校准曲线", type="primary", use_container_width=True)

        if audit_clicked:
            record = st.session_state.record
            record.analyst = analyst
            record.analysis_date = analysis_date
            record.instrument_model = inst_model
            record.instrument_id = inst_id
            record.temperature = temp
            record.humidity = humidity
            record.calibration_curve = cc

            items = run_audit_for_category(record, "校准曲线")
            items += run_audit_for_category(record, "标准溶液")
            st.session_state.audit_results["标准曲线"] = items
            show_calibration_results(cc)
            st.markdown("### 📋 审核结果")
            from ui.components import render_audit_results
            render_audit_results(items)
        elif cc.points:
            st.session_state.record.calibration_curve = cc

    # --- Tab 2: 前处理 ---
    elif tab == "2. 前处理":
        st.header("2. 样品前处理审核")
        st.caption("依据 HJ 535-2009 6.2 样品前处理")

        method, details, pret_date = build_pretreatment_from_form()

        st.markdown("---")
        if st.button("▶ 审核前处理", type="primary"):
            record = st.session_state.record
            record.pretreatment_method = method
            record.pretreatment_details = details
            record.pretreatment_date = pret_date

            items = run_audit_for_category(record, "前处理")
            items += run_audit_for_category(record, "标准溶液")
            st.session_state.audit_results["前处理"] = items

            st.markdown("### 📋 审核结果")
            from ui.components import render_audit_results
            render_audit_results(items)

    # --- Tab 3: 分析与结果 ---
    elif tab == "3. 分析与结果":
        st.header("3. 分析条件与样品结果审核")
        st.caption("依据 HJ 535-2009 7 分析步骤")

        data = build_analysis_from_form()

        st.markdown("---")
        if st.button("▶ 审核分析结果", type="primary"):
            record = st.session_state.record
            record.wavelength = data['wavelength']
            record.cuvette_path = data['cuvette_path']
            record.color_dev_time = data['color_dev_time']
            record.reference_solution = data['reference_solution']
            record.nessler_method = data['nessler_method']
            record.tartrate_boiled = data['tartrate_boiled']
            record.ammonia_free_water = data['ammonia_free_water']
            record.lab_blank_absorbance = data['lab_blank_abs']
            record.field_blank_absorbance = data.get('field_blank_abs')
            record.samples = data['samples']
            record.qc_standards = data['qc_standards']
            record.parallels = data['parallels']

            # First run calibration audit to get regression
            if record.calibration_curve.points:
                run_audit_for_category(record, "校准曲线")

            items = []
            for cat in ["仪器条件", "空白检验", "质控样", "平行样", "计算", "测定范围"]:
                items.extend(run_audit_for_category(record, cat))
            st.session_state.audit_results["分析结果"] = items

            st.markdown("### 📋 审核结果")
            from ui.components import render_audit_results
            render_audit_results(items)

    # --- Tab 4: 审核报告 ---
    elif tab == "4. 📋 审核报告":
        st.header("4. 综合审核报告")

        if st.session_state.full_report is None:
            st.info("请先同步记录数据（在各Tab页中点击审核按钮录入），然后在左侧边栏点击 **🔄 执行全部审核**。")
            with st.expander("📊 当前审核状态"):
                for k, v in st.session_state.audit_results.items():
                    st.markdown(f"**{k}**: {len(v)} 项结果")
        else:
            report = st.session_state.full_report

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.download_button(
                    "📥 下载审核报告 (JSON)",
                    data=json.dumps({
                        "items": [{
                            "code": i.code, "category": i.category,
                            "name": i.name, "status": i.status.value,
                            "actual_value": i.actual_value,
                            "limit_value": i.limit_value,
                            "hj_ref": i.hj_ref, "detail": i.detail,
                            "suggestion": i.suggestion,
                        } for i in report.items],
                        "summary": {
                            "pass": report.pass_count,
                            "fail": report.fail_count,
                            "warning": report.warning_count,
                            "info": report.info_count,
                            "overall_pass": report.overall_pass,
                            "verdict": report.overall_verdict,
                        }
                    }, ensure_ascii=False, indent=2),
                    file_name=f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )
            show_report(report)


if __name__ == "__main__":
    main()
