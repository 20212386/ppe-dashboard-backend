import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="메인 대시보드", page_icon="🦺", layout="wide")

DATA_PATH = Path("app/data/input_logs.csv")

st.markdown("""
<style>
.block-container {
    padding-top: 1.4rem;
    padding-bottom: 2rem;
}
.metric-card {
    background: #ffffff;
    border-radius: 22px;
    padding: 22px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    border: 1px solid #eef2f7;
    min-height: 150px;
}
.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
}
.metric-title {
    font-size: 17px;
    font-weight: 800;
    color: #334155;
    margin-bottom: 10px;
}
.metric-value {
    font-size: 34px;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.1;
}
.metric-sub {
    margin-top: 12px;
    font-size: 14px;
    font-weight: 700;
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
}
.metric-icon {
    width: 46px;
    height: 46px;
    border-radius: 14px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 22px;
}
.section-card {
    background: #ffffff;
    border-radius: 24px;
    padding: 22px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    border: 1px solid #eef2f7;
    min-height: 320px;
}
.section-title {
    font-size: 26px;
    font-weight: 900;
    color: #111827;
    margin-bottom: 6px;
}
.section-sub {
    font-size: 15px;
    color: #64748b;
    margin-bottom: 18px;
}
.small-note {
    margin-top: 10px;
    color: #475569;
    font-size: 15px;
    font-weight: 600;
}
.bar-row {
    margin-bottom: 16px;
}
.bar-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.bar-label {
    font-size: 15px;
    font-weight: 700;
    color: #334155;
}
.bar-value {
    font-size: 14px;
    font-weight: 800;
    color: #111827;
}
.bar-bg {
    width: 100%;
    height: 14px;
    background: #eef2f7;
    border-radius: 999px;
    overflow: hidden;
}
.bar-fill {
    height: 14px;
    border-radius: 999px;
}
.guide-box {
    border: 1px dashed #e2e8f0;
    border-radius: 18px;
    padding: 18px;
    color: #475569;
    background: #fafafa;
}
</style>
""", unsafe_allow_html=True)


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

    for col in ["date", "time_slot", "site", "zone", "task_type", "missed_ppe", "team", "note"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["is_violated"] = pd.to_numeric(df["is_violated"], errors="coerce").fillna(0).astype(int)

    return df


def render_metric_card(title, value, sub, accent, sub_bg, sub_fg, icon, icon_bg):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left:6px solid {accent};">
            <div class="metric-top">
                <div>
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-sub" style="background:{sub_bg}; color:{sub_fg};">{sub}</div>
                </div>
                <div class="metric-icon" style="background:{icon_bg};">{icon}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_empty(msg="데이터가 없습니다."):
    st.markdown(f'<div class="guide-box">{msg}</div>', unsafe_allow_html=True)


def make_count_df(series):
    if series.empty:
        return pd.DataFrame(columns=["label", "count"])
    vc = series.value_counts()
    return pd.DataFrame({
        "label": vc.index.astype(str),
        "count": vc.values.astype(int)
    })


def render_bar_list(df, color):
    if df.empty:
        render_empty("표시할 데이터가 없습니다.")
        return

    max_count = max(int(df["count"].max()), 1)
    html = ""

    for _, row in df.iterrows():
        label = str(row["label"])
        count = int(row["count"])
        width = max((count / max_count) * 100, 8)

        html += f"""
        <div class="bar-row">
            <div class="bar-head">
                <div class="bar-label">{label}</div>
                <div class="bar-value">{count}</div>
            </div>
            <div class="bar-bg">
                <div class="bar-fill" style="width:{width}%; background:{color};"></div>
            </div>
        </div>
        """

    st.markdown(html, unsafe_allow_html=True)


df = load_input_logs()

st.markdown("## PPE 안전관리 메인 대시보드")
st.caption("입력 로그 기준으로 전체 안전 현황을 보여줍니다.")

if df.empty:
    render_empty("input_logs.csv 데이터가 없습니다.")
    st.stop()

total_logs = len(df)
total_violations = int((df["is_violated"] == 1).sum())
overall_compliance = round(((total_logs - total_violations) / total_logs) * 100, 1) if total_logs > 0 else 0.0

violated_df = df[df["is_violated"] == 1].copy()

if violated_df.empty:
    weakest_zone = "-"
    weakest_zone_count = 0
    most_missing = "-"
    most_missing_count = 0
    hourly_df = pd.DataFrame(columns=["label", "count"])
    zone_df = pd.DataFrame(columns=["label", "count"])
    ppe_df = pd.DataFrame(columns=["label", "count"])
else:
    zone_counts = violated_df["zone"][violated_df["zone"] != ""].value_counts()
    weakest_zone = zone_counts.idxmax() if not zone_counts.empty else "-"
    weakest_zone_count = int(zone_counts.max()) if not zone_counts.empty else 0

    ppe_counts = violated_df["missed_ppe"][violated_df["missed_ppe"] != ""].value_counts()
    most_missing = ppe_counts.idxmax() if not ppe_counts.empty else "-"
    most_missing_count = int(ppe_counts.max()) if not ppe_counts.empty else 0

    time_order = {"오전": 0, "점심직후": 1, "오후": 2}
    hourly_df = make_count_df(violated_df["time_slot"][violated_df["time_slot"] != ""])
    if not hourly_df.empty:
        hourly_df["order"] = hourly_df["label"].map(lambda x: time_order.get(x, 999))
        hourly_df = hourly_df.sort_values(["order", "label"]).drop(columns=["order"]).reset_index(drop=True)

    zone_df = make_count_df(violated_df["zone"][violated_df["zone"] != ""])
    ppe_df = make_count_df(violated_df["missed_ppe"][violated_df["missed_ppe"] != ""])

safety_points = []
if weakest_zone != "-":
    safety_points.append(f"{weakest_zone} 점검 강화 필요")
if most_missing != "-":
    safety_points.append(f"{most_missing} 착용 여부 집중 확인 필요")
if not violated_df.empty and not hourly_df.empty:
    safety_points.append(f"{hourly_df.iloc[0]['label']} 시간대 위반 패턴 확인 필요")
if not safety_points:
    safety_points = ["현재 큰 위반 패턴은 없지만 지속 점검이 필요합니다."]

c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card(
        "전체 준수율",
        f"{overall_compliance}%",
        "종합 안전 수준",
        "#22c55e",
        "#f0fdf4",
        "#166534",
        "✅",
        "#dcfce7"
    )

with c2:
    render_metric_card(
        "전체 점검 건수",
        f"{total_logs}",
        "누적 로그 수",
        "#3b82f6",
        "#eff6ff",
        "#1d4ed8",
        "📋",
        "#dbeafe"
    )

with c3:
    render_metric_card(
        "전체 위반 건수",
        f"{total_violations}",
        "위험 감지",
        "#ef4444",
        "#fef2f2",
        "#b91c1c",
        "🚨",
        "#fee2e2"
    )

with c4:
    render_metric_card(
        "취약 구역",
        weakest_zone,
        f"위반 {weakest_zone_count}건",
        "#f97316",
        "#fff7ed",
        "#c2410c",
        "📍",
        "#ffedd5"
    )

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

r1c1, r1c2 = st.columns(2)

with r1c1:
    st.markdown(
        '<div class="section-card"><div class="section-title">시간대별 위반 현황</div><div class="section-sub">어느 시간대에 위반이 많이 몰리는지 확인합니다</div>',
        unsafe_allow_html=True
    )
    render_bar_list(hourly_df, "#3b82f6")
    st.markdown('</div>', unsafe_allow_html=True)

with r1c2:
    st.markdown(
        '<div class="section-card"><div class="section-title">구역별 위반 현황</div><div class="section-sub">어느 작업구역에 위반이 많이 몰리는지 확인합니다</div>',
        unsafe_allow_html=True
    )
    render_bar_list(zone_df, "#f97316")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown(
        '<div class="section-card"><div class="section-title">누락 PPE 현황</div><div class="section-sub">가장 자주 빠지는 보호구를 확인합니다</div>',
        unsafe_allow_html=True
    )
    render_bar_list(ppe_df, "#8b5cf6")
    st.markdown('</div>', unsafe_allow_html=True)

with r2c2:
    st.markdown(
        '<div class="section-card"><div class="section-title">안전 포인트</div><div class="section-sub">바로 확인할 핵심 요약입니다</div>',
        unsafe_allow_html=True
    )
    for point in safety_points:
        st.markdown(
            f"""
            <div style="margin-bottom:12px; padding:14px 16px; border-radius:16px; background:#f8fafc; border:1px solid #e2e8f0; font-size:15px; font-weight:600; color:#334155;">
                • {point}
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="small-note">가장 많이 누락된 PPE는 <b>{most_missing}</b>이며, 총 <b>{most_missing_count}</b>건입니다.</div>',
    unsafe_allow_html=True
)