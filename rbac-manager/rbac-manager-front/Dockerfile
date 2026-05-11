ARG node_version=20
FROM docker.io/node:${node_version}-alpine AS builder
WORKDIR /usr/src/app
COPY . .
RUN npm install --no-audit
ARG kendo_license=false
RUN if [ "${kendo_license}" = "false" ]; then \ 
    echo "the project dosen't use kendo UI"; \
    else \
    echo "the project is using kendo license, activating ..." && \
    export KENDO_UI_LICENSE=${kendo_license} && \
    npx kendo-ui-license activate; \
    fi
RUN npm run build --no-audit

FROM docker.io/nginx:alpine

ARG dir_output=dist
ARG user=reactuser
RUN addgroup -S reactgroup && adduser -S ${user} -G reactgroup

ARG sub_directory=/
COPY --from=builder --chown=${user}:reactgroup /usr/src/app/${dir_output} /usr/share/nginx/html${sub_directory}
COPY --from=builder --chown=${user}:reactgroup /usr/src/app/nginx/default.conf.template /etc/nginx/templates/

RUN apk update && apk add --upgrade libxml2 libavif && \ 
    chown -R ${user}:reactgroup /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    chown -R ${user}:reactgroup /etc/nginx && \
    chmod -R 755 /etc/nginx && \
    chown -R ${user}:reactgroup /var/cache/nginx && \
    chown -R ${user}:reactgroup /var/log/nginx && \
    chown -R ${user}:reactgroup /tmp && \
    chmod -R 755 /tmp

COPY run.sh /run.sh
RUN chmod +x /run.sh && chown ${user}:reactgroup /run.sh

USER root
RUN touch /var/run/nginx.pid && \ 
    chown -R ${user}:reactgroup /var/run/nginx.pid

ARG port_exposed
EXPOSE $port_exposed

USER $user

ENTRYPOINT ["/run.sh"]