from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

# ایجاد پوشه آپلود اگر وجود ندارد
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# روت اصلی
@app.get("/")
async def root():
    return {"message": "Metreyar API"}

# آپلود فایل
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)
    return {
        "filename": file.filename,
        "size": len(contents),
        "message": "File uploaded successfully"
    }

# فرم HTML برای آپلود دستی فایل از مرورگر
@app.get("/upload-form", response_class=HTMLResponse)
async def upload_form():
    return """
    <html>
        <head>
            <title>Upload File - Metreyar API</title>
        </head>
        <body>
            <h1>Upload File</h1>
            <form action="/upload/" enctype="multipart/form-data" method="post">
                <input name="file" type="file">
                <input type="submit">
            </form>
        </body>
    </html>
    """
