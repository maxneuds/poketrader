FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

RUN ["apt", "update"]
RUN ["apt", "install", "-y", "vim"]
RUN ["apt", "install", "-y", "neofetch"]
RUN ["apt", "install", "-y", "tesseract-ocr"]
RUN ["apt", "install", "-y", "adb"]

RUN pip install poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

RUN echo 'alias ll="ls -lah --color=auto"' >> /home/vscode/.zshrc
RUN echo 'alias ll="ls -lah --color=auto"' >> /home/vscode/.zshrc


