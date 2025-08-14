# Chatbot Application

## Overview

This project is an implementation of a retrieval augmented generation (RAG) chatbot that can be used for a variety of things like document summarization, customer support or FAQ chatbot, and so on.

It utilizes an openly sourced LLM and an embedding model available on the OLLAMA platform.

## Technologies used
- Python 3.13
- Ollama
- Langchain
- ChromaDB
- Langgraph

## Setup

### Ollama setup
1. Install Ollama on your preferred platform using the instruction given on the official website
    ```
    https://ollama.com/download
    
    #On RunPod use:
    curl -fsSL https://ollama.com/install.sh | sh

2. Pull the models used in the project
     ```
    ollama pull llama3.2:3b

    ollama pull mxbai-embed-large:335m

    #On RunPod use:
    ollama serve & \
    sleep 5 && \
    ollama pull llama3.2:3b && \
    ollama pull mxbai-embed-large:335m && \
    pkill ollama

3. ollama should then be running in the background, using:
    ```
    ollama serve & (skip if you're using runpod)

### Project setup
1. Clone repo
    ```
    git clone <repo-name>
    cd <main-directory>

2. Create a virtual environment using
    ```
    python -m venv <environment-name> (On Windows)

    python3 -m venv <environment-name>

3. Activate the virtual environment using
    ```
    source .<environment-name>/Scripts/activate (On Windows)

    source .<environment-name>/bin/activate

4. Install dependencies from requiremnts.txt file
    ```
    pip install -r requirements.txt (On Windows)

    pip3 install -r requirements.txt

5. Make directory data_source (if it doesn't exist) to store documents that information would be retrieved from
    ```
    mkdir data_sources

6. Run python file
    ```
    python chatbot.py (On Windows)

    python3 chatbot.py

## Deploying on Runpod

    chmod +x start.sh
    ./start.sh &
    disown