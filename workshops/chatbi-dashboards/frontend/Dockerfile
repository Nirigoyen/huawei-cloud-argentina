FROM node:24-slim

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
ARG NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ARG BACKEND_URL=http://localhost:8000
ENV BACKEND_URL=$BACKEND_URL
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
