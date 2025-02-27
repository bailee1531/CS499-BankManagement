"""
Entry point for the Flask application.

This module uses the application factory pattern to create an instance of the Flask app.
It then runs the development server if this module is executed as the main program.
"""

from app import create_app  # Import the application factory function from the app module

# Create an instance of the Flask application by calling the factory function
app = create_app()

if __name__ == '__main__':
    # Run the Flask development server in debug mode.
    # Debug mode enables hot reloading and provides detailed error messages.
    app.run(debug=True)
    
    # Uncomment the following line to run the server on all available IP addresses at port 5000.
    # This is useful if you want the app to be accessible from other machines on your network.
    # app.run(debug=True, host='0.0.0.0', port=5000)
