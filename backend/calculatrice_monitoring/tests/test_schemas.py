import pytest
from marshmallow import ValidationError

from calculatrice_monitoring.schemas import HeadersAndRowsSchema


class TestHeadersAndRowsSchema:
    def test_schema_load(self):
        raw = {
            "headers": ["", "1st column", "2nd column"],
            "rows": [["Item 1", 1, 11], ["Item 2", 2, 22]],
        }
        data = HeadersAndRowsSchema().load(raw)
        assert data == {
            "headers": ["", "1st column", "2nd column"],
            "rows": [["Item 1", 1, 11], ["Item 2", 2, 22]],
        }

    @pytest.mark.parametrize(
        "raw",
        [
            {
                "headers": ["1st column"],
                "rows": [[1, 11], [2, 22]],
            },
            {
                "headers": ["1st column", "2nd column"],
                "rows": [[1], [2, 22]],
            },
        ],
    )
    def test_length_validation_error(self, raw):
        with pytest.raises(ValidationError):
            HeadersAndRowsSchema().load(raw)
