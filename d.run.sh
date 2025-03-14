# Automatically stop and delete old container to create and run the new one
docker rm -f metro_estado 2>/dev/null || true && \
docker run -d --name metro_estado --restart unless-stopped --network ntfy_default metro_scrapper
