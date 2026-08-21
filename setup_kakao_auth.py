"""최초 1회 로컬에서 실행하는 카카오 OAuth 인증 스크립트.
실행 전 카카오 디벨로퍼스(https://developers.kakao.com)에서:
  1. 애플리케이션 생성 후 REST API 키 확인
  2. 카카오 로그인 활성화, Redirect URI에 http://localhost:8888/oauth 등록
  3. 동의항목에서 '카카오톡 메시지 전송'(talk_message) 활성화
을 먼저 완료해야 한다.
"""
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv

REDIRECT_URI = "http://localhost:8888/oauth"
AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"

_auth_code = {}


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        code = query.get("code", [None])[0]
        _auth_code["code"] = code
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("인증 완료. 이 창은 닫으셔도 됩니다.".encode("utf-8"))

    def log_message(self, format, *args):
        pass  # 콘솔 로그 억제


def main():
    load_dotenv()
    rest_api_key = os.environ.get("KAKAO_REST_API_KEY") or input("카카오 REST API 키 입력: ").strip()
    client_secret = os.environ.get("KAKAO_CLIENT_SECRET") or input(
        "Client Secret (보안 미사용이면 그냥 엔터): "
    ).strip()

    auth_url = (
        f"{AUTHORIZE_URL}?client_id={rest_api_key}"
        f"&redirect_uri={REDIRECT_URI}&response_type=code&scope=talk_message"
    )
    print(f"브라우저를 열어 카카오 로그인을 진행합니다:\n{auth_url}")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8888), _CallbackHandler)
    server.handle_request()  # 콜백 1회 수신 후 종료

    code = _auth_code.get("code")
    if not code:
        print("인증 코드를 받지 못했습니다. 다시 시도해주세요.")
        return

    data = {
        "grant_type": "authorization_code",
        "client_id": rest_api_key,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    if client_secret:
        data["client_secret"] = client_secret
    resp = requests.post(TOKEN_URL, data=data, timeout=10)
    if resp.status_code != 200:
        print(f"토큰 교환 실패: {resp.status_code} {resp.text}")
        return
    tokens = resp.json()

    print("\n인증 성공. 아래 값을 GitHub repo Settings > Secrets and variables > Actions 에 등록하세요.")
    print(f"KAKAO_REST_API_KEY = {rest_api_key}")
    print(f"KAKAO_REFRESH_TOKEN = {tokens['refresh_token']}")
    if client_secret:
        print(f"KAKAO_CLIENT_SECRET = {client_secret}")


if __name__ == "__main__":
    main()
