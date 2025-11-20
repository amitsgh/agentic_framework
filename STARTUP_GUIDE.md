cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/health

# Or open browser
# http://localhost:8000/docs

streamlit run ui/app.py



pytest
pytest --cov=app --cov-report=html --cov-report=term

pytest tests/unit/test_models.py::TestDocument

pytest -v

pytest -m unit          # Run only unit tests
pytest -m integration    # Run only integration tests

pytest -x