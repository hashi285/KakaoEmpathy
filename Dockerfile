# 1. AWS Lambda 파이썬 3.12 이미지
FROM public.ecr.aws/lambda/python:3.12

# 2. 작업 디렉토리 설정
WORKDIR ${LAMBDA_TASK_ROOT}

# 3. 모든 소스 파일 복사 (main.py, parrot_data.py 등 전체)
COPY . .

# 4. 필수 라이브러리 설치 (parrot_data에서 쓰는 추가 라이브러리가 있다면 여기에 추가하세요)
RUN pip install mcp mangum uvicorn

# 5. 실행 핸들러 (파일명.함수명)
CMD [ "main.handler" ]