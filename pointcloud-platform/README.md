# 🌍 Point Cloud Visualization Platform

A complete, production-ready Dockerized platform for uploading, processing, and visualizing LAS/LAZ point cloud files in your browser with advanced measurement tools.

![Platform](https://img.shields.io/badge/Platform-Docker-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![Frontend](https://img.shields.io/badge/Frontend-Potree-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- 📤 **Drag & Drop Upload**: Easy LAS/LAZ file upload interface
- ⚙️ **Automatic Processing**: PDAL preprocessing and Potree conversion
- 🎨 **3D Visualization**: Interactive point cloud viewer powered by Potree
- 📏 **Measurement Tools**:
  - Distance measurement
  - Area calculation
  - Volume calculation
  - Angle measurement
  - Height measurement
- 🐳 **Fully Dockerized**: No local dependency issues
- 💾 **Persistent Storage**: Projects saved across container restarts
- 🔄 **Multi-Project Support**: Manage multiple point clouds

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                         │
│                     http://localhost:8080                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Nginx)                          │
│  • Potree Viewer                                            │
│  • Upload Interface                                         │
│  • Measurement Tools                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                           │
│  • File Upload Endpoint                                     │
│  • PDAL Pipeline                                            │
│  • PotreeConverter                                          │
│  • Static File Serving                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Docker Volumes                             │
│  • uploads/     - Original LAS/LAZ files                    │
│  • processed/   - Converted Potree octrees                  │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Minimum System Requirements**:
  - 8GB RAM (16GB recommended for large point clouds)
  - 4 CPU cores
  - 10GB free disk space

## 🚀 Quick Start

### 1. Install Docker Desktop

**Windows:**
1. Download from [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Run installer and follow prompts
3. Restart computer if required
4. Verify installation:
   ```powershell
   docker --version
   docker-compose --version
   ```

**Mac:**
1. Download from [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. Drag to Applications folder
3. Launch Docker Desktop
4. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Clone or Download This Repository

```bash
cd "C:\Users\Admin\Desktop\Point visulization platform\pointcloud-platform"
```

### 3. Build and Start the Platform

```powershell
# Build containers (first time only, takes 5-10 minutes)
docker-compose build

# Start the platform
docker-compose up
```

**Note**: The first build will take 5-10 minutes as it compiles PotreeConverter from source. Subsequent starts are much faster.

### 4. Access the Platform

Open your browser and navigate to:
```
http://localhost:8081
```

**Alternative**: Use the management script for easier control:
```powershell
.\manage.ps1
```

## 📖 Usage Guide

### Uploading Point Clouds

1. **Open the Platform**: Navigate to `http://localhost:8081`
2. **Upload File**: 
   - Drag and drop a `.las` or `.laz` file onto the upload zone, OR
   - Click "Browse Files" to select a file
3. **Wait for Processing**: The platform will:
   - Validate the file
   - Run PDAL preprocessing (outlier removal, noise filtering)
   - Convert to Potree octree format
   - Display the point cloud
4. **View Results**: The 3D viewer will automatically load your point cloud

### Using Measurement Tools

#### Distance Measurement
1. Click "Distance Measurement" button
2. Click two points in the point cloud
3. The distance will be displayed in meters

#### Area Measurement
1. Click "Area Measurement" button
2. Click multiple points to create a polygon
3. Double-click to finish
4. The area will be displayed in square meters

#### Volume Measurement
1. Click "Volume Measurement" button
2. Define a volume region by clicking points
3. The volume will be calculated in cubic meters

#### Angle Measurement
1. Click "Angle Measurement" button
2. Click three points (vertex in the middle)
3. The angle will be displayed in degrees

#### Height Measurement
1. Click "Height Measurement" button
2. Click two points (vertical distance)
3. The height difference will be displayed

### Managing Projects

- **View Projects**: Previously uploaded projects appear in the "Recent Projects" list
- **Switch Projects**: Click on a project to load it
- **Upload New**: Click "Upload New Point Cloud" to add another project

## 🛠️ Advanced Configuration

### Adjusting Resource Limits

Edit `docker-compose.yml` to adjust CPU and memory limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Adjust based on your system
      memory: 8G     # Adjust based on your system
```

### Customizing PDAL Pipeline

Edit `backend/pdal_pipeline.json` to customize preprocessing:

```json
[
  {
    "type": "readers.las",
    "filename": "input.las"
  },
  {
    "type": "filters.outlier",
    "method": "statistical",
    "mean_k": 12,
    "multiplier": 2.0
  }
]
```

### Changing Ports

Edit `docker-compose.yml`:

```yaml
ports:
  - "8081:80"    # Change 8081 to your preferred port
```

## 🐛 Troubleshooting

### Container Build Fails

**Issue**: PotreeConverter compilation fails

**Solution**:
```powershell
# Clean build
docker-compose down -v
docker-compose build --no-cache
```

### Upload Fails

**Issue**: File upload returns error

**Solutions**:
1. Check file format (must be `.las` or `.laz`)
2. Verify file is not corrupted
3. Check Docker logs:
   ```powershell
   docker-compose logs backend
   ```

### Point Cloud Doesn't Load

**Issue**: Viewer shows blank screen

**Solutions**:
1. Check browser console for errors (F12)
2. Verify processing completed:
   ```powershell
   docker-compose logs backend
   ```
3. Check processed files exist:
   ```powershell
   docker exec pointcloud-backend ls -la /app/processed
   ```

### Performance Issues

**Issue**: Slow rendering or processing

**Solutions**:
1. Increase Docker Desktop memory allocation:
   - Docker Desktop → Settings → Resources → Memory
   - Allocate at least 8GB
2. Reduce point budget in viewer (edit `frontend/index.html`):
   ```javascript
   viewer.setPointBudget(500_000); // Reduce from 1_000_000
   ```

### Port Already in Use

**Issue**: Port 8080 or 8000 already in use

**Solution**: Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8082:80"    # Frontend (change to another available port)
  - "8001:8000"  # Backend
```

## 📊 Sample Data

Download sample LAS/LAZ files for testing:

- [USGS 3DEP LiDAR](https://www.usgs.gov/3d-elevation-program)
- [OpenTopography](https://opentopography.org/)
- [Sample LAS Files](https://github.com/ASPRSorg/LAS/tree/master/Sample%20LAS%20Files)

## 🔧 Development

### Running in Development Mode

```powershell
# Backend with auto-reload
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
python -m http.server 8080
```

### Viewing Logs

```powershell
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Accessing Containers

```powershell
# Backend shell
docker exec -it pointcloud-backend /bin/bash

# Frontend shell
docker exec -it pointcloud-frontend /bin/sh
```

## 📁 Project Structure

```
pointcloud-platform/
│
├── backend/
│   ├── Dockerfile              # Backend container configuration
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # FastAPI application
│   ├── pdal_pipeline.json      # PDAL preprocessing config
│   ├── uploads/                # Uploaded files (volume)
│   ├── processed/              # Processed point clouds (volume)
│   └── utils/
│       └── potree.py           # PotreeConverter utilities
│
├── frontend/
│   ├── Dockerfile              # Frontend container configuration
│   ├── index.html              # Potree viewer interface
│   └── potree/                 # Potree library (downloaded during build)
│
├── docker-compose.yml          # Container orchestration
└── README.md                   # This file
```

## 🔒 Security Notes

**For Production Deployment:**

1. **CORS**: Update CORS settings in `backend/main.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

2. **File Size Limits**: Add upload size limits in `backend/main.py`:
   ```python
   @app.post("/upload")
   async def upload_point_cloud(file: UploadFile = File(..., max_size=1_000_000_000)):
   ```

3. **Authentication**: Implement user authentication for production use

4. **HTTPS**: Use a reverse proxy (nginx/traefik) with SSL certificates

## 📝 License

MIT License - feel free to use this project for any purpose.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📧 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Docker logs: `docker-compose logs`
3. Open an issue on GitHub

## 🎯 Roadmap

- [ ] User authentication and project management
- [ ] Support for additional point cloud formats (E57, PCD, PLY)
- [ ] Batch processing multiple files
- [ ] Cloud storage integration (S3, Azure Blob)
- [ ] Advanced filtering and classification tools
- [ ] Export measurements to CSV/JSON
- [ ] Real-time collaboration features

---

**Built with ❤️ using FastAPI, PDAL, Potree, and Docker**
