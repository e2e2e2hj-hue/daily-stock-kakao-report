"""카카오 '나에게 보내기' 메시지 발송 및 토큰 관리."""
import base64
import requests
from nacl import encoding, public

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
LINK_URL = "https://finance.naver.com/sise/"  # 카카오 text 템플릿은 link 필드가 필수라 고정 URL 사용


def refresh_access_token(rest_api_key: str, refresh_token: str, client_secret: str = None) -> dict:
    """access_token을 갱신한다. 응답에 refresh_token이 포함되면 회전된 것이므로 호출자가 저장해야 한다."""
    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token,
    }
    if client_secret:
        data["client_secret"] = client_secret
    resp = requests.post(TOKEN_URL, data=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def send_text_message(access_token: str, text: str) -> None:
    if len(text) > 200:
        text = text[:197] + "..."
    template_object = {
        "object_type": "text",
        "text": text,
        "link": {"web_url": LINK_URL, "mobile_web_url": LINK_URL},
    }
    resp = requests.post(
        SEND_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": _to_json(template_object)},
        timeout=10,
    )
    resp.raise_for_status()


def _to_json(obj) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)


def update_github_secret(repo: str, secret_name: str, secret_value: str, pat: str) -> None:
    """refresh_token이 회전됐을 때 GitHub repo secret을 새 값으로 갱신한다."""
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
    }
    key_resp = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers=headers,
        timeout=10,
    )
    key_resp.raise_for_status()
    key_data = key_resp.json()

    public_key = public.PublicKey(key_data["key"], encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

    put_resp = requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}",
        headers=headers,
        json={"encrypted_value": encrypted_b64, "key_id": key_data["key_id"]},
        timeout=10,
    )
    put_resp.raise_for_status()
