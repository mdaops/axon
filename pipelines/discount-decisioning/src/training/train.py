import argparse

import joblib
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score


def load_data(path: Path) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_parquet(path)
    X = df.drop(columns=["converted"])
    y = df["converted"]
    return X, y


def train_model(X: pd.DataFrame, y: pd.Series) -> LogisticRegression:
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X, y)
    return model


def evaluate_model(model: LogisticRegression, X: pd.DataFrame, y: pd.Series) -> dict[str, float]:
    y_pred = model.predict(X)
    return {
        "accuracy": accuracy_score(y, y_pred),
        "precision": precision_score(y, y_pred),
        "recall": recall_score(y, y_pred),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/sessions.parquet"))
    parser.add_argument("--output", type=Path, default=Path("model/model.joblib"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    X, y = load_data(args.input)
    print(f"Loaded {len(X)} samples")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = train_model(X_train, y_train)
    print("Model trained")

    train_metrics = evaluate_model(model, X_train, y_train)
    test_metrics = evaluate_model(model, X_test, y_test)

    print(f"Train: {train_metrics}")
    print(f"Test:  {test_metrics}")

    joblib.dump(model, args.output)
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
