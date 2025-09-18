# app.py
import os
import tempfile
import uuid
import subprocess
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

SECRET = os.getenv("SECRET_KEY", "")  # set trên Zeabur

app = FastAPI(title="GPT Exec OR-Tools", version="1.0.0")

class ExecRequest(BaseModel):
    language: str = "python"
    code: str
    timeout_sec: Optional[int] = 20  # server sẽ giới hạn tối đa 30s

@app.get("/healthz")
def healthz():
    return {"ok": True, "time": datetime.utcnow().isoformat() + "Z"}

@app.post("/execute")
def execute(req: ExecRequest, auth: str = Header(default="")):
    # 1) Auth kiểm tra khóa
    if not SECRET or auth != SECRET:
        raise HTTPException(status_code=401, detail="Sai hoặc thiếu API key (header 'auth')")

    # 2) Chỉ cho Python
    if req.language.lower() != "python":
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ language='python'")

    # 3) Ghi code ra file tạm
    file_id = uuid.uuid4().hex
    path = os.path.join(tempfile.gettempdir(), f"exec_{file_id}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(req.code)

    # 4) Chạy code với timeout
    # Lưu ý: Đây là môi trường sandbox cơ bản (timeout). Không cho chạy lâu.
    # Nếu code nặng hãy tối ưu/giới hạn trong GPT.
    t = min(max(1, req.timeout_sec or 1), 300)  # 1..30s
    try:
        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=t,
            check=False,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "ran_at": datetime.utcnow().isoformat() + "Z",
            "time_limit_sec": t,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "returncode": None,
            "stdout": e.stdout or "",
            "stderr": f"TIMEOUT after {t}s",
            "ran_at": datetime.utcnow().isoformat() + "Z",
            "time_limit_sec": t,
        }
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
