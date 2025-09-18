from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import subprocess, tempfile, os

app = FastAPI()

class ExecRequest(BaseModel):
    language: str
    code: str

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/execute")
def execute(req: ExecRequest, auth: str = Header(default="")):
    # kiểm tra key
    if auth != os.environ.get("SECRET_KEY", "YOUR_SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Sai API key")

    if req.language != "python":
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ Python")

    # ghi code ra file tạm và chạy
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(req.code)
        path = f.name

    try:
        # timeout = 90s (1 phút 30 giây)
        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=90
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Code chạy quá 90s, bị dừng.")
    finally:
        try:
            os.remove(path)
        except:
            pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
