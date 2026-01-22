"""
교사용 대시보드 - teacher.py (Supabase 버전)
─────────────────────────────────────────────────────────────────
• student_submissions 테이블 실시간 모니터링
• "새로고침" 버튼 → 최신 데이터 즉시 갱신
• 학번(부분) 검색, 최근 N일 필터, CSV 다운로드
• 통계: 총 제출 수, 고유 학생 수, 문항별 정답(O) 비율
• 개인별 피드백 조회: 특정 학번의 제출 이력 상세 확인

[실행 전 필수 설정]
1. .streamlit/secrets.toml 파일에 아래 내용이 있어야 합니다.
   [SUPABASE_URL]
   value = "본인의_SUPABASE_URL"
   
   [SUPABASE_SERVICE_ROLE_KEY]
   value = "본인의_SUPABASE_KEY"
   
2. 패키지 설치: pip install streamlit pandas supabase
"""

import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# --------------------------------------------------------------------------------
# 1. UI 및 보안 설정
# --------------------------------------------------------------------------------
st.set_page_config(page_title="교사용 대시보드", layout="wide")

# 간단한 비밀번호 보호 기능 (실제 운영 시 더 강력한 보안 권장)
with st.sidebar:
    st.header("🔒 관리자 인증")
    password = st.text_input("교사 인증 암호", type="password")
    
    if password != "1234":  # 원하는 비밀번호로 변경하세요
        st.warning("선생님만 접근할 수 있습니다.")
        st.info("암호를 입력하세요.")
        st.stop()  # 암호가 틀리면 여기서 코드 실행 중단
    else:
        st.success("인증되었습니다.")

# --------------------------------------------------------------------------------
# 2. Supabase 연결 설정
# --------------------------------------------------------------------------------
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Supabase 연결 설정 오류: secrets.toml을 확인해주세요.")
        st.stop()

