FROM node:alpine as build

RUN npm install --location=global pnpm

WORKDIR /app
COPY package.json pnpm-lock.yaml /app/
RUN pnpm install
COPY jsconfig.json vite.config.js /app/
COPY public /app/public
COPY src /app/src
COPY index-green.html /app/index.html
RUN pnpm build

FROM nginx:alpine

WORKDIR /app
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /app
COPY --from=build /app/dist /usr/share/nginx/html
ENTRYPOINT /app/entrypoint.sh
