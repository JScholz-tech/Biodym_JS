import uvicorn

uvicorn.run("systemdefiner.main:app", host="127.0.0.1", port=8001, reload=True)
