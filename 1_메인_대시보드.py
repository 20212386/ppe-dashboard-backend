import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

st.set_page_config(page_title="PPE 안전관리 대시보드", page_icon="🦺", layout="wide")

DATA_PATH = Path("app/data/input_logs.csv")

# =========================
# 스타일
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1800px;
}

.main-title {
    font-size: 42px;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 6px;
}
.main-sub {
    font-size: 18px;
    color: #6b7280;
    margin-bottom: 26px;
}

.metric-card {
    background: #ffffff;
    border-radius: 26px;
    padding: 24px 26px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    min-height: 210px;
}
.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}
.metric-title {
    font-size: 18px;
    font-weight: 800;
    color: #4b5563;
    margin-bottom: 18px;
}
.metric-value {
    font-size: 40px;
    line-height: 1.1;
    font-weight: 900;
    color: #0f172a;
    word-break: keep-all;
}
.metric-badge {
    margin-top: 18px;
    display: inline-block;
    padding: 9px 14px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 800;
}
.metric-icon {
    width: 72px;
    height: 72px;
    border-radius: 18px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 34px;
}

.section-card {
    background: #ffffff;
    border-radius: 28px;
    padding: 26px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    min-height: 520px;
}
.section-title {
    font-size: 28px;
    font-weight: 900;
    color: #111827;
    margin-bottom: 8px;
}
.section-sub {
    font-size: 16px;
    color: #6b7280;
    margin-bottom: 22px;
}
.sub-card {
    background: #fff;
    border-radius: 24px;
    padding: 22px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}
.point-box {
    background: #fff4f4;
    border: 1px solid #f3c9c9;
    border-radius: 22px;
    padding: 18px 20px;
    margin-bottom: 16px;
}
.point-title {
    color: #b91c1c;
    font-size: 17px;
    font-weight: 900;
    margin-bottom: 8px;
}
.point-text {
    color: #b91c1c;
    font-size: 16px;
    font-weight: 700;
}

.reco-title {
    font-size: 18px;
    font-weight: 900;
    color: #374151;
    margin-top: 18px;
    margin-bottom: 12px;
}
.ai-box {
    background: #ffffff;
    border-radius: 28px;
    padding: 26px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    min-height: 520px;
}
.ai-title {
    font-size: 24px;
    font-weight: 900;
    color: #111827;
    margin-bottom: 6px;
}
.ai-sub {
    font-size: 16px;
    color: #6b7280;
    margin-bottom: 28px;
}
.ai-list li {
    margin-bottom: 18px;
    font-size: 18px;
    color: #374151;
    line-height: 1.7;
    font-weight: 600;
}
.update-text {
    margin-top: 28px;
    color: #6b7280;
    font-size: 18px;
    font-weight: 700;
}
.base-note {
    margin-top: 12px;
    color: #6b7280;
    font-size: 15px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 데이터 로드
# =========================
@st.cache_data
def load_input_logs():
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=[
            "date", "time_slot", "site", "zone", "task_type",
            "missed_ppe", "is_violated", "team", "note"
        ])

    df = pd.read_csv(DATA_PATH)

    required_cols = [
        "date", "time_slot", "site", "zone", "task_type",
        "missed_ppe", "is_violated", "team", "note"
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

    df = df[required_cols].copy()

    text_cols = ["date", "time_slot", "site", "zone", "task_type", "missed_ppe", "team", "note"]
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["is_violated"] = pd.to_numeric(df["is_violated"], errors="coerce").fillna(0).astype(int)

    # 날짜 포맷 통일
    parsed = pd.to_datetime(df["date"], errors="coerce")
    df["date"] = parsed.dt.strftime("%Y-%m-%d").fillna(df["date"])

    return df


def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon, icon_bg):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left:7px solid {accent};">
            <div class="metric-top">
                <div style="width:75%;">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">{badge_text}</div>
                </div>
                <div class="metric-icon" style="background:{icon_bg};">{icon}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def make_bar_chart(df, x, y, color_seq, title=""):
    fig = px.bar(
        df,
        x=x,
        y=y,
        text=y
    )
    fig.update_traces(
        marker_color=color_seq,
        textposition="outside"
    )
    fig.update_layout(
        height=430,
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis_title="",
        yaxis_title="",
        font=dict(size=16),
        yaxis=dict(showgrid=True, gridcolor="#e5e7eb", zeroline=False),
        xaxis=dict(showgrid=False)
    )
    return fig


def make_horizontal_bar(df, x, y, color_col):
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation="h",
        color=color_col,
        color_discrete_map={
            "danger": "#ef4444",
            "warn": "#f59e0b",
            "safe": "#22c55e"
        },
        text=x
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=470,
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis_title="",
        yaxis_title="",
        font=dict(size=16),
        xaxis=dict(range=[0, 100], showgrid=False),
        yaxis=dict(showgrid=False, autorange="reversed")
    )
    return fig


# =========================
# 기본 계산
# =========================
df = load_input_logs()

