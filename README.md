# LET'S TALK PANEL

A web panel to test combined AI resources.

## Installation

### Docker

Follow instructions here to install with docker<br />
https://github.com/ground-creative/openvoice-docker

### Stand Alone Installation

1. Clone the repository

```
git clone https://github.com/ground-creative/letstalk-panel.git
```

2. Change environment variables in env.sample file and rename it to .env

3. Install dependencies

```
cd backend
pip install -r requirements.txt
```

## Usage

1. Run the backend inside the backend folder

```
gunicorn -w 4 -b 0.0.0.0:5002 app:app
```

2. Run the frontend from the main folder

```
serve -s frontend -l 3006
```

3. Access panel at http://localhost:5002
