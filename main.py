#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import tempfile
import uuid
import yaml
import json
from datetime import datetime

# Import existing resume generation functions
from generate_resume import (
    load_resume_data, 
    generate_latex_resume, 
    compile_latex,
    escape_latex,
    format_contact_links,
    format_skills,
    format_experience,
    format_education,
    format_awards,
    format_certifications,
    format_publications
)

# Initialize FastAPI app
app = FastAPI(
    title="YAML to PDF Resume Builder API",
    description="A FastAPI service to generate professional PDF resumes from structured data",
    version="1.0.0",
    docs_url="/docs",  # Explicitly set docs URL
    redoc_url="/redoc",  # Explicitly set redoc URL
    openapi_url="/openapi.json"  # Explicitly set OpenAPI schema URL
)

# Add CORS middleware to ensure docs can load properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ContactLink(BaseModel):
    name: str
    url: str

class Contact(BaseModel):
    phone: str
    email: str
    location: str
    links: List[ContactLink]

class Skill(BaseModel):
    category: str
    items: str

class Achievement(BaseModel):
    name: str
    description: str

class Experience(BaseModel):
    title: str
    company: str
    company_url: Optional[str] = None
    company_description: Optional[str] = None
    location: str
    date_start: str
    date_end: str
    achievements: Optional[List[Achievement]] = None

class Education(BaseModel):
    degree: str
    institution: str
    location: str
    date_start: str
    date_end: str

class Award(BaseModel):
    title: str
    organization: str
    organization_detail: Optional[str] = None
    organization_url: Optional[str] = None
    location: str
    date: str

class Certification(BaseModel):
    title: str
    organization: str
    url: str
    date: str

class Publication(BaseModel):
    authors: str
    title: str
    venue: str
    year: str
    url: str

class ResumeData(BaseModel):
    name: str
    contact: Contact
    summary: str
    skills: List[Skill]
    experience: List[Experience]
    education: List[Education]
    awards: Optional[List[Award]] = []
    certifications: Optional[List[Certification]] = []
    publications: Optional[List[Publication]] = []

class GenerateResumeResponse(BaseModel):
    message: str
    filename: str
    download_url: str

# Create a temporary directory for generated files
TEMP_DIR = os.path.join(tempfile.gettempdir(), "resume_builder")
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return JSONResponse(content={
        "message": "YAML to PDF Resume Builder API",
        "version": "1.0.0",
        "status": "running",
        "documentation": {
            "swagger_ui": "https://yaml2pdf-resume-builder.fly.dev/docs",
            "redoc": "https://yaml2pdf-resume-builder.fly.dev/redoc",
            "openapi_schema": "https://yaml2pdf-resume-builder.fly.dev/openapi.json"
        },
        "endpoints": {
            "health_check": "GET /health",
            "generate_resume": "POST /generate-resume",
            "upload_yaml": "POST /upload-yaml", 
            "generate_from_yaml": "POST /generate-from-yaml",
            "download_file": "GET /download/{filename}",
            "get_template": "GET /template",
            "get_sample_data": "GET /sample-data",
            "cleanup_temp": "DELETE /cleanup"
        }
    }, status_code=200)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Basic health check information
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "resume-builder-api",
            "version": "1.0.0",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc", 
                "openapi_schema": "/openapi.json"
            },
            "environment": {
                "temp_dir_exists": os.path.exists(TEMP_DIR),
                "template_file_exists": os.path.exists("template.tex"),
                "resume_yaml_exists": os.path.exists("resume.yaml")
            }
        }
        
        return JSONResponse(content=health_data, status_code=200)
    
    except Exception as e:
        error_data = {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "resume-builder-api",
            "error": str(e)
        }
        return JSONResponse(content=error_data, status_code=500)

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the API is responding"""
    return JSONResponse(content={
        "message": "Test endpoint working!",
        "timestamp": datetime.now().isoformat(),
        "status": "ok"
    }, status_code=200)

@app.post("/generate-resume", response_model=GenerateResumeResponse)
async def generate_resume(resume_data: ResumeData):
    """
    Generate a PDF resume from structured resume data
    """
    try:
        # Use fixed filename for simplicity
        filename = "resume"
        
        # Convert Pydantic models to dict for compatibility with existing functions
        data_dict = resume_data.model_dump()
        
        # Set output directory to temp directory
        original_output_dir = os.environ.get('OUTPUT_DIR', '.')
        os.environ['OUTPUT_DIR'] = TEMP_DIR
        
        # Generate LaTeX file
        latex_path = os.path.join(TEMP_DIR, f"{filename}.tex")
        generate_latex_resume(data_dict, output_path=latex_path)
        
        # Compile to PDF - need to ensure template files are accessible
        # Copy template.tex to temp directory for compilation
        import shutil
        template_temp_path = os.path.join(TEMP_DIR, 'template.tex')
        if not os.path.exists(template_temp_path):
            shutil.copy2('template.tex', template_temp_path)
        
        pdf_path = compile_latex(latex_path, data=data_dict)
        
        # Restore original output directory
        os.environ['OUTPUT_DIR'] = original_output_dir
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        # Also save copies in the root directory for easy access
        import shutil
        root_tex_path = "resume.tex"
        root_pdf_path = "resume.pdf"
        
        if os.path.exists(latex_path):
            shutil.copy2(latex_path, root_tex_path)
            print(f"Copied LaTeX file to: {root_tex_path}")
        
        if os.path.exists(pdf_path):
            shutil.copy2(pdf_path, root_pdf_path)
            print(f"Copied PDF file to: {root_pdf_path}")
        
        return GenerateResumeResponse(
            message="Resume generated successfully",
            filename="resume.pdf",
            download_url="/download/resume.pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating resume: {str(e)}")

@app.post("/upload-yaml", response_model=GenerateResumeResponse)
async def upload_yaml_resume(file: UploadFile = File(...)):
    """
    Upload a YAML file and generate a PDF resume
    """
    try:
        if not file.filename.endswith(('.yaml', '.yml')):
            raise HTTPException(status_code=400, detail="File must be a YAML file (.yaml or .yml)")
        
        # Save uploaded file temporarily
        upload_path = os.path.join(TEMP_DIR, f"upload_{uuid.uuid4()}.yaml")
        
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Load data from YAML file
        data_dict = load_resume_data(upload_path)
        
        # Use fixed filename for simplicity
        filename = "resume"
        
        # Set output directory
        original_output_dir = os.environ.get('OUTPUT_DIR', '.')
        os.environ['OUTPUT_DIR'] = TEMP_DIR
        
        # Generate LaTeX and PDF
        latex_path = os.path.join(TEMP_DIR, f"{filename}.tex")
        generate_latex_resume(data_dict, output_path=latex_path)
        
        # Ensure template files are accessible for compilation
        import shutil
        template_temp_path = os.path.join(TEMP_DIR, 'template.tex')
        if not os.path.exists(template_temp_path):
            shutil.copy2('template.tex', template_temp_path)
        
        pdf_path = compile_latex(latex_path, data=data_dict)
        
        # Restore original output directory
        os.environ['OUTPUT_DIR'] = original_output_dir
        
        # Clean up uploaded YAML file
        os.remove(upload_path)
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        # Also save copies in the root directory for easy access
        import shutil
        root_tex_path = "resume.tex"
        root_pdf_path = "resume.pdf"
        
        if os.path.exists(latex_path):
            shutil.copy2(latex_path, root_tex_path)
            print(f"Copied LaTeX file to: {root_tex_path}")
        
        if os.path.exists(pdf_path):
            shutil.copy2(pdf_path, root_pdf_path)
            print(f"Copied PDF file to: {root_pdf_path}")
        
        return GenerateResumeResponse(
            message="Resume generated successfully from uploaded YAML",
            filename="resume.pdf",
            download_url="/download/resume.pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing YAML file: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download generated PDF files
    """
    file_path = os.path.join(TEMP_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=filename
    )

