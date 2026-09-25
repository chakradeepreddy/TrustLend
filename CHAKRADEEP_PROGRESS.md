# CHAKRADEEP — TRUSTLEND PROGRESS LOG

## Project
- Project: TrustLend / Second Look
- Hackathon: HackGenix 2026
- Problem Statement: PS #11 — When the Model Should Ask for Help
- Team: Akshay, Tanush, Chakradeep, Gokul
- My role: Chakradeep

## My ownership
I own:
- src/model.py
- Loan model
- Model calibration
- Cost-based cutoff
- Check 1
- Reliability diagram
- Model card

## Team ownership
- Akshay → src/familiarity.py, src/policy.py, src/decide.py
- Tanush → src/data.py, src/evaluate.py
- Chakradeep → src/model.py
- Gokul → app/

## Git setup completed
- GitHub repository: TrustLend
- Main branch initialized and pushed
- Initial skeleton commit: d7ecb64
- My branch: chakradeep/model
- My branch is connected to origin
- Working tree currently clean

## Python environment completed
- Python version: 3.12.14
- Conda environment: trustlend
- Interpreter:
  /opt/anaconda3/envs/trustlend/bin/python
- Required project packages installed successfully:
  pandas
  numpy
  scikit-learn
  streamlit
  plotly
  joblib

## Repository structure created
TrustLend/
├── data/
├── artifacts/
├── src/
│   ├── __init__.py
│   ├── data.py
│   ├── model.py
│   ├── familiarity.py
│   ├── policy.py
│   ├── decide.py
│   └── evaluate.py
├── scripts/
│   ├── __init__.py
│   ├── train.py
│   └── evaluate.py
├── app/
│   ├── Home.py
│   └── pages/
├── notebooks/
├── requirements.txt
├── .gitignore
└── README.md

## Completed milestones

### Step 0 — Repository setup
Status: COMPLETE
- Repository created
- Initial project skeleton created
- requirements.txt created
- .gitignore created
- README.md created
- Skeleton committed to main
- Skeleton pushed to GitHub

### Branch setup
Status: COMPLETE
- chakradeep/model created
- chakradeep/model pushed to GitHub
- Work will happen on this branch

### Python setup
Status: COMPLETE
- Python 3.12.14 installed
- trustlend Conda environment created
- Project packages installed
- Antigravity should use the trustlend interpreter

### ML implementation
Status: IN PROGRESS

Completed tasks:
- Train the loan-risk model (HistGradientBoostingClassifier + CalibratedClassifierCV)
- Calculate the 17% cost-based cutoff
- Implement Check 1 (uncertainty band)
- Save the trained model artifact to artifacts/model.joblib
- Implement risk(), plain_decision(), check1_unsure(), and CUTOFF
- Produce the reliability diagram (Raw AUC: 0.8669, Calibrated AUC: 0.8677 on temporary split)

Pending tasks:
- Create the model card
- Test everything

## My planned ML work
1. Understand the training data contract
2. Train the loan-risk model
3. Calibrate the model
4. Calculate the 17% cost-based cutoff
5. Implement Check 1
6. Produce the reliability diagram
7. Save the trained model artifact when appropriate
8. Hand risk(), plain_decision(), check1_unsure(), and CUTOFF to Akshay
9. Create the model card
10. Test everything

## Important project rules
- Do not modify another person's implementation files without coordination.
- Do not commit the CSV dataset.
- Do not commit .venv/
- Keep experimental work separate from production project files.
- Do not invent or manually fake metrics.
- The model must be evaluated honestly.
- Keep this log updated after each meaningful milestone.

## Current status
Current step: Baseline model implementation and reliability diagram generation complete (using temporary train/validation split).
Next step: Create the model card.
