import uvicorn

if __name__ == "__main__":
    print("🚀 FastAPI 서버를 시작합니다...")
    # main.py 안에 있는 app 실행
    uvicorn.run("main:app", host="0.0.0.0", port=9100)