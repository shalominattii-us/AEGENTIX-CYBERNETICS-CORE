FROM mcr.microsoft.com/powershell:latest
WORKDIR /app
COPY registry.ps1 .
COPY skills/ /skills/
CMD ["pwsh", "-File", "registry.ps1"]
