import os
import json
import pytest

from receipts_parser.parse_image import process_receipt

def test_process_receipt_success():
    """
    Test successful receipt processing with valid input.
    """

    test_image_path = os.path.join(os.path.dirname(__file__), "data/test-receipt.jpg")
    expected_output_path = os.path.join(os.path.dirname(__file__), "data/expected-output-test-receipt.json")
    with open(expected_output_path, "r") as f:
        expected_prices = [tuple(item) for item in json.load(f)]

    actual_prices = process_receipt(test_image_path)
    print(actual_prices)
    assert len(expected_prices) == len(actual_prices), "given output is not the lenght it expected to be"
    
    for i, (expected, actual) in enumerate(zip(expected_prices, actual_prices)):
        assert actual == expected, f"difference at index {i}: got {actual}, expected {expected}"

def test_process_receipt_invalid_file_path():
    """
    Test that FileNotFoundError is raised when image file does not exist.
    """

    non_existent_path = os.path.join(os.path.dirname(__file__), "data/non-existent-file.jpg")
    
    with pytest.raises(FileNotFoundError):
        process_receipt(non_existent_path)
