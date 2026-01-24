"""
============================================================================
Point Cloud Visualization Platform - Backend API
============================================================================
FastAPI application that handles:
- LAS/LAZ file uploads
- PDAL preprocessing
- PotreeConverter execution
- Serving processed point clouds
============================================================================
"""

import os
import uuid
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import laspy

# Import custom utilities
from utils.potree import run_potree_converter, validate_potree_output

# ============================================================================
# Application Configuration
# ============================================================================

app = FastAPI(
    title="Point Cloud Visualization Platform",
    description="API for uploading, processing, and visualizing LAS/LAZ point clouds",
    version="1.0.0"
)

# ============================================================================
# CORS Configuration
# ============================================================================
# Allow frontend to communicate with backend from different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Directory Configuration
# ============================================================================

# Support both Docker and local development
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", "./processed"))
PDAL_PIPELINE_PATH = Path(os.getenv("PDAL_PIPELINE_PATH", "./pdal_pipeline.json"))

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Mount Static Files
# ============================================================================
# Serve processed point clouds as static files
app.mount("/processed", StaticFiles(directory=str(PROCESSED_DIR)), name="processed")

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "status": "online",
        "service": "Point Cloud Visualization Platform",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "projects": "/projects",
            "processed": "/processed/{project_id}/"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Docker
    """
    return {"status": "healthy"}


@app.post("/upload")
@app.post("/api/upload")  # Support /api/ prefix for nginx proxy
async def upload_point_cloud(file: UploadFile = File(..., description="LAS or LAZ point cloud file")):
    """
    Upload and process a LAS/LAZ point cloud file
    
    Maximum file size: 10GB (configurable)
    
    Process:
    1. Validate file format
    2. Generate unique project ID
    3. Save uploaded file
    4. Run PotreeConverter (with LAZ fallback)
    5. Return project information or detailed error structure
    
    Args:
        file: LAS or LAZ file upload (max 10GB)
        
    Returns:
        JSON with project_id, status, and viewer URL
    """
    
    # ========================================================================
    # Step 1: Validate File Format
    # ========================================================================
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = file.filename.lower().split('.')[-1]
    
    if file_extension not in ['las', 'laz']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format: .{file_extension}. Only .las and .laz files are supported."
        )
    
    # ========================================================================
    # Step 2: Generate Unique Project ID
    # ========================================================================
    
    project_id = str(uuid.uuid4())
    project_upload_dir = UPLOAD_DIR / project_id
    project_processed_dir = PROCESSED_DIR / project_id
    
    try:
        project_upload_dir.mkdir(parents=True, exist_ok=True)
        project_processed_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
         return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Server file permission error: {str(e)}",
                "detail": "Could not create project directories."
            }
        )
    
    # ========================================================================
    # Step 3: Save Uploaded File
    # ========================================================================
    
    input_file_path = project_upload_dir / file.filename
    
    try:
        # Save uploaded file
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"✓ File saved: {input_file_path}")
        
        # Validate LAS/LAZ file
        with laspy.open(input_file_path) as las_file:
            header = las_file.header
            point_count = header.point_count
            print(f"✓ Valid LAS/LAZ file with {point_count:,} points")
            
    except Exception as e:
        # Clean up on error
        shutil.rmtree(project_upload_dir, ignore_errors=True)
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": f"Invalid or corrupted LAS/LAZ file",
                "detail": str(e)
            }
        )
    
    # ========================================================================
    # Step 4: Run PotreeConverter (Robust Wrapper)
    # ========================================================================
    
    try:
        print(f"⚙ Running PotreeConverter for {project_id}...")
        
        # This wrapper handles logging, LAZ fallback, and execution
        result = run_potree_converter(
            input_file=input_file_path,
            output_dir=project_processed_dir,
            project_name="cloud"
        )
        
        if result["success"]:
            print(f"✓ PotreeConverter complete for {project_id}")
            return JSONResponse(content={
                "status": "success",
                "project_id": project_id,
                "filename": file.filename,
                "point_count": point_count,
                "viewer_url": f"/processed/{project_id}/pointclouds/cloud/",
                "metadata_url": f"/processed/{project_id}/pointclouds/cloud/metadata.json",
                "message": "Point cloud processed successfully",
                "logs": result.get("logs", "")[:1000] + "..." if len(result.get("logs", "")) > 1000 else result.get("logs", "")
            })
        else:
            # Conversion failed - Return full details
            print(f"✗ PotreeConverter failed for {project_id}")
            
            # Clean up partial files
            shutil.rmtree(project_processed_dir, ignore_errors=True)
            
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Conversion failed",
                    "detail": result["message"],
                    "command": result["command"],
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "logs": result["logs"]
                }
            )
            
    except Exception as e:
        # Unexpected server error
        shutil.rmtree(project_upload_dir, ignore_errors=True)
        shutil.rmtree(project_processed_dir, ignore_errors=True)
        
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal Server Error during processing",
                "detail": str(e),
                "traceback": traceback.format_exc()
            }
        )


@app.get("/projects")
@app.get("/api/projects")  # Support /api/ prefix for nginx proxy
async def list_projects():
    """
    List all processed projects
    
    Returns:
        JSON array of project information
    """
    
    projects = []
    
    for project_dir in PROCESSED_DIR.iterdir():
        if project_dir.is_dir():
            metadata_file = project_dir / "metadata.json"
            
            project_info = {
                "project_id": project_dir.name,
                "viewer_url": f"/processed/{project_dir.name}/pointclouds/cloud/"
            }
            
            # Load metadata if available
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        project_info["metadata"] = metadata
                except:
                    pass
            
            projects.append(project_info)
    
    return JSONResponse(content={
        "status": "success",
        "count": len(projects),
        "projects": projects
    })


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """
    Delete a project and its associated files
    
    Args:
        project_id: Unique project identifier
        
    Returns:
        Success confirmation
    """
    
    project_upload_dir = UPLOAD_DIR / project_id
    project_processed_dir = PROCESSED_DIR / project_id
    
    # Check if project exists
    if not project_processed_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete directories
    try:
        shutil.rmtree(project_upload_dir, ignore_errors=True)
        shutil.rmtree(project_processed_dir, ignore_errors=True)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Project {project_id} deleted successfully"
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting project: {str(e)}"
        )


# ============================================================================
# Application Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Run on application startup
    """
    print("=" * 80)
    print("Point Cloud Visualization Platform - Backend")
    print("=" * 80)
    print(f"Upload directory: {UPLOAD_DIR}")
    print(f"Processed directory: {PROCESSED_DIR}")
    print("Server starting on http://0.0.0.0:8000")
    print("=" * 80)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
