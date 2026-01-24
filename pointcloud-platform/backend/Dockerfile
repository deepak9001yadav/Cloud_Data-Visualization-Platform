# ============================================================================
# Dockerfile for Point Cloud Visualization Platform - Backend
# ============================================================================
# This Dockerfile creates a complete backend environment with:
# - Python 3.10
# - PDAL (Point Data Abstraction Library)
# - GDAL (Geospatial Data Abstraction Library)
# - LASzip (LAS/LAZ compression)
# - PotreeConverter (Octree generation for Potree viewer)
# - FastAPI + Uvicorn (Web server)
# ============================================================================

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# ============================================================================
# STEP 1: Install System Dependencies
# ============================================================================
RUN apt-get update && apt-get install -y \
    # Python and build tools
    ca-certificates \
    python3.10 \
    python3-pip \
    python3.10-dev \
    build-essential \
    cmake \
    git \
    wget \
    # PDAL and GDAL dependencies
    libpdal-dev \
    pdal \
    libgdal-dev \
    gdal-bin \
    # LASzip for LAZ compression support
    liblaszip-dev \
    # Additional libraries for PotreeConverter
    libtbb-dev \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# STEP 2: Install PotreeConverter
# ============================================================================
# PotreeConverter converts point clouds to Potree's octree format
# We compile from source to get the latest stable version and KEEP resources
RUN cd /opt && \
    git clone https://github.com/potree/PotreeConverter.git && \
    cd PotreeConverter && \
    mkdir build && \
    cd build && \
    cmake -DCMAKE_BUILD_TYPE=Release .. && \
    make && \
    # Copy binary to root of repo so it sits next to 'resources' folder
    cp PotreeConverter .. && \
    # Cleanup build dir to save space, but keep the repo structure
    rm -rf /opt/PotreeConverter/build

# ============================================================================
# STEP 3: Upgrade pip and Install Python Dependencies
# ============================================================================
RUN python3.10 -m pip install --upgrade pip

# Copy requirements file
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# STEP 4: Copy Application Code
# ============================================================================
COPY main.py .
COPY pdal_pipeline.json .
COPY utils/ ./utils/

# ============================================================================
# STEP 5: Create Directories for Uploads and Processed Files
# ============================================================================
RUN mkdir -p /app/uploads /app/processed

# ============================================================================
# STEP 6: Expose Port and Set Environment Variables
# ============================================================================
EXPOSE 10000

# Set Python to run in unbuffered mode (logs appear immediately)
ENV PYTHONUNBUFFERED=1

# ============================================================================
# STEP 7: Health Check
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:10000/health || exit 1

# ============================================================================
# STEP 8: Run the Application
# ============================================================================
# Use uvicorn to run FastAPI with:
# - Host 0.0.0.0 (accessible from outside container)
# - Port 10000
# - Auto-reload disabled in production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
