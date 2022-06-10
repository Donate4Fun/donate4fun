FROM alpine

RUN apk add --no-cache --update tor bash iproute2-ss

COPY entrypoint.sh /

CMD ["/entrypoint.sh"]
