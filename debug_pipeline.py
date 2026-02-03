import sys
import traceback
import os
sys.path.append(os.getcwd())

try:
    from ml.train_pipeline import ServiceProbTrainingPipeline
    print("Starting pipeline...")
    pipeline = ServiceProbTrainingPipeline()
    raw = pipeline.fetch_data()
    if raw is not None:
        engineered = pipeline.engineer_features(raw)
        pipeline.train(engineered)
    print("Pipeline finished successfully.")
except Exception:
    with open("pipeline_error.txt", "w") as f:
        f.write(traceback.format_exc())
    print("Error written to pipeline_error.txt")