@app.get("/template")
async def get_template():
    """
    Get the LaTeX template content for reference
    """
    try:
        with open('template.tex', 'r') as f:
            template_content = f.read()
        
        return {
            "template": template_content,
            "message": "LaTeX template content"
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template file not found")

@app.get("/sample-data")
async def get_sample_data():
    """
    Get sample resume data structure for reference
    """
    try:
        sample_data = load_resume_data('resume.yaml')
        return {
            "sample_data": sample_data,
            "message": "Sample resume data structure"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading sample data: {str(e)}")

# Cleanup endpoint (optional - for development)
@app.delete("/cleanup")
async def cleanup_temp_files():
    """
    Clean up temporary files (development endpoint)
    """
    try:
        files_removed = 0
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                files_removed += 1
        
        return {
            "message": f"Cleaned up {files_removed} temporary files",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up files: {str(e)}")

@app.post("/generate-from-yaml", response_model=GenerateResumeResponse)
async def generate_from_existing_yaml():
    """
    Generate resume.tex and resume.pdf from the existing resume.yaml file in the project directory
    """
    try:
        yaml_file_path = "resume.yaml"
        
        # Check if resume.yaml exists
        if not os.path.exists(yaml_file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"resume.yaml file not found in project directory. Please ensure resume.yaml exists in the project root."
            )
        
        # Load data from existing YAML file
        data_dict = load_resume_data(yaml_file_path)
        
        # Generate LaTeX file directly in the project root
        latex_path = "resume.tex"
        generate_latex_resume(data_dict, output_path=latex_path)
        
        # Compile to PDF directly in the project root
        # Set OUTPUT_DIR to current directory for this operation
        original_output_dir = os.environ.get('OUTPUT_DIR', '.')
        os.environ['OUTPUT_DIR'] = '.'
        
        pdf_path = compile_latex(latex_path, data=data_dict)
        
        # Restore original output directory
        os.environ['OUTPUT_DIR'] = original_output_dir
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        # Also copy files to temp directory for download endpoint compatibility
        import shutil
        temp_tex_path = os.path.join(TEMP_DIR, "resume.tex")
        temp_pdf_path = os.path.join(TEMP_DIR, "resume.pdf")
        
        if os.path.exists(latex_path):
            shutil.copy2(latex_path, temp_tex_path)
            print(f"Copied LaTeX file to temp directory: {temp_tex_path}")
        
        if os.path.exists(pdf_path):
            shutil.copy2(pdf_path, temp_pdf_path)
            print(f"Copied PDF file to temp directory: {temp_pdf_path}")
        
        return GenerateResumeResponse(
            message="Resume generated successfully from existing resume.yaml",
            filename="resume.pdf",
            download_url="/download/resume.pdf"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating resume from YAML: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 