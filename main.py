from playwright.async_api import async_playwright
import os
import tempfile
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
import uvicorn
import uuid
import re
from pathlib import Path

app = FastAPI(title="NFS-e PDF Generator")

CODE_PATTERN = re.compile(r'^[A-Za-z0-9]+$')

@app.get("/nfse/sp/pdf")
async def generate_nfse_pdf(
    ccm: int = Query(..., description="CCM number", gt=0, le=99999999),
    nf: int = Query(..., description="NF number", gt=0, le=999999999),
    cod: str = Query(
        ..., 
        description="Verification code", 
        min_length=1, 
        max_length=20,
        regex='^[A-Za-z0-9]+$'
    )
):
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / f"nfe_{uuid.uuid4()}.pdf"
        pdf_content = None
        
        try:
            async with async_playwright() as p:            
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                page = await browser.new_page()
                
                url = f"https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx?ccm={ccm}&nf={nf}&cod={cod}"
                response = await page.goto(url)
                
                if response.status != 200:
                    raise HTTPException(
                        status_code=404,
                        detail="Unable to retrieve the NFe. Please verify the provided information."
                    )
                
                await page.wait_for_load_state('networkidle')
                
                await page.pdf(path=str(pdf_path), format="A4")
                
                await browser.close()
                
                if pdf_path.is_file():
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_content = pdf_file.read()
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Error generating PDF document"
                    )
                
                return Response(
                    content=pdf_content,
                    media_type='application/pdf',
                    headers={
                        'Content-Disposition': f'attachment; filename=nfse_{ccm}_{nf}.pdf',
                        'X-Content-Type-Options': 'nosniff',
                        'Cache-Control': 'no-store'
                    }
                )
                
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing your request"
            )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=None,
        ssl_certfile=None
    ) 