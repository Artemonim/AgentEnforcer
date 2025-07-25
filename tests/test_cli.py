from unittest.mock import patch

import pytest

from enforcer.cli import main


def test_main():
    with patch("enforcer.cli.mcp.run") as mock_run:
        main()
        mock_run.assert_called_once()
