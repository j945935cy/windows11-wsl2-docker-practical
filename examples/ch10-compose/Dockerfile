FROM python:3.12-alpine
WORKDIR /site
COPY site/ /site/
EXPOSE 8000
CMD ["python", "-m", "http.server", "8000", "--directory", "/site"]
