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

# Create output directory
RUN mkdir -p /app/output
ENV OUTPUT_DIR=/app/output

# Configure LaTeX to allow writing to directories
RUN mkdir -p /root/texmf/web2c && \
    echo "openout_any = a" > /root/texmf/web2c/texmf.cnf

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy app files
COPY generate_resume.py template.tex ./

# No default entrypoint/cmd - will be provided by docker-compose 