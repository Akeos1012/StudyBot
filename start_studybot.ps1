# Start StudyBot Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn app.main:app --reload"

# Start StudyBot Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

# Wait for frontend to start
Start-Sleep -Seconds 3

# Open StudyBot in browser
Start-Process "http://localhost:5173"