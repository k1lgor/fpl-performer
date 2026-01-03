FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install uv && uv sync

EXPOSE 7860

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
