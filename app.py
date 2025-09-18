from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import subprocess, tempfile, os

app = FastAPI()

# 🔑 Secret key cố định
SECRET_KEY = "MY_SUPER_SECRET_KEY_2025"

class ExecRequest(BaseModel):
    language: str
    code: str

@app.post("/execute")
def execute(req: ExecRequest, auth: str = Header(default="")):
    # kiểm tra key
    if auth != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Sai API key")

    if req.language != "python":
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ Python")

    # ghi code ra file tạm và chạy
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(req.code)
        path = f.name

    try:
        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=90   # Timeout 90 giây
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    finally:
        try:
            os.remove(path)
        except:
            pass
