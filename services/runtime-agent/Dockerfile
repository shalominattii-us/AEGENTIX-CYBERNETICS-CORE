FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --only=production --no-audit --no-fund

COPY src ./src

USER node

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:8080/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

CMD ["node", "src/index.js"]

