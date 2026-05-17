import streamlit as st
from models.audit_result import AuditItem, AuditReport, AuditStatus


def status_badge(status: AuditStatus) -> str:
    """返回状态对应的HTML徽章"""
    colors = {
        AuditStatus.PASS: ("#d4edda", "#155724", "✅"),
        AuditStatus.FAIL: ("#f8d7da", "#721c24", "❌"),
        AuditStatus.WARNING: ("#fff3cd", "#856404", "⚠️"),
        AuditStatus.INFO: ("#cce5ff", "#004085", "ℹ️"),
    }
    bg, fg, icon = colors.get(status, ("#e2e3e5", "#383d41", "?"))
    return (f'<span style="display:inline-block;padding:2px 10px;'
            f'border-radius:12px;background:{bg};color:{fg};'
            f'font-size:13px;font-weight:600;white-space:nowrap">'
            f'{icon} {status.value}</span>')


def render_audit_item(item: AuditItem):
    """渲染单个审核项"""
    st.markdown(f"""
    <div style="border:1px solid #dee2e6;border-radius:8px;padding:12px;margin:6px 0;background:#fff">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-weight:600;font-size:15px">{item.code} {item.name}</span>
            {status_badge(item.status)}
        </div>
        <div style="display:flex;gap:20px;font-size:13px;color:#6c757d;margin-bottom:4px">
            <span>📋 类别: {item.category}</span>
            <span>📖 HJ 535-2009 {item.hj_ref}</span>
        </div>
    """, unsafe_allow_html=True)
    if item.actual_value or item.limit_value:
        st.markdown(f"""
        <div style="font-size:14px;margin:4px 0">
            <span style="color:#666">实际值: </span><b>{item.actual_value or '—'}</b>
            &nbsp;&nbsp;|&nbsp;&nbsp;
            <span style="color:#666">标准要求: </span><b style="color:#0d6efd">{item.limit_value or '—'}</b>
        </div>
        """, unsafe_allow_html=True)
    if item.detail:
        st.markdown(f'<div style="font-size:13px;color:#dc3545;margin:4px 0">📝 {item.detail}</div>',
                    unsafe_allow_html=True)
    if item.suggestion:
        st.markdown(f'<div style="font-size:13px;color:#198754;margin:2px 0">💡 {item.suggestion}</div>',
                    unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_audit_results(items: list):
    """渲染审核结果列表"""
    if not items:
        st.info("暂无审核结果，请先点击审核按钮。")
        return

    by_status = {AuditStatus.FAIL: [], AuditStatus.WARNING: [],
                 AuditStatus.PASS: [], AuditStatus.INFO: []}
    for i in items:
        by_status.setdefault(i.status, []).append(i)

    if by_status[AuditStatus.FAIL]:
        st.error(f"❌ 不合格项: {len(by_status[AuditStatus.FAIL])}")
    if by_status[AuditStatus.WARNING]:
        st.warning(f"⚠️ 警告项: {len(by_status[AuditStatus.WARNING])}")
    if by_status[AuditStatus.PASS]:
        st.success(f"✅ 合格项: {len(by_status[AuditStatus.PASS])}")

    render_order = [AuditStatus.FAIL, AuditStatus.WARNING, AuditStatus.PASS, AuditStatus.INFO]
    for status in render_order:
        for item in by_status.get(status, []):
            render_audit_item(item)


def render_report_summary(report: AuditReport):
    """渲染报告摘要"""
    cols = st.columns(4)
    cols[0].metric("合格", report.pass_count, delta=None)
    cols[1].metric("不合格", report.fail_count,
                   delta="需整改" if report.fail_count > 0 else None,
                   delta_color="inverse")
    cols[2].metric("警告", report.warning_count)
    cols[3].metric("提示", report.info_count)

    if report.overall_pass:
        if report.warning_count == 0:
            st.success(f"## {report.overall_verdict}")
        else:
            st.warning(f"## {report.overall_verdict}")
    else:
        st.error(f"## {report.overall_verdict}")


def record_info_form():
    """通用记录基本信息表单"""
    col1, col2, col3 = st.columns(3)
    with col1:
        analyst = st.text_input("分析人员", key="info_analyst")
        analysis_date = st.date_input("分析日期", key="info_date")
    with col2:
        instrument_model = st.text_input("仪器型号", value="可见分光光度计", key="info_inst_model")
        instrument_id = st.text_input("仪器编号", key="info_inst_id")
    with col3:
        temperature = st.number_input("室温 (℃)", min_value=0.0, max_value=50.0, value=25.0, step=0.5, key="info_temp")
        humidity = st.number_input("相对湿度 (%)", min_value=0, max_value=100, value=55, key="info_humid")
    return analyst, analysis_date, instrument_model, instrument_id, temperature, humidity
