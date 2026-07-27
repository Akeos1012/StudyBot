import uvicorn

if __name__ == "__main__":
    print("🚀 Starting AI Study Companion...")
    print("📚 Available at: http://localhost:8000")
    print("📖 Topics: http://localhost:8000/topics")
    print("\nPress Ctrl+C to stop")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )