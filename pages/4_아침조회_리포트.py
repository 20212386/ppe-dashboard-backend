import streamlit as st
import requests
from datetime import date

st.set_page_config(
    page_title="아침조회 리포트",
    layout="wide"
)

API_BASE_URL = "https://ppe-dashboard-backend.onrender.com"


# =========================
# API
# =========================
def fetch_tbm_report(target_date=None):
    try:
        params = {}
        if target_date:
            params["target_date"] = str(target_date)

        res = requests.get(f"{API_BASE_URL}/report/tbm", params=params, timeout=8)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"TBM 리포트 조회 실패: {e}")
        return None


# =========================
# 스타일
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 2.4rem;
    padding-bottom: 2rem;
    max-width: 1480px;
}

.main-title {
    font-size: 2.1rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}

.sub-title {
    color: #64748b;
    font-size: 1rem;
    margin-bottom: 1rem;
}

.section-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    padding: 22px 22px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    margin-bottom: 1rem;
}

.section-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.8rem;
}

.section-sub {
    color: #64748b;
    font-size: 0.86rem;
    margin-bottom: 1rem;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 20px 22px;
    min-height: 145px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}

.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 14px;
}

.metric-label {
    color: #64748b;
    font-size: 0.92rem;
    margin-bottom: 10px;
    font-weight: 600;
}

.metric-value-lg {
    color: #0f172a;
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 10px;
    letter-spacing: -0.03em;
}

.metric-value-md {
    color: #0f172a;
    font-size: 1.5rem;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: 10px;
    letter-spacing: -0.02em;
}

.metric-badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
}

.metric-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.35rem;
    flex-shrink: 0;
}

.script-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 18px;
    padding: 18px;
    color: #334155;
    font-size: 1rem;
    line-height: 1.8;
    white-space: pre-wrap;
}

.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 0;
    border-bottom: 1px solid #f1f5f9;
    font-size: 0.95rem;
}

.stat-row:last-child {
    border-bottom: none;
}

.stat-name {
    color: #64748b;
    font-weight: 700;
}

.stat-value {
    color: #0f172a;
    font-weight: 800;
    font-size: 1.5rem;
}

.check-item {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 10px;
    color: #92400e;
    font-size: 0.92rem;
    line-height: 1.55;
    font-weight: 700;
}

.focus-box {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1px solid #93c5fd;
    border-radius: 18px;
    padding: 18px;
    color: #1e3a8a;
    font-size: 1rem;
    line-height: 1.7;
    font-weight: 700;
}

.stButton > button {
    border-radius: 14px;
    font-weight: 700;
    min-height: 44px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 렌더
# =========================
def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon_bg, icon_fg, icon_symbol, large=False):
    value_class = "metric-value-lg" if large else "metric-value-md"
    st.markdown(
        f"""
        <div class="metric-card" style="border-left:6px solid {accent};">
            <div class="metric-top">
                <div>
                    <div class="metric-label">{title}</div>
                    <div class="{value_class}">{value}</div>
                    <span class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">{badge_text}</span>
                </div>
                <div class="metric-icon" style="background:{icon_bg}; color:{icon_fg};">{icon_symbol}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 헤더
# =========================
st.markdown('<div class="main-title">아침조회 리포트 (TBM Co-pilot)</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">전일 기준 자동 브리핑 리포트와 오늘의 중점 관리 포인트를 확인합니다</div>',
    unsafe_allow_html=True
)

top1, top2 = st.columns([3, 1])
with top1:
    target_date = st.date_input("기준 날짜", value=date.today(), label_visibility="collapsed")
with top2:
    refresh = st.button("새로고침", use_container_width=True)

if refresh:
    st.rerun()


# =========================
# 데이터
# =========================
report_data = fetch_tbm_report(target_date)

if report_data:
    report_date = report_data.get("date", str(target_date))
    kpis = report_data.get("kpis", {})
    stats = report_data.get("stats", {})
    briefing_text = report_data.get("briefing_text", "브리핑 데이터가 없습니다.")
    checklist = report_data.get("checklist", [])
    focus_message = report_data.get("focus_message", "오늘의 중점 관리사항이 없습니다.")
    full_script = report_data.get("full_script", "전체 브리핑 텍스트가 없습니다.")
else:
    report_date = str(target_date)
    kpis = {
        "compliance_rate": 0,
        "top_zone": None,
        "top_ppe": None,
        "top_time": None
    }
    stats = {
        "total_rows": 0,
        "risk_rows": 0,
        "not_worn_rows": 0,
        "normal_rows": 0
    }
    briefing_text = "브리핑 데이터가 없습니다."
    checklist = []
    focus_message = "오늘의 중점 관리사항이 없습니다."
    full_script = "전체 브리핑 텍스트가 없습니다."

compliance_rate = kpis.get("compliance_rate", 0)
top_zone = kpis.get("top_zone") or "-"
top_ppe = kpis.get("top_ppe") or "-"
top_time = kpis.get("top_time") or "-"

st.caption(f"브리핑 기준일: {report_date}")

# =========================
# KPI 카드
# =========================
c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card(
        "전일 준수율",
        f"{compliance_rate}%",
        "전일 기준",
        "#3b82f6",
        "#eff6ff",
        "#1d4ed8",
        "#eff6ff",
        "#2563eb",
        "🛡",
        large=True
    )

with c2:
    render_metric_card(
        "최대 취약구역",
        top_zone,
        "전일 집중구역",
        "#ef4444",
        "#fef2f2",
        "#b91c1c",
        "#fef2f2",
        "#dc2626",
        "📍"
    )

with c3:
    render_metric_card(
        "최다 누락 PPE",
        top_ppe,
        "우선 점검",
        "#f97316",
        "#fff7ed",
        "#c2410c",
        "#fff7ed",
        "#ea580c",
        "⛑"
    )

with c4:
    render_metric_card(
        "최다 주의 시간대",
        top_time,
        "집중 시간대",
        "#a855f7",
        "#faf5ff",
        "#7e22ce",
        "#faf5ff",
        "#9333ea",
        "⏰"
    )

st.write("")


# =========================
# 브리핑 대본 + 통계 요약
# =========================
left_col, right_col = st.columns([2.1, 1])

with left_col:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">핵심 브리핑 대본</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="script-box">{briefing_text}</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">통계 요약</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="stat-row">
            <span class="stat-name">전일 총 데이터</span>
            <span class="stat-value">{stats.get("total_rows", 0)}</span>
        </div>
        <div class="stat-row">
            <span class="stat-name">위험노출</span>
            <span class="stat-value">{stats.get("risk_rows", 0)}</span>
        </div>
        <div class="stat-row">
            <span class="stat-name">PPE 미착용</span>
            <span class="stat-value">{stats.get("not_worn_rows", 0)}</span>
        </div>
        <div class="stat-row">
            <span class="stat-name">정상 착용</span>
            <span class="stat-value">{stats.get("normal_rows", 0)}</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# 체크리스트 + 오늘의 포커스
# =========================
l2, r2 = st.columns([1.6, 2.4])

with l2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">현장 체크리스트</div>', unsafe_allow_html=True)

    if checklist:
        for item in checklist:
            st.markdown(f'<div class="check-item">✓ {item}</div>', unsafe_allow_html=True)
    else:
        st.info("체크리스트 항목이 없습니다.")

    st.markdown('</div>', unsafe_allow_html=True)

with r2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">오늘의 중점 관리사항</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="focus-box">{focus_message}</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# 전체 브리핑 텍스트
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">전체 브리핑 텍스트</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="script-box">{full_script}</div>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)