FROM mcr.microsoft.com/powershell:latest
WORKDIR /app
COPY router.ps1 .
EXPOSE 8080
CMD ["pwsh", "-File", "router.ps1"]
