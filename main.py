from typing import Union

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from rembg import remove
from pydantic import BaseModel
import base64
from functools import partial
import asyncio

app = FastAPI()

# CORS 미들웨어 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용. 실제 운영 환경에서는 특정 도메인만 지정하는 것이 좋습니다
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)


@app.get("/")
def read_root():
    return {"Hello": "World"}

# remove_background 함수를 비동기로 실행하도록 수정
async def async_remove_background(input_data: bytes) -> bytes:
    """
    이미지의 배경을 제거하는 비동기 함수
    """
    try:
        # 동기 함수를 비동기로 실행
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(None, partial(remove, input_data, force_return_bytes=True))
        return output
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        raise e

# base64 입력을 위한 모델 정의
class ImageInput(BaseModel):
    image: str  # base64 encoded string

@app.post("/remove-bg")
async def remove_bg(image_input: ImageInput):
    """
    Base64로 인코딩된 이미지를 받아서 배경을 제거하고 결과를 반환하는 엔드포인트
    """
    try:
        # base64 문자열에서 prefix 제거 (만약 있다면)
        if ',' in image_input.image:
            image_input.image = image_input.image.split(',')[1]

        # base64 디코딩하여 바이너리 데이터로 변환
        image_bytes = base64.b64decode(image_input.image)

        # 비동기로 배경 제거 실행
        output_data = await async_remove_background(image_bytes)  # 바이트 데이터 전달

        # 결과를 base64로 인코딩하여 반환
        output_base64 = base64.b64encode(output_data).decode('utf-8')

        return {
            "status": "success",
            "image": output_base64
        }

    except Exception as e:
        print(e)
        return {"status": "error", "message": f"배경 제거 중 오류가 발생했습니다: {str(e)}"}
