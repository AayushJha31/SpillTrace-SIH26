from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/ais/ais_sample_10000.csv")


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Required AIS development file was not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE, low_memory=False)

    print("\n=== AIS INPUT PROFILE ===")
    print(f"Input file: {INPUT_FILE}")
    print(f"Input row count: {len(df):,}")
    print(f"Input column count: {len(df.columns)}")

    print("\n=== COLUMNS ===")
    for column in df.columns:
        print(column)

    print("\n=== DATA TYPES ===")
    print(df.dtypes.to_string())

    print("\n=== NULL COUNTS ===")
    print(df.isna().sum().sort_values(ascending=False).to_string())

    required_columns = [
        "mmsi",
        "base_date_time",
        "longitude",
        "latitude",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required AIS columns: "
            + ", ".join(missing_columns)
        )

    timestamps = pd.to_datetime(
        df["base_date_time"],
        errors="coerce",
        utc=True,
    )

    print("\n=== TIMESTAMP CHECK ===")
    print(f"Valid timestamps: {timestamps.notna().sum():,}")
    print(f"Invalid timestamps: {timestamps.isna().sum():,}")
    print(f"First timestamp UTC: {timestamps.min()}")
    print(f"Last timestamp UTC: {timestamps.max()}")

    latitude = pd.to_numeric(
        df["latitude"],
        errors="coerce",
    )

    longitude = pd.to_numeric(
        df["longitude"],
        errors="coerce",
    )

    valid_coordinates = (
        latitude.between(-90.0, 90.0)
        & longitude.between(-180.0, 180.0)
    )

    print("\n=== COORDINATE CHECK ===")
    print(f"Valid coordinate rows: {valid_coordinates.sum():,}")
    print(f"Invalid coordinate rows: {(~valid_coordinates).sum():,}")
    print(f"Latitude minimum: {latitude.min()}")
    print(f"Latitude maximum: {latitude.max()}")
    print(f"Longitude minimum: {longitude.min()}")
    print(f"Longitude maximum: {longitude.max()}")

    mmsi = pd.to_numeric(
        df["mmsi"],
        errors="coerce",
    )

    valid_mmsi = mmsi.between(
        100000000,
        999999999,
    )

    print("\n=== MMSI CHECK ===")
    print(f"Valid MMSI rows: {valid_mmsi.sum():,}")
    print(f"Invalid MMSI rows: {(~valid_mmsi).sum():,}")
    print(f"Unique valid MMSIs: {mmsi[valid_mmsi].nunique():,}")

    duplicate_count = df.duplicated(
        subset=[
            "mmsi",
            "base_date_time",
            "longitude",
            "latitude",
        ]
    ).sum()

    print("\n=== DUPLICATE CHECK ===")
    print(
        "Duplicate MMSI + timestamp + longitude + latitude rows: "
        f"{duplicate_count:,}"
    )


if __name__ == "__main__":
    main()