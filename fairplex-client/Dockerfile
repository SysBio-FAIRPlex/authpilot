# Stage 1: Build the application
FROM node:23-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Create the production image
FROM node:23-alpine AS production

WORKDIR /app
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist/ ./dist/
COPY ./public/ ./public/
COPY ./src/views/ ./views/
RUN npm install --omit=dev

ENV NODE_ENV=production

ARG MY_PORT
ENV MY_PORT ${MY_PORT}

EXPOSE ${MY_PORT}

CMD ["npx", "tsx", "./dist/app.js"]