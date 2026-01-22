🧪 AI 기반 과학 서술형 평가 시스템

이 프로젝트는 Streamlit, OpenAI GPT, Supabase를 연동하여 학생들의 서술형 답안을 수집하고, AI가 즉각적으로 채점 및 피드백을 제공하며, 데이터를 클라우드 데이터베이스에 저장하는 시스템입니다.

📊 시스템 구조 (Architecture)

      🧑‍🎓 학생 (Student)
             │
             │ 1. 학번 및 답안 입력
             ▼
  ┌──────────────────────────────┐
  │   🖥️ Streamlit Web App       │
  │  (서술형 3문항 문제지)       │
  └──────────┬───────────────────┘
             │
             │ 2. 제출 (Submit)
             ▼
  ┌──────────────────────────────┐       3. 채점 요청        ┌──────────────┐
  │      ⚡ 로직 처리 부         │ ───────────────────────▶│  🤖 OpenAI   │
  │ (유효성 검사 및 데이터 처리) │ ◀───────────────────────│    (GPT-4o)  │
  └──────────┬───────────────────┘       4. 피드백 반환      └──────────────┘
             │
             │ 5. 데이터 저장 (Insert)
             ▼
      ☁️ Supabase (Database)
  (학생 정보, 답안, 피드백 영구 저장)


✨ 주요 기능

학생용 인터페이스:

학번 입력 및 과학 서술형 3문항(기체 운동, 보일 법칙, 열에너지) 답안 작성 폼 제공.

필수 입력값 검증 (빈 칸 방지).

AI 자동 채점 및 피드백:

OpenAI API를 활용하여 사전에 정의된 **채점 기준(Rubric)**에 따라 답안 분석.

O/X 판정 및 200자 이내의 친절한 첨삭 피드백 생성.

데이터베이스 연동:

Supabase 클라우드 DB에 학생의 답안, AI 피드백, 채점 기준 등을 실시간으로 저장.

🛠️ 설치 및 실행 방법 (Setup)

1. 필수 라이브러리 설치

터미널에서 아래 명령어를 입력하여 필요한 패키지를 설치합니다.

pip install streamlit openai supabase


2. Secrets 설정 (.streamlit/secrets.toml)

프로젝트 루트 경로에 .streamlit 폴더를 만들고 그 안에 secrets.toml 파일을 생성하여 API 키를 설정해야 합니다.

# .streamlit/secrets.toml

OPENAI_API_KEY = "sk-..."
SUPABASE_URL = "[https://your-project.supabase.co](https://your-project.supabase.co)"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"


3. 애플리케이션 실행

streamlit run app.py


🗄️ 데이터베이스 스키마 (Supabase)

Supabase의 student_submissions 테이블은 아래와 같은 구조로 데이터가 저장됩니다.

컬럼명 (Column)

설명 (Description)

student_id

학생 학번 (예: 10130)

answer_1~3

학생이 작성한 답안

feedback_1~3

AI가 생성한 피드백 (O/X 포함)

guideline_1~3

채점 당시의 기준 (버전 관리용)

model

사용된 AI 모델명

created_at

제출 시간 (자동 생성)

📝 문제 구성 예시

Q1: 기체 입자들의 운동과 온도의 관계

Q2: 보일 법칙 설명

Q3: 열에너지 이동 3가지 방식 (전도, 대류, 복사)

Created with Streamlit & OpenAI
