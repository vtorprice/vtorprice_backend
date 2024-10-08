FROM nginx:stable

ARG CERTBOT_EMAIL=info@domain.com
ARG DOMAIN_LIST

RUN  apt-get update \
      && apt-get install -y cron certbot python3-certbot-nginx bash wget \
      && certbot certonly --standalone --agree-tos -m "${CERTBOT_EMAIL}" -n -d ${DOMAIN_LIST} \
      && rm -rf /var/lib/apt/lists/* \
      && echo "@monthly certbot renew --nginx >> /var/log/cron.log 2>&1" >/etc/cron.d/certbot-renew \
      && crontab /etc/cron.d/certbot-renew

VOLUME /etc/letsencrypt

CMD [ "sh", "-c", "cron && nginx -g 'daemon off;'" ]
