from app import create_app  # Import your app factory

app = create_app()  # Create an instance of your Flask app

if __name__ == '__main__':
    # Run the Flask development server
    app.run(debug=True)
   # app.run(debug=True, host='0.0.0.0', port=5000)
