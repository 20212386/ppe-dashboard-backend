import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import date

st.set_page_config(
    page_title="PPE 안전관리 대시보드",
    layout="wide"
)

API_BASE_URL = "http://127.0.0.1:8000"


# =========================
# API
# =========================
def fetch_today_dashboard(target_date=None, site=None):
    try:
        params = {}
        if target_date:
            params["target_date"] = str(target_date)
        if site:
            params["site"] = site

        res = requests.get(f"{API_BASE_URL}/dashboard/today", params=params, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"API 연결 실패: {e}")
        return None


# =========================
# 보조 함수
# =========================
def make_empty_time_df():
    return pd.DataFrame([
        {"time": "오전", "count": 0},
        {"time": "점심직후", "count": 0},
        {"time": "오후", "count": 0},
    ])


def get_zone_color(risk: float) -> str:
    if risk >= 80:
        return "#ef4444"
    if risk >= 60:
        return "#f97316"
    if risk >= 40:
        return "#eab308"
    return "#22c55e"


def build_safety_points(weakest_zone_name, most_missing_ppe_name, priority_task_text):
    points = []

    if weakest_zone_name and weakest_zone_name != "-":
        points.append(f"{weakest_zone_name} 구역 집중 순찰 강화")

    if most_missing_ppe_name and most_missing_ppe_name != "-":
        points.append(f"{most_missing_ppe_name} 착용 여부 작업 전 재확인")

    if priority_task_text and priority_task_text != "-":
        points.append(f"{priority_task_text} 작업 전 사전 점검 강화")

    if not points:
        points.append("오늘은 위반 데이터가 없어 전반적으로 양호합니다.")

    return points[:3]


def build_ai_summary(report_date, weakest_zone_name, weakest_zone_score, most_missing_ppe_name, priority_task_text):
    items = []

    if weakest_zone_name and weakest_zone_name != "-":
        items.append(f"{report_date} 기준 가장 취약한 구역은 {weakest_zone_name}이며 해당 구역 내 위반비율은 {weakest_zone_score}%입니다.")
    else:
        items.append(f"{report_date} 기준 뚜렷한 취약 구역은 감지되지 않았습니다.")

    if most_missing_ppe_name and most_missing_ppe_name != "-":
        items.append(f"반복 누락 PPE는 {most_missing_ppe_name}입니다. 해당 보호구 착용 확인을 우선 강화해야 합니다.")
    else:
        items.append("반복 누락 PPE는 아직 뚜렷하지 않습니다.")

    if priority_task_text and priority_task_text != "-":
        items.append(f"우선 개입 필요 작업은 {priority_task_text}입니다.")
    else:
        items.append("현재 우선 개입 필요 작업은 명확하지 않습니다.")

    return items[:3]


# =========================
# 스타일
# =========================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding-top: 2.4rem;
    padding-bottom: 2rem;
    max-width: 1480px;
}

.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}

.sub-title {
    color: #64748b;
    font-size: 1rem;
    margin-bottom: 0;
}

.header-card {
    background: linear-gradient(135deg, #f8fbff 0%, #eef6ff 100%);
    border: 1px solid #dbeafe;
    border-radius: 22px;
    padding: 20px 24px;
    margin-bottom: 1rem;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 20px 22px;
    min-height: 150px;
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
    font-size: 2.15rem;
    font-weight: 800;
    line-height: 1.05;
    margin-bottom: 10px;
    letter-spacing: -0.03em;
}

.metric-value-md {
    color: #0f172a;
    font-size: 1.45rem;
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

.panel-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    padding: 20px 22px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    margin-bottom: 1rem;
}

.panel-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.8rem;
    letter-spacing: -0.01em;
}

.panel-sub {
    color: #64748b;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}

.alert-box {
    border-radius: 14px;
    padding: 14px 16px;
    border: 1px solid;
    margin-bottom: 12px;
    background: #fff;
}

.alert-title {
    font-size: 0.92rem;
    font-weight: 800;
    margin-bottom: 4px;
}

.alert-desc {
    font-size: 0.84rem;
    line-height: 1.55;
}

.recommend-wrap {
    border-top: 1px solid #e2e8f0;
    padding-top: 14px;
    margin-top: 14px;
}

.recommend-title {
    font-size: 0.8rem;
    color: #64748b;
    margin-bottom: 10px;
    font-weight: 800;
}

.recommend-item {
    font-size: 0.84rem;
    color: #334155;
    margin-bottom: 8px;
}

.ai-card {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1px solid #bfdbfe;
    border-radius: 20px;
    padding: 22px 20px;
}

.ai-head {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
}

.ai-icon-wrap {
    width: 56px;
    height: 56px;
    border-radius: 999px;
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.45rem;
    flex-shrink: 0;
}

.ai-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 2px;
}

