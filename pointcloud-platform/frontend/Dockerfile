# ============================================================================
# Dockerfile for Point Cloud Visualization Platform - Frontend
# ============================================================================
# This Dockerfile creates a lightweight frontend environment with:
# - Nginx web server
# - Potree viewer library
# - Custom HTML interface
# ============================================================================

FROM nginx:alpine

# Set working directory
WORKDIR /usr/share/nginx/html

# ============================================================================
# STEP 1: Install Dependencies
# ============================================================================
RUN apk add --no-cache \
    wget \
    unzip

# ============================================================================
# STEP 2: Download Potree Library
# ============================================================================
# Download Potree 1.8 (stable release)
RUN wget https://github.com/potree/potree/releases/download/1.8/Potree_1.8.zip && \
    unzip Potree_1.8.zip && \
    mv Potree_1.8/* . && \
    rm -rf Potree_1.8.zip Potree_1.8

# ============================================================================
# STEP 3: Copy Custom Frontend Files
# ============================================================================
# Copy our custom index.html (will overwrite Potree's default)
COPY index.html .

# ============================================================================
# STEP 4: Configure Nginx
# ============================================================================
# Create custom nginx configuration
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Allow large file uploads (up to 10GB for point cloud files) \
    client_max_body_size 10G; \
    client_body_timeout 600s; \
    client_body_buffer_size 128k; \
    \
    # Enable CORS for API calls \
    add_header Access-Control-Allow-Origin *; \
    \
    # Serve static files \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Proxy API requests to backend \
    location /api/ { \
        proxy_pass http://backend:8000/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        # Increase timeout for large file uploads (10 minutes) \
        proxy_read_timeout 600s; \
        proxy_send_timeout 600s; \
        proxy_connect_timeout 600s; \
        # Disable buffering for large uploads \
        proxy_request_buffering off; \
    } \
}' > /etc/nginx/conf.d/default.conf

# ============================================================================
# STEP 5: Expose Port
# ============================================================================
EXPOSE 80

# ============================================================================
# STEP 6: Start Nginx
# ============================================================================
CMD ["nginx", "-g", "daemon off;"]
