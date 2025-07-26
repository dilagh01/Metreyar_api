📁 backend/main.py (FastAPI با CORS فعال)

from fastapi import FastAPI, File, UploadFile from fastapi.middleware.cors import CORSMiddleware from fastapi.responses import FileResponse from typing import List from pathlib import Path import shutil import pytesseract from PIL import Image from fpdf import FPDF from openpyxl import Workbook import os import uuid

app = FastAPI()

فعال‌سازی CORS برای GitHub Pages

app.add_middleware( CORSMiddleware, allow_origins=["https://dilagh01.github.io"], allow_credentials=True, allow_methods=[""], allow_headers=[""], )

UPLOAD_FOLDER = "uploaded_images" RESULT_FOLDER = "results" os.makedirs(UPLOAD_FOLDER, exist_ok=True) os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.post("/ocr") async def perform_ocr(files: List[UploadFile] = File(...)): extracted_texts = [] pdf = FPDF() pdf.set_auto_page_break(auto=True, margin=15) wb = Workbook() ws = wb.active ws.title = "OCR Results" ws.append(["Filename", "Extracted Text"])

for file in files:
    unique_id = str(uuid.uuid4())
    extension = Path(file.filename).suffix
    filename = f"{unique_id}{extension}"
    filepath = Path(UPLOAD_FOLDER) / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img = Image.open(filepath)
    text = pytesseract.image_to_string(img, lang="fas+eng")
    extracted_texts.append(text)

    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.splitlines():
        pdf.multi_cell(0, 10, line)

    ws.append([filename, text])

pdf_path = Path(RESULT_FOLDER) / "ocr_result.pdf"
pdf.output(str(pdf_path))

excel_path = Path(RESULT_FOLDER) / "ocr_result.xlsx"
wb.save(str(excel_path))

return {"message": "✅ OCR completed", "text": extracted_texts}

📁 lib/widgets/web_document_recognition.dart (Flutter Web)

import 'dart:convert'; import 'dart:html' as html; import 'package:flutter/material.dart'; import 'package:http/http.dart' as http;

class WebDocumentRecognition extends StatefulWidget { const WebDocumentRecognition({super.key});

@override State<WebDocumentRecognition> createState() => _WebDocumentRecognitionState(); }

class _WebDocumentRecognitionState extends State<WebDocumentRecognition> { String result = ''; bool loading = false;

Future<void> pickAndUploadFile() async { final input = html.FileUploadInputElement(); input.accept = 'image/*'; input.click();

input.onChange.listen((e) async {
  final file = input.files!.first;
  final reader = html.FileReader();

  reader.readAsArrayBuffer(file);
  reader.onLoadEnd.listen((event) async {
    setState(() {
      loading = true;
      result = '';
    });

    final data = reader.result as List<int>;
    final multipartFile = http.MultipartFile.fromBytes(
      'files',
      data,
      filename: file.name,
    );

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('https://metreyar-api.onrender.com/ocr'),
    );
    request.files.add(multipartFile);

    try {
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final decoded = jsonDecode(response.body);
        setState(() {
          result = decoded['text'].join("\n\n");
        });
      } else {
        setState(() {
          result = 'خطا: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        result = 'خطای اتصال: $e';
      });
    } finally {
      setState(() {
        loading = false;
      });
    }
  });
});

}

@override Widget build(BuildContext context) { return Center( child: Column( mainAxisAlignment: MainAxisAlignment.center, children: [ ElevatedButton( onPressed: loading ? null : pickAndUploadFile, child: const Text('انتخاب تصویر'), ), const SizedBox(height: 20), if (loading) const CircularProgressIndicator(), if (result.isNotEmpty) Padding( padding: const EdgeInsets.all(16.0), child: Text(result), ), ], ), ); } }

