from __init__ import create_app  # this imports from __init__.py

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