.ai-desc {
    font-size: 0.84rem;
    color: #64748b;
}

.ai-list {
    margin: 0;
    padding-left: 1.1rem;
}

.ai-list li {
    color: #1e293b;
    font-size: 0.92rem;
    line-height: 1.65;
    margin-bottom: 8px;
}

.ai-time {
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 렌더 함수
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


def render_alert_box(title, desc, bg, border, title_color, desc_color, icon_symbol):
    st.markdown(
        f"""
        <div class="alert-box" style="background:{bg}; border-color:{border};">
            <div class="alert-title" style="color:{title_color};">{icon_symbol} {title}</div>
            <div class="alert-desc" style="color:{desc_color};">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 헤더
# =========================
st.markdown('<div class="header-card">', unsafe_allow_html=True)

header_left, header_mid1, header_mid2, header_right = st.columns([3.6, 1.4, 1.2, 0.8])

with header_left:
    st.markdown('<div class="main-title">PPE 안전관리 대시보드</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">날짜와 현장 조건에 맞는 안전 현황을 확인하세요</div>',
        unsafe_allow_html=True
    )

with header_mid1:
    selected_date = st.date_input("날짜", value=date.today(), label_visibility="collapsed")

with header_mid2:
    selected_site = st.selectbox(
        "현장 선택",
        ["전체 현장", "현장1", "현장2", "현장3"],
        label_visibility="collapsed"
    )

with header_right:
    st.write("")
    if st.button("새로고침", use_container_width=True):
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)


# =========================
# 데이터 호출
# =========================
api_data = fetch_today_dashboard(selected_date, selected_site)

if api_data:
    report_date = api_data.get("date", str(selected_date))
    report_site = api_data.get("site", selected_site)
    kpi = api_data.get("kpi", {})
    charts = api_data.get("charts", {})

    time_data = pd.DataFrame(charts.get("hourly_violations", []))
    if not time_data.empty:
        time_data = time_data.rename(columns={"time_slot": "time", "count": "count"})
        order = {"오전": 0, "점심직후": 1, "오후": 2}
        time_data["sort"] = time_data["time"].map(order)
        time_data = time_data.sort_values("sort").drop(columns=["sort"])
    else:
        time_data = make_empty_time_df()

    zone_data = pd.DataFrame(charts.get("zone_risk_scores", []))
    if not zone_data.empty:
        zone_data = zone_data.rename(columns={"zone": "zone", "risk_score": "risk"})
        zone_data = zone_data.sort_values("risk", ascending=False)
    else:
        zone_data = pd.DataFrame(columns=["zone", "risk"])
else:
    report_date = str(selected_date)
    report_site = selected_site
    kpi = {}
    time_data = make_empty_time_df()
    zone_data = pd.DataFrame(columns=["zone", "risk"])

compliance_rate_text = kpi.get("compliance_rate_text", "-")
weakest_zone_name = kpi.get("weakest_zone_name") or "-"
weakest_zone_score = kpi.get("weakest_zone_score", 0)
most_missing_ppe_name = kpi.get("most_missing_ppe_name") or "-"
most_missing_ppe_count = kpi.get("most_missing_ppe_count", 0)
priority_task_text = kpi.get("priority_task_text") or "-"

display_safety_points = build_safety_points(
    weakest_zone_name,
    most_missing_ppe_name,
    priority_task_text
)

ai_summary_items = build_ai_summary(
    report_date,
    weakest_zone_name,
    weakest_zone_score,
    most_missing_ppe_name,
    priority_task_text
)

st.caption(f"기준일: {report_date} · 현장: {report_site}")

# =========================
# KPI 카드
# =========================
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    render_metric_card(
        title="위험노출 대비 PPE 준수율",
        value=compliance_rate_text,
        badge_text="실시간 집계",
        accent="#3b82f6",
        badge_bg="#eff6ff",
        badge_fg="#1d4ed8",
        icon_bg="#eff6ff",
        icon_fg="#2563eb",
        icon_symbol="🛡",
        large=True
    )

with kpi2:
    render_metric_card(
        title="오늘 가장 취약한 구역",
        value=weakest_zone_name,
        badge_text=f"위험도 {weakest_zone_score}%",
        accent="#ef4444",
        badge_bg="#fef2f2",
        badge_fg="#b91c1c",
        icon_bg="#fef2f2",
        icon_fg="#dc2626",
        icon_symbol="⚠"
    )

with kpi3:
    render_metric_card(
        title="반복 누락 PPE",
        value=most_missing_ppe_name,
        badge_text=f"{most_missing_ppe_count}회 반복",
        accent="#f97316",
        badge_bg="#fff7ed",
        badge_fg="#c2410c",
        icon_bg="#fff7ed",
        icon_fg="#ea580c",
        icon_symbol="⛑"
    )

with kpi4:
    render_metric_card(
        title="우선 개입 필요 작업",
        value=priority_task_text,
        badge_text="우선 확인",
        accent="#a855f7",
        badge_bg="#faf5ff",
        badge_fg="#7e22ce",
        icon_bg="#faf5ff",
        icon_fg="#9333ea",
        icon_symbol="⏱"
    )

st.write("")

# =========================
# 메인 영역
# =========================
main_col, side_col = st.columns([2.1, 1])

with main_col:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">시간대별 PPE 이탈 건수</div>', unsafe_allow_html=True)

    max_time_count = int(time_data["count"].max()) if not time_data.empty else 0
    time_y_max = max(10, ((max_time_count + 1) // 2 + 1) * 2)

    fig_time = go.Figure()
    fig_time.add_trace(
        go.Bar(
            x=time_data["time"],
            y=time_data["count"],
            marker=dict(
                color=["#3b82f6", "#60a5fa", "#1d4ed8"][:len(time_data)],
                line=dict(color="#2563eb", width=0.5)
            ),
            width=0.42,
            hovertemplate="시간대: %{x}<br>건수: %{y}건<extra></extra>",
        )
    )
    fig_time.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        bargap=0.56,
        xaxis=dict(
            title="",
            tickfont=dict(size=12),
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=12),
            gridcolor="#e2e8f0",
            zeroline=False,
            dtick=2,
            range=[0, time_y_max]
        ),
    )
    try:
        fig_time.update_layout(barcornerradius=8)
    except Exception:
        pass

    st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False}, key="page1_time_chart")
    st.markdown('<div class="panel-sub">시간대별 API 집계 결과입니다 · 눈금 간격 2건 고정</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">작업구역별 위험도</div>', unsafe_allow_html=True)

    fig_zone = go.Figure()
    if not zone_data.empty:
        fig_zone.add_trace(
            go.Bar(
                x=zone_data["risk"],
                y=zone_data["zone"],
                orientation="h",
                marker=dict(
                    color=[get_zone_color(v) for v in zone_data["risk"]],
                    line=dict(color="#ffffff", width=0.4)
                ),
                width=0.44,
                hovertemplate="구역: %{y}<br>위험도: %{x}%<extra></extra>",
            )
        )

    fig_zone.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        bargap=0.42,
        xaxis=dict(
            title="",
            tickfont=dict(size=12),
            gridcolor="#e2e8f0",
            zeroline=False,
            range=[0, 100],
            dtick=20
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=12),
            autorange="reversed",
            showgrid=False
        ),
    )
    try:
        fig_zone.update_layout(barcornerradius=8)
    except Exception:
        pass

    st.plotly_chart(fig_zone, use_container_width=True, config={"displayModeBar": False}, key="page1_zone_chart")
    st.markdown(
        f'<div class="panel-sub">{weakest_zone_name} 위험도 {weakest_zone_score}% · 0~100 기준 고정</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with side_col:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">오늘의 안전개입 포인트</div>', unsafe_allow_html=True)

    if display_safety_points:
        for point in display_safety_points:
            render_alert_box(
                title="안전 포인트",
                desc=point,
                bg="#fef2f2",
                border="#fecaca",
                title_color="#7f1d1d",
                desc_color="#b91c1c",
                icon_symbol="⚠"
            )
    else:
        render_alert_box(
            title="안전 포인트",
            desc="오늘 표시할 안전 포인트가 없습니다.",
            bg="#f8fafc",
            border="#cbd5e1",
            title_color="#334155",
            desc_color="#475569",
            icon_symbol="ℹ"
        )

    st.markdown(
        """
        <div class="recommend-wrap">
            <div class="recommend-title">권장 조치사항</div>
            <div class="recommend-item">• 점심 직후 현장 순찰 강화</div>
            <div class="recommend-item">• 고소작업 전 랜야드 체결 확인</div>
            <div class="recommend-item">• 절단작업 전 장갑 착용 점검</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    ai_list_html = "".join([f"<li>{item}</li>" for item in ai_summary_items])

    st.markdown('<div class="ai-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ai-head">
            <div class="ai-icon-wrap">🧠</div>
            <div>
                <div class="ai-title">AI 안전 분석</div>
                <div class="ai-desc">실시간 패턴 분석 기반 요약</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(f'<ul class="ai-list">{ai_list_html}</ul>', unsafe_allow_html=True)
    st.markdown('<div class="ai-time">마지막 업데이트: 방금 전</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)