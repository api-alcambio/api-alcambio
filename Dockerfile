FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias necesarias para Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Agregar repositorio de Google Chrome (Forma moderna compatible)
RUN wget -q -O /tmp/google-chrome-key.pub https://dl-ssl.google.com/linux/linux_signing_key.pub && \
    gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg /tmp/google-chrome-key.pub && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Instalar Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]