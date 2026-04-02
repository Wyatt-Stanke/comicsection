FROM ghcr.io/stephanlensky/swayvnc-chrome:latest

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Make directory for the app
RUN mkdir -p /app
RUN chown $DOCKER_USER:$DOCKER_USER /app

# Switch to the non-root user
USER $DOCKER_USER

WORKDIR /app

# Install python
RUN uv python install 3.13

# Install dependencies
COPY --chown=$DOCKER_USER:$DOCKER_USER scraper/requirements.txt /app/
RUN uv venv /app/.venv && uv pip install -r requirements.txt

# Copy scraper source code
COPY --chown=$DOCKER_USER:$DOCKER_USER scraper/main.py scraper/utils.py /app/

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run headed inside the swayvnc container
ENV HEADED=1
ENV SCRAPER_BASE_DIR=/workspace

USER root

# Pass custom command to entrypoint script provided by the base image
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]
