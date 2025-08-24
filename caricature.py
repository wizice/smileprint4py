# caricature.py
import os, io, base64, requests
import logging
from PIL import Image
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = "https://api.openai.com/v1/images/edits"

logger.info("캐리커처 모듈 초기화 완료")

def center_square(path, out_size=1024):
    """입력 이미지를 센터 크롭 후 1024x1024로 리사이즈"""
    logger.info(f"이미지 전처리 시작: {path}")
    logger.info(f"목표 크기: {out_size}x{out_size}")
    
    im = Image.open(path).convert("RGB")
    w, h = im.size
    logger.info(f"원본 이미지 크기: {w}x{h}")
    
    s = min(w, h)
    left = (w - s) // 2
    top  = (h - s) // 2
    logger.info(f"센터 크롭 영역: left={left}, top={top}, size={s}x{s}")
    
    im_sq = im.crop((left, top, left + s, top + s)).resize((out_size, out_size), Image.LANCZOS)
    logger.info(f"크롭 및 리사이즈 완료: {out_size}x{out_size}")
    
    buf = io.BytesIO()
    im_sq.save(buf, format="PNG")  # edits는 PNG/JPG 권장
    buf.seek(0)
    
    logger.info(f"이미지 버퍼 생성 완료: {len(buf.getvalue())} bytes")
    return buf

def make_caricature(input_path, out_path="caricature.png", size="1024x1024"):
    logger.info("=" * 50)
    logger.info("캐리커처 생성 시작")
    logger.info(f"입력 파일: {input_path}")
    logger.info(f"출력 파일: {out_path}")
    logger.info(f"출력 크기: {size}")
    
    # 스타일 프롬프트 (핵심)
    prompt = (
        "A simplified colored-pencil caricature of the person in the photo. "
        "Clean contour lines, soft cross-hatching, warm umber/sienna with a bit of blue, "
        "textured off-white paper background. Exaggerate smile lines gently, keep likeness."
    )
    logger.info(f"프롬프트: {prompt[:100]}...")

    logger.info("이미지 전처리 중...")
    img_buf = center_square(input_path, out_size=int(size.split('x')[0]))

    files = {
        # 이미지 편집 엔드포인트는 multipart/form-data 형식.
        # 여러 장을 넣을 때는 image[]를 반복해서 보냅니다.
        "image[]": ("input.png", img_buf, "image/png"),
        # 필요 시 특정 영역만 바꾸려면 "mask": ("mask.png", open(...,"rb"), "image/png")
    }
    data = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": size,
        # 원본과의 닮음을 더 강하게 유지하고 싶을 때(선택):
        "input_fidelity": "high",
        # gpt-image-1은 기본이 base64 응답입니다.
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    logger.info("API 요청 데이터 준비 완료")
    logger.info(f"모델: {data['model']}")
    logger.info(f"입력 충실도: {data['input_fidelity']}")

    logger.info(f"OpenAI API 호출 중... (URL: {API_URL})")
    try:
        resp = requests.post(API_URL, headers=headers, files=files, data=data, timeout=600)
        logger.info(f"API 응답 상태 코드: {resp.status_code}")
        resp.raise_for_status()
        
        payload = resp.json()
        logger.info("API 응답 파싱 완료")
        
        # gpt-image-1 응답: data[0].b64_json
        if "data" in payload and len(payload["data"]) > 0:
            b64 = payload["data"][0]["b64_json"]
            logger.info(f"Base64 이미지 데이터 수신: {len(b64)} characters")
            
            out_bytes = base64.b64decode(b64)
            logger.info(f"디코딩 완료: {len(out_bytes)} bytes")
            
            with open(out_path, "wb") as f:
                f.write(out_bytes)
            logger.info(f"캐리커처 저장 완료: {out_path}")
            logger.info("=" * 50)
            return out_path
        else:
            logger.error(f"예상치 못한 API 응답 형식: {payload}")
            raise ValueError("Invalid API response format")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 실패: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"캐리커처 생성 중 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    # 사용 예: python caricature.py
    logger.info("캐리커처 스크립트 직접 실행")
    file_path_name = os.path.join("img", "yun1.jpg")
    logger.info(f"테스트 이미지: {file_path_name}")
    
    try:
        result = make_caricature(file_path_name, out_path="caricature.png")
        print(f"캐리커처 생성 성공: {result}")
    except Exception as e:
        logger.error(f"메인 실행 오류: {str(e)}")
        print(f"오류 발생: {str(e)}")

