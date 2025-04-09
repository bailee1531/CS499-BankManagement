"""
Entry point for the Flask application.

This module uses the application factory pattern to create an instance of the Flask app.
It then runs the development server if this module is executed as the main program.
"""

import os
from app import create_app  # Import the application factory function from the app module
from scheduler import start_scheduler

# Create an instance of the Flask application
app = create_app()

if __name__ == '__main__':

    # Start the scheduler
    scheduler = start_scheduler()

    # For local debugging:
    # app.run(debug=True)

    # For deployment on Render (binds to 0.0.0.0 and uses the PORT environment variable)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
