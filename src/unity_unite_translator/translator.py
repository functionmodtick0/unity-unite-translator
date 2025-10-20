# translator.py
import urllib.parse
import urllib.request
import time


def translate(text: str, base_url: str = "http://localhost:8000", retry: int = 3, delay: float = 0.5) -> str:
    """
    로컬 번역 서버를 통해 텍스트를 번역합니다.
    
    Args:
        text: 번역할 원문 텍스트
        base_url: 번역 서버 URL (기본값: http://localhost:8000)
        retry: 실패 시 재시도 횟수
        delay: 요청 간 대기 시간(초)
    
    Returns:
        번역된 텍스트. 실패 시 원문 반환
    """
    if not text or not text.strip():
        return text
    
    encoded_text = urllib.parse.quote(text)
    url = f"{base_url}/?text={encoded_text}"
    
    for attempt in range(retry):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    result = response.read().decode('utf-8')
                    time.sleep(delay)  # 서버 부하 방지
                    return result.strip()
        except Exception as e:
            if attempt == retry - 1:
                print(f"번역 실패 ({text[:30]}...): {e}")
                return text
            time.sleep(delay * (attempt + 1))
    
    return text


def translate_batch(texts: list[str], base_url: str = "http://localhost:8000", 
                   batch_size: int = 10, show_progress: bool = True) -> list[str]:
    """
    여러 텍스트를 일괄 번역합니다.
    
    Args:
        texts: 번역할 텍스트 리스트
        base_url: 번역 서버 URL
        batch_size: 진행상황 표시 주기
        show_progress: 진행상황 표시 여부
    
    Returns:
        번역된 텍스트 리스트
    """
    results = []
    total = len(texts)
    
    for i, text in enumerate(texts, 1):
        translated = translate(text, base_url)
        results.append(translated)
        
        if show_progress and i % batch_size == 0:
            print(f"번역 진행: {i}/{total} ({i/total*100:.1f}%)")
    
    if show_progress and total % batch_size != 0:
        print(f"번역 완료: {total}/{total} (100.0%)")
    
    return results
