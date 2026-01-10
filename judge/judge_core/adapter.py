import httpx
from django.conf import settings

class GoJudgeAdapter:
    # 强制指向本地调试端口
    BASE_URL = "http://127.0.0.1:5050"

    @staticmethod
    async def run(payload):
        """发送请求给 Go-Judge"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(f"{GoJudgeAdapter.BASE_URL}/run", json=payload)
                resp.raise_for_status()
                return resp.json()[0]
            except Exception as e:
                return {"status": "System Error", "error": str(e)}

    @staticmethod
    async def cleanup(file_id):
        if not file_id: return
        async with httpx.AsyncClient() as client:
            try:
                await client.delete(f"{GoJudgeAdapter.BASE_URL}/file/{file_id}")
            except:
                pass