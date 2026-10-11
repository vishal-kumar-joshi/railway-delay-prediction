# RailGuard AI 🚆
### Railway Delay Prediction System

RailGuard AI is a machine learning project designed to predict railway delays using historical railway data,whether & current live information. It combines a trained ML model with a FastAPI backend and a web-based interface to demonstrate delay predictions.

## Features
- Machine learning-based delay prediction
- FastAPI backend for prediction APIs
- Interactive web interface
- Railway route and delay information visualization

## Tech Stack
- **Language:** Python, JavaScript
- **ML & Data:** Scikit-learn, Pandas, NumPy
- **Backend:** FastAPI, Uvicorn
- **Tools:** Jupyter Notebook, Git, GitHub

## Getting Started

**1. Clone the repository**
```bash
git clone https://github.com/vishal-kumar-joshi/railway-delay-prediction.git
cd railway-delay-prediction
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the backend**

Run the FastAPI application using the entry-point file configured in the project:
```bash
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` to explore the API.

> Note: Update the entry-point command if your FastAPI application uses a different filename or package path.

## Dataset & Model
The project uses railway data for model training and evaluation. Large datasets are excluded from the Git repository to keep it lightweight. Trained model files are used for prediction.

## Project Status
Developed as a machine learning portfolio project for learning, experimentation, and demonstration.

## Author
**Vishal Kumar Joshi**

- GitHub: [vishal-kumar-joshi](https://github.com/vishal-kumar-joshi)