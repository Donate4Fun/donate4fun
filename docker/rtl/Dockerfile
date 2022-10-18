FROM node:16-alpine as builder
ARG GIT_REF=v0.13.1

WORKDIR /RTL
RUN apk add --no-cache --update git
RUN git clone -n https://github.com/Ride-The-Lightning/RTL . \
  && git checkout $GIT_REF

RUN npm ci --force

# Build the Angular application
RUN npm run buildfrontend

# Build the Backend from typescript server
RUN npm run buildbackend

# Remove non production necessary modules
RUN npm prune --omit=dev --force

# ---------------
# Release App
# ---------------
FROM node:16-alpine as runner

WORKDIR /RTL

RUN apk add --no-cache tini

COPY --from=builder /RTL/rtl.js ./rtl.js
COPY --from=builder /RTL/package.json ./package.json
COPY --from=builder /RTL/frontend ./frontend
COPY --from=builder /RTL/backend ./backend
COPY --from=builder /RTL/node_modules/ ./node_modules
RUN mkdir /fake-macaroon && echo fake > /fake-macaroon/admin.macaroon

EXPOSE 3000

ENTRYPOINT ["/sbin/tini", "-g", "--"]

CMD ["node", "rtl"]
