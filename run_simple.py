from app import app

if __name__ == "__main__":
    print("Starting server on port 8080...")
    app.run(debug=True, host='0.0.0.0', port=8080) 