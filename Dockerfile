# 1단계: 빌더 스테이지 (쉘이 있는 파이썬 이미지 사용)
FROM python:3.13-slim AS builder

# uv 바이너리만 복사해서 가져오기
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# uv.lock과 pyproject.toml을 복사하여 의존성 설치
COPY pyproject.toml uv.lock ./
# 쉘이 있는 이미지이므로 RUN 명령어가 정상 작동합니다.
RUN uv export --frozen --no-dev -o requirements.txt

# 2단계: 런타임 스테이지 (AWS Lambda 전용 이미지)
FROM public.ecr.aws/lambda/python:3.13

WORKDIR ${LAMBDA_TASK_ROOT}

# 빌더에서 생성된 requirements.txt 복사 및 설치
COPY --from=builder /app/requirements.txt .
RUN pip install -r requirements.txt

# 소스 코드 및 관련 데이터 복사
COPY main.py parrot_data.py ./

# Lambda 핸들러 설정
CMD [ "main.handler" ]