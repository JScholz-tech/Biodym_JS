# Get base image for JupyterLab
FROM quay.io/jupyter/base-notebook


# Set up container working directory
WORKDIR /home/jovyan



# Load Python packages from requirements.txt file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Expose JupyterLab on port 8888
EXPOSE 8888

# Start JupyterLab
CMD ["start-notebook.py", "--NotebookApp.token=''"]
