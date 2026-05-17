import streamlit as st
from models.audit_result import AuditReport, AuditStatus
from ui.components import render_report_summary, render_audit_item


def show_report(report: AuditReport):
    """显示综合审核报告"""
    st.header("综合审核报告")
    st.caption(f"审核时间: {report.audit_time}")

    st.markdown("---")
    render_report_summary(report)

    st.markdown("---")
    st.subheader("审核详情（按类别）")

    categories: dict = {}
    for item in report.items:
        categories.setdefault(item.category, []).append(item)

    for cat, items in categories.items():
        cat_fails = sum(1 for i in items if i.status == AuditStatus.FAIL)
        cat_warns = sum(1 for i in items if i.status == AuditStatus.WARNING)
        cat_passes = sum(1 for i in items if i.status == AuditStatus.PASS)
        cat_infos = sum(1 for i in items if i.status == AuditStatus.INFO)

        icon = "✅" if cat_fails == 0 else "❌"
        total = len(items)
        with st.expander(f"{icon} {cat} ({cat_passes}合格 / {cat_fails}不合格 / {cat_warns}警告 / {total}项)",
                         expanded=(cat_fails > 0)):
            for item in items:
                render_audit_item(item)

    st.markdown("---")
    st.subheader("不合格/警告项目汇总")
    issues = [i for i in report.items if i.status in (AuditStatus.FAIL, AuditStatus.WARNING)]
    if not issues:
        st.success("无不合格或警告项目。")
    else:
        for item in issues:
            render_audit_item(item)

    st.markdown("---")
    st.subheader("整改建议汇总")
    suggestions = [i for i in report.items if i.suggestion]
    if not suggestions:
        st.info("无需整改。")
    else:
        for i, item in enumerate(suggestions, 1):
            st.markdown(f"**{i}.** [{item.code}] {item.name}: {item.suggestion}")
