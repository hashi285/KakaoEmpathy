# 1. uv가 설치된 가벼운 파이썬 이미지 사용
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 파일 복사 및 설치 (캐싱 활용)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 4. 소스 코드 복사
COPY . .

# 5. 실행 환경 설정 (uv로 설치된 패키지 경로 인식)
ENV PATH="/app/.venv/bin:$PATH"

# 6. 포트 설정 (App Runner 기본 포트와 맞춤)
EXPOSE 8000

# 7. 서버 실행 (host와 port 명시)
CMD ["python", "main.py"]