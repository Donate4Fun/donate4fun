FROM golang:1.18-alpine as builder
ARG GIT_REF

# Force Go to use the cgo based DNS resolver. This is required to ensure DNS
# queries required to connect to linked containers succeed.
ENV GODEBUG netdns=cgo

WORKDIR /go/src/github.com/lightningnetwork/lnd
RUN apk add --no-cache --update alpine-sdk git make

RUN git clone -n https://github.com/nikicat/lnd . && git checkout $GIT_REF
RUN make && make install


FROM alpine

RUN apk add --no-cache --update bash grep iproute2-ss
COPY entrypoint.sh /

EXPOSE 9735 10009

COPY --from=builder /go/bin/lncli /go/bin/lnd /usr/bin/

CMD ["/entrypoint.sh"]
