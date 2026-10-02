"""Create a simple 5-row, 3-column DataFrame."""

import pandas as pd


def make_dataframe() -> pd.DataFrame:
    """Return a DataFrame with 3 columns and 5 rows."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["alice", "bob", "carol", "dave", "erin"],
            "score": [88.5, 92.0, 79.5, 95.0, 84.0],
        }
    )


if __name__ == "__main__":
    df = make_dataframe()
    print(df)
    print(f"\nshape: {df.shape}")
