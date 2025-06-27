# My Trading App

This is a simple Flask-based trading app. It allows you to enter trades and stores them in a local SQLite database (`trades.db`).

## Project Structure
- `app.py`: Main Flask application
- `templates/`: HTML forms and pages for the app
- `static/`: Static files (custom styles can be added later)
- `trades.db`: SQLite database file (created automatically on first run)

## Setup & Run
1. Ensure you have Python 3.7+ and Flask installed.
2. Go to you venv folder, and activate the environment, then simply run the app in classical way:
   ```zsh
   cd dev@lab:~/devel/portfel2$  
   . .venv/bin/activate
     python app.py
   ```
3. Open your browser at http://127.0.0.1:5000/

## Notes
- The database is initialized automatically if it does not exist.
- You can add custom styles in the `static/` directory.
