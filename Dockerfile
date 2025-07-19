FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Set output directory environment variable (matching docker-compose setting)
ENV OUTPUT_DIR=/app

# Configure LaTeX to allow writing to directories
RUN mkdir -p /root/texmf/web2c && \
    echo "openout_any = a" > /root/texmf/web2c/texmf.cnf

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy all application files
COPY generate_resume.py main.py template.tex resume.yaml ./

# Expose FastAPI port
EXPOSE 8000

# Default command to run the FastAPI server
# Can be overridden with: docker run <image> python3 generate_resume.py
CMD ["python3", "main.py"] 