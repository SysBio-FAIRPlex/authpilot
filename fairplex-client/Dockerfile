# Stage 1: Build the application
FROM node:23-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
COPY public ./public
RUN npm run build

# # Stage 2: Create the production image
# FROM node:23-alpine

# WORKDIR /app

# COPY --from=builder /app/dist ./dist

# ENV NODE_ENV=production

EXPOSE 5554

CMD ["node", "./dist/app.js"]