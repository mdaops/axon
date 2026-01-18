"""Generate synthetic e-commerce session data."""

import argparse
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sessions(n_samples: int = 10000, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic session data with conversion labels."""
    rng = np.random.default_rng(seed)

    session_duration = rng.exponential(scale=300, size=n_samples).clip(60, 1800)
    pages_viewed = rng.poisson(lam=8, size=n_samples).clip(1, 50)
    cart_value = rng.exponential(scale=80, size=n_samples).clip(0, 500)
    items_in_cart = rng.poisson(lam=2, size=n_samples).clip(0, 10)

    norm_duration = (session_duration - 60) / (1800 - 60)
    norm_pages = pages_viewed / 50
    norm_value = cart_value / 500
    norm_items = items_in_cart / 10

    score = 0.2 * norm_duration + 0.2 * norm_pages + 0.4 * norm_value + 0.2 * norm_items
    noise = rng.normal(0, 0.15, size=n_samples)
    prob = 1 / (1 + np.exp(-(score + noise - 0.3) * 5))
    converted = rng.binomial(1, prob)

    return pd.DataFrame(
        {
            "session_duration_seconds": session_duration.round(0).astype(int),
            "pages_viewed": pages_viewed,
            "cart_value": cart_value.round(2),
            "items_in_cart": items_in_cart,
            "converted": converted,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/sessions.parquet"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    df = generate_sessions(n_samples=10000)
    df.to_parquet(args.output, index=False)

    print(f"Generated {len(df)} sessions")
    print(f"Conversion rate: {df['converted'].mean():.1%}")


if __name__ == "__main__":
    main()
