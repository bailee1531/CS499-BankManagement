"""
Entry point for the Flask application.

This module uses the application factory pattern to create an instance of the Flask app.
It then runs the development server if this module is executed as the main program.
"""

import os
from app import create_app  # Import the application factory function from the app module

# Create an instance of the Flask application
app = create_app()

if __name__ == '__main__':
    # Get the port from the environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app on 0.0.0.0 so it's accessible externally
    app.run(debug=True, host='0.0.0.0', port=port)
