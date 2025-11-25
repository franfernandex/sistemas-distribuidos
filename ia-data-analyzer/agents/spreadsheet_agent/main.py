from fastapi import FastAPI, UploadFile, File
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import logging
import os

app = FastAPI(title="Spreadsheet Agent")
logger = logging.getLogger(__name__)

@app.post("/detect_outliers")
async def detect_outliers(file: UploadFile = File(...)):
    """Detecta outliers em planilha usando Isolation Forest"""
    try:
        # Salva o arquivo temporariamente
        temp_path = f"/app/shared/temp_{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Lê o arquivo
        if file.filename.endswith('.csv'):
            df = pd.read_csv(temp_path)
        else:
            df = pd.read_excel(temp_path)
        
        # Remove colunas não numéricas
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return {"error": "No numeric columns found"}
        
        # Detecta outliers
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        outliers = iso_forest.fit_predict(numeric_df)
        
        # Marca outliers
        df['is_outlier'] = outliers == -1
        
        # Salva resultado
        output_filename = f"cleaned_{file.filename}"
        output_path = f"/app/shared/{output_filename}"
        df.to_csv(output_path, index=False)
        
        # Remove temporário
        os.remove(temp_path)
        
        return {
            "status": "success",
            "outliers_detected": sum(df['is_outlier']),
            "cleaned_file": output_filename
        }
    
    except Exception as e:
        logger.error(f"Error processing {file.filename}: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
