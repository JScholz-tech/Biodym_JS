# Docker 
Docker enables programming in isolated environment containers that allow a very reproducible way of working. In this folder, a Dockerfile is provided that defines the coding environment for working with bioDYM. You can use it to build an image and run it as container. In that way, you don't need to install any libraries or even Jupyter Lab locally on your computer. This Dockerfile is configured that you can access, edit and save local folders. It uses the requirements.txt file provided to install the necessary libraries and Jupyter Lab. Docker runs on Windows Subsystem for Linux (WSL). Docker can be a bit tricky to set up, if you haven't worked with it before, I would recommend simply using Anaconda. If you still want to work with Docker, I'd recommend checking out the following resources:  

More information on Docker: https://docs.docker.com/get-started/docker-overview/  
Data science with JupyterLab in Docker: https://docs.docker.com/guides/jupyter/

  
# Docker commands
Build an image:

    docker build -t biodym-image .


Run container with image:

    docker run -p 8888:8888 -v $(pwd):/home/jovyan/ biodym-image

Accessing JupyterLab after running the container: http://localhost:8888



