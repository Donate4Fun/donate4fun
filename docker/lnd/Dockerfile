FROM golang:1.18-alpine as builder
ARG GIT_REF
ARG GIT_REPO=https://github.com/nikicat/lnd

# Force Go to use the cgo based DNS resolver. This is required to ensure DNS
# queries required to connect to linked containers succeed.
ENV GODEBUG netdns=cgo

WORKDIR /go/src/github.com/lightningnetwork/lnd
RUN apk add --no-cache --update alpine-sdk git make

RUN git clone -n $GIT_REPO . && git checkout $GIT_REF
RUN make && make install


FROM alpine

RUN apk add --no-cache --update bash grep iproute2-ss bind-tools
COPY entrypoint.sh /

EXPOSE 9735 10009

COPY --from=builder /go/bin/lncli /go/bin/lnd /usr/bin/

CMD ["/entrypoint.sh"]
