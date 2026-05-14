
step1: First run this command::

->   pip install -e .

Step2 : 
->    python src/queues/worker.py  

step3:
->    uvicorn src.api.main:app --reload