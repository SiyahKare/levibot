"""
Feature schema validator.

Validates DataFrame against features.yml schema.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


class FeatureSchemaValidator:
    """Validates feature DataFrames against schema."""

    def __init__(self, schema_path: Path | str):
        """
        Initialize validator with schema file.

        Args:
            schema_path: Path to features.yml
        """
        self.schema_path = Path(schema_path)
        with open(self.schema_path) as f:
            self.schema = yaml.safe_load(f)

        self.features = {f["name"]: f for f in self.schema["features"]}

    def validate(self, df: pd.DataFrame, strict: bool = True) -> list[str]:
        """
        Validate DataFrame against schema.

        Args:
            df: DataFrame to validate
            strict: If True, raise exception on errors; if False, return list of errors

        Returns:
            List of error messages (empty if valid)

        Raises:
            ValueError: If strict=True and validation fails
        """
        errors = []

        # Check required columns
        required_cols = {
            f["name"] for f in self.schema["features"] if not f.get("nullable", True)
        }
        missing = required_cols - set(df.columns)
        if missing:
            errors.append(f"Missing required columns: {missing}")

        # Check data types
        for col in df.columns:
            if col not in self.features:
                continue  # Allow extra columns

            spec = self.features[col]
            dtype_spec = spec["dtype"]

            # Map schema dtypes to pandas dtypes
            dtype_map = {
                "int8": ["int8"],
                "int64": ["int64"],
                "float32": ["float32", "float64"],  # Allow upcasting
                "float64": ["float64"],
                "string": ["object", "string"],
            }

            expected = dtype_map.get(dtype_spec, [dtype_spec])
            actual = str(df[col].dtype)

            if actual not in expected:
                errors.append(
                    f"Column '{col}': expected dtype {dtype_spec}, got {actual}"
                )

            # Check nullability
            if not spec.get("nullable", True) and df[col].isnull().any():
                null_count = df[col].isnull().sum()
                errors.append(
                    f"Column '{col}': found {null_count} null values (nullable=false)"
                )

        # Check constraints
        for constraint in self.schema.get("constraints", []):
            name = constraint["name"]
            check = constraint["check"]
            severity = constraint.get("severity", "error")

            # Implement constraint checks
            if name == "time_monotonic":
                if "ts" in df.columns and "symbol" in df.columns:
                    for sym in df["symbol"].unique():
                        sym_df = df[df["symbol"] == sym]
                        if not sym_df["ts"].is_monotonic_increasing:
                            msg = f"Constraint '{name}' failed for symbol {sym}: ts not monotonic"
                            if severity == "error":
                                errors.append(msg)
                            else:
                                print(f"⚠️ {msg}")

            elif name == "no_missing_close":
                if "close" in df.columns and df["close"].isnull().any():
                    msg = f"Constraint '{name}' failed: close has null values"
                    if severity == "error":
                        errors.append(msg)

            elif name == "positive_volume":
                if "volume" in df.columns and (df["volume"] < 0).any():
                    msg = f"Constraint '{name}' failed: volume has negative values"
                    if severity == "warning":
                        print(f"⚠️ {msg}")
                    else:
                        errors.append(msg)

        if strict and errors:
            raise ValueError(f"Schema validation failed:\n" + "\n".join(errors))

        return errors

    def get_schema_info(self) -> dict[str, Any]:
        """Get schema metadata."""
        return {
            "version": self.schema["version"],
            "features_count": len(self.schema["features"]),
            "constraints_count": len(self.schema.get("constraints", [])),
            "meta": self.schema.get("meta", {}),
        }


def validate_features(df: pd.DataFrame, schema_path: Path | str | None = None) -> None:
    """
    Convenience function to validate DataFrame.

    Args:
        df: DataFrame to validate
        schema_path: Path to features.yml (defaults to standard location)

    Raises:
        ValueError: If validation fails
    """
    if schema_path is None:
        schema_path = (
            Path(__file__).parent / "features.yml"
        )

    validator = FeatureSchemaValidator(schema_path)
    validator.validate(df, strict=True)

