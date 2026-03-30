import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="데이터 입력",
    layout="wide"
)

DATA_PATH = Path("app/data/input_logs.csv")

# =========================
# 유틸
# =========================
EXPECTED_COLUMNS = [
    "date",
    "time_slot",
    "site",
    "zone",
    "task_type",
    "missed_ppe",
    "is_violated",
    "team",
    "note",
]

def ensure_data_file():
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        pd.DataFrame(columns=EXPECTED_COLUMNS).to_csv(DATA_PATH, index=False, encoding="utf-8-sig")

def load_data() -> pd.DataFrame:
    ensure_data_file()
    try:
        df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(DATA_PATH)

    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[EXPECTED_COLUMNS].copy()
    return df

def save_data(df: pd.DataFrame):
    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")

def normalize_uploaded_df(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work.columns = [str(c).strip() for c in work.columns]

    # 컬럼명 호환
    rename_map = {
        "time": "time_slot",
        "ppe_type": "missed_ppe",
        "worker_id": "team",   # 혹시 잘못 들어와도 빈값 대체용
        "site_name": "site",
    }
    work = work.rename(columns=rename_map)

    # 없는 컬럼 채우기
    for col in EXPECTED_COLUMNS:
        if col not in work.columns:
            work[col] = ""

    # 값 정리
    work["date"] = work["date"].astype(str).str.strip()
    work["time_slot"] = work["time_slot"].astype(str).str.strip()
    work["site"] = work["site"].astype(str).str.strip()
    work["zone"] = work["zone"].astype(str).str.strip()
    work["task_type"] = work["task_type"].astype(str).str.strip()
    work["missed_ppe"] = work["missed_ppe"].astype(str).str.strip()
    work["team"] = work["team"].astype(str).str.strip()
    work["note"] = work["note"].astype(str).str.strip()

    # site 통일
    work["site"] = (
        work["site"]
        .str.replace("현장 1", "현장1", regex=False)
        .str.replace("현장 2", "현장2", regex=False)
        .str.replace("현장 3", "현장3", regex=False)
    )

    # missed_ppe 정리
    work["missed_ppe"] = work["missed_ppe"].replace({
        "None": "",
        "nan": "",
        "NaN": "",
    })

    # is_violated 자동 정리
    def to_violated(v):
        s = str(v).strip()
        if s in ["1", "1.0", "True", "true"]:
            return 1
        if s in ["0", "0.0", "False", "false"]:
            return 0
        return None

    parsed = work["is_violated"].apply(to_violated)
    auto_calc = work["missed_ppe"].apply(lambda x: 0 if str(x).strip() == "" else 1)
    work["is_violated"] = parsed.fillna(auto_calc).astype(int)

    return work[EXPECTED_COLUMNS].copy()

def make_manual_row(date_value, time_slot, site, zone, task_type, missed_ppe, team, note):
    missed_ppe = str(missed_ppe).strip()
    is_violated = 0 if missed_ppe == "" or missed_ppe == "정상 착용" else 1

    if missed_ppe == "정상 착용":
        missed_ppe = ""

    return pd.DataFrame([{
        "date": str(date_value),
        "time_slot": time_slot,
        "site": site,
        "zone": zone,
        "task_type": task_type,
        "missed_ppe": missed_ppe,
        "is_violated": is_violated,
        "team": team,
        "note": note,
    }])

def summary_metrics(df: pd.DataFrame):
    total_count = len(df)
    violated_count = int((df["is_violated"] == 1).sum()) if not df.empty else 0
    normal_count = total_count - violated_count
    today_count = 0

    if not df.empty and "date" in df.columns:
        today_str = str(pd.Timestamp.today().date())
        today_count = int((df["date"].astype(str) == today_str).sum())

    return total_count, today_count, violated_count, normal_count


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
    font-size: 2.05rem;
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
    padding: 22px;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
    margin-bottom: 1rem;
}

.section-title {
    font-size: 1.12rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.5rem;
}

.help-box {
    border: 1px dashed #cbd5e1;
    background: #f8fafc;
    border-radius: 16px;
    padding: 16px;
    color: #475569;
    font-size: 0.9rem;
    line-height: 1.6;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 18px 18px;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
    margin-bottom: 0.8rem;
}

.metric-label {
    color: #64748b;
    font-size: 0.9rem;
    font-weight: 700;
    margin-bottom: 8px;
}

.metric-value {
    color: #0f172a;
    font-size: 1.9rem;
    font-weight: 800;
    line-height: 1;
}

