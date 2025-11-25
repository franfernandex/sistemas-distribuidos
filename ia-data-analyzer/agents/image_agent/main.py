from fastapi import FastAPI, UploadFile, File
import easyocr
import cv2
import numpy as np
import pandas as pd
import logging
import os

app = FastAPI(title="Image Agent")
logger = logging.getLogger(__name__)
reader = easyocr.Reader(['pt'])

@app.post("/extract_data_from_image")
async def extract_data_from_image(file: UploadFile = File(...)):
    """Extrai dados numéricos de imagens de gráficos/tabelas"""
    try:
        # Lê imagem
        image_data = await file.read()
        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        
        # Usa OCR para extrair texto
        results = reader.readtext(image)
        
        # Filtra apenas números
        extracted_numbers = []
        for (bbox, text, confidence) in results:
            # Tenta converter para número
            try:
                num = float(text.replace(',', '.'))
                extracted_numbers.append(num)
            except ValueError:
                continue
        
        # Cria DataFrame com dados extraídos
        df = pd.DataFrame({
            'extracted_value': extracted_numbers,
            'data_type': 'numeric_from_image'
        })
        
        # Salva em CSV
        output_filename = f"extracted_data_{file.filename.split('.')[0]}.csv"
        output_path = f"/app/shared/{output_filename}"
        df.to_csv(output_path, index=False)
        
        return {
            "status": "success",
            "numbers_extracted": len(extracted_numbers),
            "extracted_file": output_filename,
            "sample_data": extracted_numbers[:5]  # Primeiros 5 valores
        }
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
