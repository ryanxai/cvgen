#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
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
    version="1.0.0"
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
    return {
        "message": "YAML to PDF Resume Builder API",
        "version": "1.0.0",
        "endpoints": {
            "generate_resume": "POST /generate-resume",
            "upload_yaml": "POST /upload-yaml",
            "health": "GET /health",
            "download": "GET /download/{filename}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "resume-builder-api"
    }

@app.post("/generate-resume", response_model=GenerateResumeResponse)
async def generate_resume(resume_data: ResumeData):
    """
    Generate a PDF resume from structured resume data
    """
    try:
        # Generate unique filename
        name_parts = resume_data.name.split()
        if len(name_parts) >= 2:
            firstname = name_parts[0].capitalize()
            lastname = name_parts[-1].capitalize()
            base_filename = f"{firstname}_{lastname}"
        else:
            base_filename = "resume"
        
        # Add unique identifier to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{base_filename}_{unique_id}"
        
        # Convert Pydantic models to dict for compatibility with existing functions
        data_dict = resume_data.model_dump()
        
        # Set output directory to temp directory
        os.environ['OUTPUT_DIR'] = TEMP_DIR
        
        # Generate LaTeX file
        latex_path = os.path.join(TEMP_DIR, f"{filename}.tex")
        generate_latex_resume(data_dict, output_path=latex_path)
        
        # Compile to PDF
        pdf_path = compile_latex(latex_path, data=data_dict)
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        return GenerateResumeResponse(
            message="Resume generated successfully",
            filename=f"{filename}.pdf",
            download_url=f"/download/{filename}.pdf"
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
        
        # Generate unique filename
        name_parts = data_dict.get('name', 'resume').split()
        if len(name_parts) >= 2:
            firstname = name_parts[0].capitalize()
            lastname = name_parts[-1].capitalize()
            base_filename = f"{firstname}_{lastname}"
        else:
            base_filename = "resume"
        
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{base_filename}_{unique_id}"
        
        # Set output directory
        os.environ['OUTPUT_DIR'] = TEMP_DIR
        
        # Generate LaTeX and PDF
        latex_path = os.path.join(TEMP_DIR, f"{filename}.tex")
        generate_latex_resume(data_dict, output_path=latex_path)
        
        pdf_path = compile_latex(latex_path, data=data_dict)
        
        # Clean up uploaded YAML file
        os.remove(upload_path)
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        return GenerateResumeResponse(
            message="Resume generated successfully from uploaded YAML",
            filename=f"{filename}.pdf",
            download_url=f"/download/{filename}.pdf"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 