.stButton > button {
    border-radius: 14px;
    font-weight: 800;
    min-height: 44px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 데이터 로드
# =========================
df = load_data()
total_count, today_count, violated_count, normal_count = summary_metrics(df)

# =========================
# 헤더
# =========================
st.markdown('<div class="main-title">데이터 입력</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">CSV 업로드 또는 수기 입력으로 PPE 로그 데이터를 통합 관리합니다</div>',
    unsafe_allow_html=True
)

left, right = st.columns([2.2, 1])

# =========================
# 좌측: 업로드 + 입력
# =========================
with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">CSV 파일 업로드</div>', unsafe_allow_html=True)
    st.caption("업로드한 CSV는 app/data/input_logs.csv 기준으로 저장됩니다.")

    uploaded_file = st.file_uploader(
        "CSV 파일 선택",
        type=["csv"],
        label_visibility="collapsed"
    )

    st.markdown(
        """
        <div class="help-box">
            <b>예시 컬럼 구조</b><br>
            date,time_slot,site,zone,task_type,missed_ppe,is_violated,team,note
            <br><br>
            <b>예시 값</b><br>
            2026-03-24,오후,현장1,고소작업구역,고소작업,랜야드,1,A팀,업로드 테스트
        </div>
        """,
        unsafe_allow_html=True
    )

    if uploaded_file is not None:
        try:
            upload_df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except Exception:
            upload_df = pd.read_csv(uploaded_file)

        normalized_df = normalize_uploaded_df(upload_df)

        st.write("업로드 미리보기")
        st.dataframe(normalized_df.head(10).astype(str).astype(object), use_container_width=True)

        if st.button("업로드 데이터 저장", use_container_width=True):
            current_df = load_data()
            merged_df = pd.concat([current_df, normalized_df], ignore_index=True)
            save_data(merged_df)
            st.success("CSV 데이터가 기존 데이터에 추가 저장되었습니다.")
            st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">수기 데이터 입력</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    c5, c6 = st.columns(2)
    c7, c8 = st.columns(2)

    with c1:
        manual_date = st.date_input("날짜")
    with c2:
        manual_time_slot = st.selectbox("시간대", ["오전", "점심직후", "오후"])

    with c3:
        manual_site = st.selectbox("현장", ["현장1", "현장2", "현장3"])
    with c4:
        manual_team = st.selectbox("팀", ["A팀", "B팀", "C팀", "D팀"])

    with c5:
        manual_zone = st.selectbox("작업구역", ["고소작업구역", "절단작업구역", "자재운반구역", "설비점검구역"])
    with c6:
        manual_task_type = st.selectbox("작업유형", ["고소작업", "절단작업", "자재운반", "설비점검"])

    with c7:
        manual_missed_ppe = st.selectbox("누락 PPE", ["정상 착용", "장갑", "안전모", "랜야드"])
    with c8:
        # 💡 [핵심] 여기에 아이디 껍데기를 추가했습니다! 기능은 없고 간지만 납니다.
        dummy_worker_id = st.text_input("작업자 ID", placeholder="예 : W-1234")

    # 💡 [핵심] 비고 칸을 밖으로 빼서 전체 가로 너비를 꽉 채우게 만들었습니다!
    manual_note = st.text_input("비고", placeholder="추가 메모 입력")

    if st.button("수기 입력 저장", use_container_width=True):
        new_row = make_manual_row(
            date_value=manual_date,
            time_slot=manual_time_slot,
            site=manual_site,
            zone=manual_zone,
            task_type=manual_task_type,
            missed_ppe=manual_missed_ppe,
            team=manual_team,
            note=manual_note,
        )

        merged_df = pd.concat([df, new_row], ignore_index=True)
        save_data(merged_df)
        st.success("수기 입력 데이터가 저장되었습니다.")
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">데이터 미리보기</div>', unsafe_allow_html=True)
    st.caption("최근 20건 기준입니다.")
    preview_df = df.tail(20).iloc[::-1] if not df.empty else df
    st.dataframe(preview_df.astype(str).astype(object), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 우측: 요약
# =========================
with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">데이터 상태 요약</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">총 데이터 건수</div>
            <div class="metric-value">{total_count}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">오늘 데이터</div>
            <div class="metric-value">{today_count}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">위험 데이터</div>
            <div class="metric-value">{violated_count}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">정상 데이터</div>
            <div class="metric-value">{normal_count}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)