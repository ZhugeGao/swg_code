from SWG_utils import timestamp_convert

def test_timestamp_convert_simple():
    """Tests a simple conversion under a few minutes."""
    assert timestamp_convert(123.456) == '00:02:03.456000'

def test_timestamp_convert_with_hour():
    """Tests a conversion that includes hours."""
    assert timestamp_convert(3723.1) == '01:02:03.100000'

def test_timestamp_convert_sub_minute():
    """Tests a conversion for a value less than one minute."""
    assert timestamp_convert(59.999) == '00:00:59.999000'

def test_timestamp_convert_zero():
    """Tests the zero case."""
    assert timestamp_convert(0.0) == '00:00:00.000000'

def test_timestamp_convert_long_ms():
    """Tests a conversion with long milliseconds."""
    assert timestamp_convert(1.987654) == '00:00:01.987654'
