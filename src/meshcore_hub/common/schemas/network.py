"""Pydantic schemas for network configuration."""

from typing import Optional

from pydantic import BaseModel


class RadioConfig(BaseModel):
    """Parsed radio configuration from comma-delimited string.

    Format: "<profile>,<frequency>,<bandwidth>,<spreading_factor>,<coding_rate>,<tx_power>"
    Example: "EU/UK Narrow,869.618MHz,62.5kHz,8,8,22dBm"
    """

    profile: Optional[str] = None
    frequency: Optional[str] = None
    bandwidth: Optional[str] = None
    spreading_factor: Optional[int] = None
    coding_rate: Optional[int] = None
    tx_power: Optional[str] = None

    @classmethod
    def from_config_string(cls, config_str: Optional[str]) -> Optional["RadioConfig"]:
        """Parse a comma-delimited radio config string.

        Args:
            config_str: Comma-delimited string in format:
                "<profile>,<frequency>,<bandwidth>,<spreading_factor>,<coding_rate>,<tx_power>"

        Returns:
            RadioConfig instance if parsing succeeds, None if input is None or empty
        """
        if not config_str:
            return None

        parts = [p.strip() for p in config_str.split(",")]

        # Handle partial configs by filling with None
        while len(parts) < 6:
            parts.append("")

        # Parse spreading factor and coding rate as integers
        spreading_factor = None
        coding_rate = None

        try:
            if parts[3]:
                spreading_factor = int(parts[3])
        except ValueError:
            pass

        try:
            if parts[4]:
                coding_rate = int(parts[4])
        except ValueError:
            pass

        return cls(
            profile=parts[0] or None,
            frequency=parts[1] or None,
            bandwidth=parts[2] or None,
            spreading_factor=spreading_factor,
            coding_rate=coding_rate,
            tx_power=parts[5] or None,
        )
