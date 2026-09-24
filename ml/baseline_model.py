import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score


DATA_FILE = "data/raw/telemetry.csv"


def main():

    print("Loading WATTWISE telemetry dataset...")

    df = pd.read_csv(DATA_FILE)

    features = [
        "node_cpu_percent",
        "node_memory_percent",
        "container_cpu_percent",
        "container_memory_mb",
    ]

    X = df[features]
    y = df["workload_type"]

    print()
    print("Dataset shape:", df.shape)

    print()
    print("Class distribution:")
    print(y.value_counts())

    # Stratified split is not possible safely with only 6
    # memory samples, so use a simple split for this baseline.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print()
    print("Test accuracy:")
    print(accuracy_score(y_test, predictions))

    print()
    print("Classification report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    print()
    print("Feature importance:")

    importance = pd.Series(
        model.feature_importances_,
        index=features,
    ).sort_values(ascending=False)

    print(importance)

    print()
    print("WATTWISE ML baseline completed.")


if __name__ == "__main__":
    main()