st.markdown('<div class="main-title">PPE 안전관리 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">날짜와 현장 조건에 맞는 안전 현황을 확인하세요</div>', unsafe_allow_html=True)

if df.empty:
    st.warning("input_logs.csv 데이터가 없습니다.")
    st.stop()

all_dates = sorted([d for d in df["date"].unique().tolist() if d != ""])
default_date = all_dates[-1] if all_dates else ""
site_options = ["전체 현장"] + sorted([s for s in df["site"].unique().tolist() if s != ""])

f1, f2, f3 = st.columns([1.25, 1.15, 0.5])

with f1:
    selected_date = st.selectbox("기준일", all_dates, index=len(all_dates)-1 if all_dates else 0)
with f2:
    selected_site = st.selectbox("현장", site_options, index=0)
with f3:
    st.write("")
    st.write("")
    if st.button("새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

filtered_df = df[df["date"] == selected_date].copy()
if selected_site != "전체 현장":
    filtered_df = filtered_df[filtered_df["site"] == selected_site].copy()

violated_df = filtered_df[filtered_df["is_violated"] == 1].copy()

total_count = len(filtered_df)
violated_count = len(violated_df)
compliance_rate = round(((total_count - violated_count) / total_count) * 100, 2) if total_count > 0 else 0.0

# 취약 구역
zone_stats = []
for zone in sorted([z for z in filtered_df["zone"].unique().tolist() if z != ""]):
    zone_df = filtered_df[filtered_df["zone"] == zone]
    if len(zone_df) == 0:
        continue
    rate = round((zone_df["is_violated"].sum() / len(zone_df)) * 100, 2)
    zone_stats.append({"zone": zone, "risk_rate": rate, "count": len(zone_df)})

zone_stats_df = pd.DataFrame(zone_stats)

if not zone_stats_df.empty:
    weakest_zone_row = zone_stats_df.sort_values(["risk_rate", "count"], ascending=[False, False]).iloc[0]
    weakest_zone = weakest_zone_row["zone"]
    weakest_zone_rate = weakest_zone_row["risk_rate"]
else:
    weakest_zone = "-"
    weakest_zone_rate = 0.0

# 반복 누락 PPE
if not violated_df.empty and (violated_df["missed_ppe"] != "").any():
    ppe_counts = violated_df[violated_df["missed_ppe"] != ""]["missed_ppe"].value_counts()
    top_ppe = ppe_counts.index[0]
    top_ppe_count = int(ppe_counts.iloc[0])
else:
    top_ppe = "-"
    top_ppe_count = 0

# 우선 개입 필요 작업
if not violated_df.empty:
    combo = violated_df.groupby(["time_slot", "zone"]).size().reset_index(name="count")
    combo = combo.sort_values("count", ascending=False)
    urgent_time = combo.iloc[0]["time_slot"]
    urgent_zone = combo.iloc[0]["zone"]
else:
    urgent_time = "-"
    urgent_zone = "-"

# =========================
# KPI 카드
# =========================
c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card(
        "위험노출 대비 PPE 준수율",
        f"{compliance_rate}%",
        "실시간 집계",
        "#3b82f6",
        "#eff6ff",
        "#1d4ed8",
        "🛡️",
        "#e0e7ff"
    )

with c2:
    render_metric_card(
        "오늘 가장 취약한 구역",
        weakest_zone,
        f"위험도 {weakest_zone_rate:.2f}%",
        "#ef4444",
        "#fef2f2",
        "#b91c1c",
        "⚠️",
        "#fef2f2"
    )

with c3:
    render_metric_card(
        "반복 누락 PPE",
        top_ppe,
        f"{top_ppe_count}회 반복",
        "#f97316",
        "#fff7ed",
        "#c2410c",
        "🦺",
        "#fff7ed"
    )

with c4:
    render_metric_card(
        "우선 개입 필요 작업",
        f"{urgent_time}<br>{urgent_zone}",
        "우선 확인",
        "#a855f7",
        "#faf5ff",
        "#7e22ce",
        "⏱️",
        "#faf5ff"
    )

st.markdown(
    f'<div class="base-note">기준일: {selected_date} · 현장: {selected_site}</div>',
    unsafe_allow_html=True
)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
line1, line2 = st.columns(2)
with line1:
    st.markdown('<div style="height:1px; background:#e5e7eb; margin:0 0 16px 0;"></div>', unsafe_allow_html=True)
with line2:
    st.markdown('<div style="height:1px; background:#e5e7eb; margin:0 0 16px 0;"></div>', unsafe_allow_html=True)

# =========================
# 2행: 시간대별 / 안전개입
# =========================
left, right = st.columns([1.55, 1])

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">시간대별 PPE 이탈 건수</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">시간대별 API 집계 결과입니다. 눈금 간격 2건 고정</div>', unsafe_allow_html=True)

    if violated_df.empty:
        st.info("위반 데이터가 없습니다.")
    else:
        time_order = ["오전", "점심직후", "오후"]
        time_counts = violated_df["time_slot"].value_counts().reindex(time_order, fill_value=0).reset_index()
        time_counts.columns = ["time_slot", "count"]
        fig_time = make_bar_chart(
            time_counts,
            "time_slot",
            "count",
            ["#4a86e8", "#6aa2ec", "#2f59d9"]
        )
        fig_time.update_layout(yaxis=dict(dtick=2, gridcolor="#e5e7eb"))
        st.plotly_chart(fig_time, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">오늘의 안전개입 포인트</div>', unsafe_allow_html=True)

    safety_messages = []

    if not violated_df.empty:
        danger_combo = violated_df.groupby(["time_slot", "zone", "missed_ppe"]).size().reset_index(name="count")
        danger_combo = danger_combo.sort_values("count", ascending=False)

        for _, row in danger_combo.head(3).iterrows():
            ppe_text = row["missed_ppe"] if str(row["missed_ppe"]).strip() != "" else "보호구"
            safety_messages.append(f"{row['time_slot']} {row['zone']}에서 {ppe_text} 미착용이 증가했습니다.")

    if not safety_messages:
        safety_messages = [
            "오늘은 뚜렷한 위험 집중 패턴이 없습니다.",
            "기본 PPE 착용 상태를 계속 유지하세요.",
            "현장 순찰은 현재 수준으로 유지하면 됩니다."
        ]

    for msg in safety_messages[:3]:
        st.markdown(
            f"""
            <div class="point-box">
                <div class="point-title">⚠️ 안전 포인트</div>
                <div class="point-text">{msg}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:1px; background:#e5e7eb; margin:8px 0 18px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="reco-title">권장 조치사항</div>', unsafe_allow_html=True)

    recommendations = []
    if "점심직후" in violated_df["time_slot"].values:
        recommendations.append("점심 직후 현장 순찰 강화")
    if "랜야드" in violated_df["missed_ppe"].values:
        recommendations.append("고소작업 전 랜야드 체결 확인")
    if "장갑" in violated_df["missed_ppe"].values:
        recommendations.append("절단작업 전 장갑 착용 점검")
    if "안전모" in violated_df["missed_ppe"].values:
        recommendations.append("설비/운반 작업 전 안전모 착용 재확인")

    if not recommendations:
        recommendations = ["현재는 기본 PPE 준수 상태 유지"]

    st.markdown("<ul style='font-size:18px; color:#374151; line-height:1.9; font-weight:600;'>", unsafe_allow_html=True)
    for rec in recommendations[:4]:
        st.markdown(f"<li>{rec}</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
line3, line4 = st.columns(2)
with line3:
    st.markdown('<div style="height:1px; background:#e5e7eb; margin:0 0 16px 0;"></div>', unsafe_allow_html=True)
with line4:
    st.markdown('<div style="height:1px; background:#e5e7eb; margin:0 0 16px 0;"></div>', unsafe_allow_html=True)

# =========================
# 3행: 작업구역별 위험도 / AI 분석
# =========================
left2, right2 = st.columns([1.55, 1])

with left2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">작업구역별 위험도</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">구역별 위험 수준을 0~100 기준으로 표시합니다</div>', unsafe_allow_html=True)

    if zone_stats_df.empty:
        st.info("위험도 데이터가 없습니다.")
    else:
        risk_df = zone_stats_df.sort_values("risk_rate", ascending=False).copy()

        def risk_class(x):
            if x >= 70:
                return "danger"
            elif x >= 45:
                return "warn"
            else:
                return "safe"

        risk_df["risk_class"] = risk_df["risk_rate"].apply(risk_class)

        fig_risk = make_horizontal_bar(
            risk_df,
            "risk_rate",
            "zone",
            "risk_class"
        )
        st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

with right2:
    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.markdown('<div class="ai-title">🧠 AI 안전 분석</div>', unsafe_allow_html=True)
    st.markdown('<div class="ai-sub">실시간 패턴 분석 기반 요약</div>', unsafe_allow_html=True)

    ai_lines = []

    if weakest_zone != "-":
        ai_lines.append(f"{selected_date} 기준 가장 취약한 구역은 {weakest_zone}이며 해당 구역 내 위반비율은 {weakest_zone_rate:.2f}%입니다.")
    if top_ppe != "-":
        ai_lines.append(f"반복 누락 PPE는 {top_ppe}입니다. 해당 보호구 착용 확인을 우선 강화해야 합니다.")
    if urgent_time != "-" and urgent_zone != "-":
        ai_lines.append(f"우선 개입 필요 작업은 {urgent_time} {urgent_zone}입니다.")
    if not ai_lines:
        ai_lines.append("현재는 뚜렷한 반복 위반 패턴이 없습니다.")

    st.markdown("<ul class='ai-list'>", unsafe_allow_html=True)
    for line in ai_lines:
        st.markdown(f"<li>{line}</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)

    st.markdown('<div class="update-text">마지막 업데이트: 방금 전</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)