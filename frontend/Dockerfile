FROM node:alpine as build

RUN npm install --location=global pnpm

WORKDIR /app
COPY package.json pnpm-lock.yaml /app/
RUN pnpm install
COPY index.html jsconfig.json vite.config.js /app/
COPY public /app/public
COPY src /app/src
RUN pnpm build

FROM nginx:alpine

WORKDIR /app
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
