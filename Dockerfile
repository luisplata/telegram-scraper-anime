FROM python:3.11-slim

# Variables
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y cron && apt-get clean

# Crear carpeta de trabajo
WORKDIR /app

# Copiar archivos
COPY . /app

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar cron job
COPY cronjob /etc/cron.d/anime-cron

# Dar permisos al archivo cron
RUN chmod 0644 /etc/cron.d/anime-cron

# Aplicar el cron job
RUN crontab /etc/cron.d/anime-cron

# Copiar entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ejecutar cron
CMD ["/entrypoint.sh"]
