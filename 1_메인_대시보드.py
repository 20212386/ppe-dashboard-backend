import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="PPE 안전관리 대시보드", page_icon="🦺", layout="wide")

API_BASE = "https://ppe-dashboard-backend.onrender.com"
OPTIONS_URL = f"{API_BASE}/dashboard/options"
SUMMARY_URL = f"{API_BASE}/dashboard/summary"

REQUEST_TIMEOUT = 20

# =========================
# 공통 함수
# =========================
def safe_get(url: str, params: dict | None = None):
    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

def to_df(items):
    if not items:
        return pd.DataFrame()
    return pd.DataFrame(items)

def fmt_pct(v):
    try:
        return f"{float(v):.2f}%"
    except Exception:
        return "-"

def fmt_num(v):
    try:
        if isinstance(v, float):
            return f"{v:.2f}"
        return str(v)
    except Exception:
        return "-"

def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon_bg, icon):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left:6px solid {accent};">
            <div class="metric-top">
                <div style="width:72%;">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">
                        {badge_text}
                    </div>
                </div>
                <div class="metric-icon" style="background:{icon_bg};">
                    {icon}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_point_box(text):
    st.markdown(
        f"""
        <div class="point-box">
            <div class="point-title">⚠️ 안전 포인트</div>
            <div class="point-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def make_vertical_bar(df, x, y, colors):
    if df.empty:
        return None

    fig = px.bar(df, x=x, y=y, text=y)

    fig.update_traces(
        marker_color=colors[:len(df)],
        opacity=0.78,
        width=0.42,
        marker_line_color="rgba(37, 99, 235, 0.25)",
        marker_line_width=1.0,
        textposition="outside"
    )

    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        showlegend=False,
        bargap=0.55,
        xaxis_title="",
        yaxis_title="",
        font=dict(size=13, color="#374151"),
        xaxis=dict(showgrid=False, tickfont=dict(size=13)),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.18)",
            zeroline=False,
            tickfont=dict(size=12),
            dtick=2
        )
    )
    return fig

def make_horizontal_bar(df, x, y, color_col=None):
    if df.empty:
        return None

    if color_col and color_col in df.columns:
        fig = px.bar(
            df,
            x=x,
            y=y,
            color=color_col,
            orientation="h",
            text=x,
            color_discrete_map={
                "danger": "rgba(239,68,68,0.82)",
                "warn": "rgba(245,158,11,0.78)",
                "safe": "rgba(34,197,94,0.75)"
            }
        )
    else:
        fig = px.bar(
            df,
            x=x,
            y=y,
            orientation="h",
            text=x
        )
        fig.update_traces(marker_color="rgba(34,197,94,0.75)")

    fig.update_traces(
        width=0.38,
        marker_line_color="rgba(15,23,42,0.12)",
        marker_line_width=1.0,
        textposition="outside"
    )

    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        showlegend=False,
        bargap=0.62,
        xaxis_title="",
        yaxis_title="",
        font=dict(size=13, color="#374151"),
        xaxis=dict(range=[0, 100], showgrid=False, tickfont=dict(size=12)),
        yaxis=dict(showgrid=False, tickfont=dict(size=13), autorange="reversed")
    )
    return fig

# =========================
# CSS
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 1.2rem;
    max-width: 1650px;
}
.main-title {
    font-size: 34px;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 4px;
}
.main-sub {
    font-size: 16px;
    color: #6b7280;
    margin-bottom: 18px;
}
.metric-card {
    background: rgba(255, 255, 255, 0.92);
    border-radius: 22px;
    padding: 18px 20px;
    border: 1px solid rgba(226, 232, 240, 0.9);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
    min-height: 165px;
}
.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
}
.metric-title {
    font-size: 15px;
    font-weight: 800;
    color: #4b5563;
    margin-bottom: 10px;
}
.metric-value {
    font-size: 27px;
    line-height: 1.15;
    font-weight: 900;
    color: #0f172a;
    word-break: keep-all;
}
.metric-badge {
    margin-top: 12px;
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
}
.metric-icon {
    width: 58px;
    height: 58px;
    border-radius: 16px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 26px;
}
.section-card {
    background: rgba(255, 255, 255, 0.94);
    border-radius: 24px;
    padding: 18px 20px 14px 20px;
    border: 1px solid rgba(226, 232, 240, 0.95);
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
    min-height: 390px;
}
.section-title {
    font-size: 21px;
    font-weight: 900;
    color: #111827;
    margin-bottom: 4px;
}
.section-sub {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 14px;
}
.point-box {
    background: rgba(255, 244, 244, 0.78);
    border: 1px solid rgba(243, 201, 201, 0.85);
    border-radius: 18px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.point-title {
    color: #b91c1c;
    font-size: 15px;
    font-weight: 900;
    margin-bottom: 6px;
}
.point-text {
    color: #b91c1c;
    font-size: 14px;
    font-weight: 700;
    line-height: 1.5;
}
.ai-box {
    background: rgba(255, 255, 255, 0.94);
    border-radius: 24px;
    padding: 18px 20px 16px 20px;
    border: 1px solid rgba(226, 232, 240, 0.95);
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
    min-height: 390px;
}
.ai-title {
    font-size: 21px;
    font-weight: 900;
    color: #111827;
    margin-bottom: 4px;
}
.ai-sub {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 16px;
}
.ai-list li {
    margin-bottom: 12px;
    font-size: 15px;
    color: #374151;
    line-height: 1.65;
    font-weight: 600;
}
.update-text {
    margin-top: 16px;
    color: #6b7280;
    font-size: 15px;
    font-weight: 700;
}
.reco-title {
    font-size: 16px;
    font-weight: 900;
    color: #374151;
    margin-top: 12px;
    margin-bottom: 8px;
}
.base-note {
    margin-top: 8px;
    color: #6b7280;
    font-size: 14px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 제목
# =========================
st.markdown('<div class="main-title">PPE 안전관리 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">날짜와 현장 조건에 맞는 안전 현황을 확인하세요</div>', unsafe_allow_html=True)

# =========================
# 옵션 불러오기
# =========================
options_data, options_err = safe_get(OPTIONS_URL)

if options_err or not options_data:
    st.error(f"옵션 조회 실패: {options_err}")
    st.stop()

available_dates = options_data.get("dates", [])
available_sites = options_data.get("sites", ["전체 현장"])

if not available_dates:
    st.error("백엔드에서 날짜 목록을 받지 못했습니다.")
    st.stop()

if not available_sites:
    available_sites = ["전체 현장"]

default_date = available_dates[-1]
default_site = "전체 현장" if "전체 현장" in available_sites else available_sites[0]

# =========================
# 필터
# =========================
f1, f2, f3 = st.columns([1.25, 1.15, 0.55])

with f1:
    selected_date = st.selectbox("기준일", available_dates, index=len(available_dates)-1)

with f2:
    selected_site = st.selectbox(
        "현장",
        available_sites,
        index=available_sites.index(default_site) if default_site in available_sites else 0
    )

with f3:
    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
    refresh = st.button("새로고침", use_container_width=True)

# =========================
# 요약 데이터 조회
# =========================
params = {"date": selected_date}
if selected_site != "전체 현장":
    params["site"] = selected_site

summary_data, summary_err = safe_get(SUMMARY_URL, params=params)

if summary_err or not summary_data:
    st.error(f"요약 조회 실패: {summary_err}")
    st.stop()

# =========================
# 백엔드 값 파싱
# =========================
cards = summary_data.get("cards", {})
charts = summary_data.get("charts", {})
safety_points = summary_data.get("safety_points", [])
recommendations = summary_data.get("recommendations", [])
ai_summary = summary_data.get("ai_summary", [])
updated_at = summary_data.get("updated_at", "방금 전")

compliance_rate = cards.get("compliance_rate", 0)
weakest_zone = cards.get("weakest_zone", "-")
weakest_zone_risk = cards.get("weakest_zone_risk", 0)
repeated_missing_ppe = cards.get("repeated_missing_ppe", "-")
repeated_missing_count = cards.get("repeated_missing_count", 0)
urgent_time = cards.get("urgent_time", "-")
urgent_zone = cards.get("urgent_zone", "-")

time_chart_df = to_df(charts.get("time_ppe_off", []))
zone_risk_df = to_df(charts.get("zone_risk", []))

# zone_risk color 넣기
if not zone_risk_df.empty and "score" in zone_risk_df.columns:
    def risk_color(v):
        try:
            v = float(v)
            if v >= 70:
                return "danger"
            elif v >= 45:
                return "warn"
            return "safe"
        except Exception:
            return "safe"
    zone_risk_df["risk_color"] = zone_risk_df["score"].apply(risk_color)

# =========================
# KPI 카드
# =========================
c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card(
        "위험노출 대비 PPE 준수율",
        fmt_pct(compliance_rate),
        "실시간 집계",
        "#3b82f6",
        "#eff6ff",
        "#2563eb",
        "#e0e7ff",
        "🛡️"
    )

with c2:
    render_metric_card(
        "오늘 가장 취약한 구역",
        weakest_zone,
        f"위험도 {fmt_pct(weakest_zone_risk)}",
        "#ef4444",
        "#fef2f2",
        "#b91c1c",
        "#fef2f2",
        "⚠️"
    )

with c3:
    render_metric_card(
        "반복 누락 PPE",
        repeated_missing_ppe,
        f"{fmt_num(repeated_missing_count)}회 반복",
        "#f97316",
        "#fff7ed",
        "#c2410c",
        "#fff7ed",
        "🦺"
    )

with c4:
    render_metric_card(
        "우선 개입 필요 작업",
        f"<span style='font-size:23px;'>{urgent_time}</span><br><span style='font-size:23px;'>{urgent_zone}</span>",
        "우선 확인",
        "#a855f7",
        "#faf5ff",
        "#7e22ce",
        "#faf5ff",
        "⏱️"
    )

st.markdown(
    f"<div class='base-note'>기준일: <b>{selected_date}</b> · 현장: <b>{selected_site}</b></div>",
    unsafe_allow_html=True
)

st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

# =========================
# 1행
# =========================
r1c1, r1c2 = st.columns([1.65, 1.0])

with r1c1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">시간대별 PPE 이탈 건수</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">시간대별 API 집계 결과입니다. 눈금 간격 2건 고정</div>', unsafe_allow_html=True)

    if time_chart_df.empty:
        st.info("백엔드에서 시간대별 차트 데이터가 없습니다.")
    else:
        fig_time = make_vertical_bar(
            time_chart_df,
            x="label",
            y="count",
            colors=["rgba(96,165,250,0.78)", "rgba(59,130,246,0.82)", "rgba(37,99,235,0.88)"]
        )
        if fig_time:
            st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False})

    st.markdown('</div>', unsafe_allow_html=True)

with r1c2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">오늘의 안전개입 포인트</div>', unsafe_allow_html=True)

    if not safety_points:
        st.info("백엔드에서 안전 포인트 데이터가 없습니다.")
    else:
        for p in safety_points[:3]:
            render_point_box(str(p))

    st.markdown('<div class="reco-title">권장 조치사항</div>', unsafe_allow_html=True)
    if recommendations:
        st.markdown("<ul style='font-size:15px; color:#374151; line-height:1.7; font-weight:600; padding-left:22px;'>", unsafe_allow_html=True)
        for item in recommendations:
            st.markdown(f"<li>{item}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
    else:
        st.info("백엔드에서 권장 조치사항이 없습니다.")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

# =========================
# 2행
# =========================
r2c1, r2c2 = st.columns([1.25, 1.0])

with r2c1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">작업구역별 위험도</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">구역별 위험 수준을 0~100 기준으로 표시합니다</div>', unsafe_allow_html=True)

    if zone_risk_df.empty:
        st.info("백엔드에서 작업구역별 위험도 데이터가 없습니다.")
    else:
        fig_zone = make_horizontal_bar(zone_risk_df, x="score", y="label", color_col="risk_color")
        if fig_zone:
            st.plotly_chart(fig_zone, use_container_width=True, config={"displayModeBar": False})

    st.markdown('</div>', unsafe_allow_html=True)

with r2c2:
    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.markdown('<div class="ai-title">🧠 AI 안전 분석</div>', unsafe_allow_html=True)
    st.markdown('<div class="ai-sub">실시간 패턴 분석 기반 요약</div>', unsafe_allow_html=True)

    if ai_summary:
        st.markdown('<ul class="ai-list">', unsafe_allow_html=True)
        for line in ai_summary:
            st.markdown(f"<li>{line}</li>", unsafe_allow_html=True)
        st.markdown('</ul>', unsafe_allow_html=True)
    else:
        st.info("백엔드에서 AI 요약 데이터가 없습니다.")

    st.markdown(f'<div class="update-text">마지막 업데이트: {updated_at}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)