# --------------------------------------------------------------------------------
# 3. 데이터 로드 함수 (캐싱 적용)
# --------------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=30)
def fetch_data(search_id: str, days: int) -> pd.DataFrame:
    """전체 데이터 조회 (필터 적용)"""
    try:
        supabase = get_supabase_client()

        # 쿼리 빌더 시작
        q = (
            supabase.table("student_submissions")
            .select(
                "id, student_id, answer_1, answer_2, answer_3, "
                "feedback_1, feedback_2, feedback_3, model, created_at"
            )
        )

        # 학번 부분 검색 (대소문자 무시)
        if search_id:
            q = q.ilike("student_id", f"%{search_id}%")

        # 최근 N일 필터 (created_at 기준)
        if days and days > 0:
            # UTC 기준으로 계산 (Supabase는 기본적으로 UTC 저장)
            date_from = datetime.now(timezone.utc) - timedelta(days=int(days))
            q = q.gte("created_at", date_from.isoformat())

        # 최신순 정렬
        q = q.order("created_at", desc=True)

        res = q.execute()
        rows = res.data or []
        df = pd.DataFrame(rows)

        # 날짜 형식 변환
        if not df.empty and "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

        return df

    except Exception as e:
        st.error(f"데이터 조회 오류: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=30)
def fetch_student_history(student_id: str, limit: int = 200) -> pd.DataFrame:
    """특정 학번의 전체 제출 이력 조회"""
    try:
        supabase = get_supabase_client()
        q = (
            supabase.table("student_submissions")
            .select(
                "id, student_id, answer_1, answer_2, answer_3, "
                "feedback_1, feedback_2, feedback_3, model, created_at"
            )
            .eq("student_id", student_id)
            .order("created_at", desc=True)
            .limit(limit)
        )
        res = q.execute()
        rows = res.data or []
        df = pd.DataFrame(rows)
        
        if not df.empty and "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
            
        return df
    except Exception as e:
        st.error(f"개인 이력 조회 오류: {e}")
        return pd.DataFrame()

# --------------------------------------------------------------------------------
# 4. 메인 UI 레이아웃
# --------------------------------------------------------------------------------
st.title("📊 서술형 평가 교사 대시보드")
st.markdown("학생들의 제출 현황을 실시간으로 모니터링하고 피드백을 분석합니다.")

# 필터링 및 컨트롤 영역
with st.container(border=True):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_id = st.text_input("🔍 학번 검색 (부분 일치)", value="", placeholder="예: 2024")
    with col2:
        days = st.number_input("📅 최근 조회 기간(일)", min_value=0, max_value=365, value=30, step=1)
    with col3:
        st.write("") # 줄맞춤용 공백
        if st.button("🔄 데이터 새로고침", use_container_width=True, type="primary"):
            st.cache_data.clear()

# 데이터 로드
df = fetch_data(search_id=search_id.strip(), days=int(days))

# --------------------------------------------------------------------------------
# 5. 통계 대시보드
# --------------------------------------------------------------------------------
st.markdown("### 📈 전체 현황 요약")

if df.empty:
    st.info("⚠️ 조건에 해당하는 데이터가 없습니다. 검색 조건을 변경하거나 새로고침 해보세요.")
else:
    # 기본 통계 계산
    unique_students = df["student_id"].nunique() if "student_id" in df.columns else 0
    latest_time = df["created_at"].max() if "created_at" in df.columns else None

    # 상단 지표 카드
    m1, m2, m3 = st.columns(3)
    m1.metric("총 제출 건수", f"{len(df)}건")
    m2.metric("참여 학생 수", f"{unique_students}명")
    
    latest_str = latest_time.strftime('%Y-%m-%d %H:%M') if latest_time is not None else "-"
    m3.metric("최근 제출 시각", latest_str)

    # 문항별 정답률 계산 함수 (feedback이 'O:'로 시작하면 정답으로 간주)
    def calculate_o_rate(series: pd.Series) -> float:
        if series is None or series.empty:
            return 0.0
        s = series.fillna("").astype(str)
        # 대소문자 구분 없이 'o:' 체크하려면 lower() 사용 가능, 여기선 명세대로 "O:"만 체크
        count_o = s.str.strip().str.startswith("O:").sum()
        return (count_o / len(s)) * 100.0

    r1 = calculate_o_rate(df.get("feedback_1"))
    r2 = calculate_o_rate(df.get("feedback_2"))
    r3 = calculate_o_rate(df.get("feedback_3"))

    st.markdown("#### ✅ 문항별 정답(Pass) 비율")
    s1, s2, s3 = st.columns(3)
    s1.metric("문항 1 정답률", f"{r1:.1f}%", help="피드백이 'O:'로 시작하는 비율")
    s2.metric("문항 2 정답률", f"{r2:.1f}%")
    s3.metric("문항 3 정답률", f"{r3:.1f}%")

    # --------------------------------------------------------------------------------
    # 6. 전체 목록 데이터프레임
    # --------------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📄 전체 제출 목록")

    # 표시할 컬럼 정의 및 정리
    cols_to_show = [
        "student_id", "created_at",
        "answer_1", "feedback_1",
        "answer_2", "feedback_2",
        "answer_3", "feedback_3",
        "model"
    ]
    # 실제 데이터에 있는 컬럼만 필터링
    valid_cols = [c for c in cols_to_show if c in df.columns]
    
    # 데이터프레임 표시
    st.dataframe(
        df[valid_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "created_at": st.column_config.DatetimeColumn("제출 일시", format="YYYY-MM-DD HH:mm"),
            "student_id": "학번",
            "model": "사용 모델"
        }
    )

    # CSV 다운로드 버튼
    csv_data = df[valid_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 전체 데이터 CSV 다운로드",
        data=csv_data,
        file_name=f"submissions_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

    # --------------------------------------------------------------------------------
    # 7. 개인별 상세 이력 조회
    # --------------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🔎 개인별 피드백 상세 조회")
    
    col_sel, col_empty = st.columns([1, 2])
    with col_sel:
        # 현재 조회된 데이터에 있는 학생 목록 추출
        student_list = sorted(df["student_id"].dropna().astype(str).unique().tolist())
        selected_student = st.selectbox("학생 선택 (학번)", options=["선택하세요"] + student_list)

    if selected_student and selected_student != "선택하세요":
        # 개별 이력 조회 함수 호출
        history_df = fetch_student_history(selected_student)
        
        st.write(f"**📌 {selected_student} 학생의 전체 제출 이력 ({len(history_df)}건)**")
        
        if history_df.empty:
            st.info("조회된 이력이 없습니다.")
        else:
            # 보기 좋게 컬럼 순서 재배치
            hist_cols = [
                "created_at",
                "answer_1", "feedback_1",
                "answer_2", "feedback_2",
                "answer_3", "feedback_3",
                "model"
            ]
            valid_hist_cols = [c for c in hist_cols if c in history_df.columns]
            
            st.dataframe(
                history_df[valid_hist_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "created_at": st.column_config.DatetimeColumn("제출 일시", format="YYYY-MM-DD HH:mm:ss")
                }
            )
