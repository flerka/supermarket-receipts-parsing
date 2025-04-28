import re
import logging
from paddleocr import PaddleOCR
from typing import List, Tuple, Sequence

# precompile patterns for price as they called often
_patterns = [
    re.compile(r'^[A-Z]?\d+\.\d{2}$'),    # to parse 12.99 or L12.99 or X12.99
    re.compile(r'^\d+\.\d{2}[A-Z]?$'),    # to parse 12.99 or 12.99L or 12.99X
    re.compile(r'^\d+$')                  # to parse 12
]

def is_price(text: str) -> bool:
    """
    Detects prices in the text in different formats.
    """

    if not isinstance(text, str):
        return False
    
    # preproces to be able to use regular expression e.g. replace € sign
    cleaned = text.replace(' ', '').replace(',', '.').replace('€', 'E').replace('$', 'S').replace('£', 'L')
    
    return any(p.match(cleaned) for p in _patterns)

def group_into_lines(
    boxes: Sequence[Tuple[str, float, float, float]],
    max_line_spacing: float = 10.0
) -> List[List[Tuple[str, float, float, float]]]:
    """
    Group bounding boxes into visual lines based on vertical positioning.

    Args:
        boxes: Sequence of boxes coordinates
        max_line_spacing: Maximum vertical distance between boxes to consider

    Returns:
        List of lines, where each line is a list of bounding boxes that belong
        to the same visual line
    """
    if not boxes:
        return []

    if max_line_spacing < 0:
        raise ValueError("max_line_spacing must be >=0")

    try:
        # sort by vertical position
        boxes.sort(key=lambda box: box[2])
    except (IndexError, TypeError) as e:
        raise ValueError("Boxes must be in (text, x1, y1, x2, y2) format") from e

    lines = []
    current_line = [boxes[0]]
    current_top = boxes[0][2]

    for box in boxes[1:]:
        if abs(box[2] - current_top) <= max_line_spacing:
            current_line.append(box)
        else:
            lines.append(current_line)
            current_line = [box]
            current_top = box[2]
    
    lines.append(current_line)
    return lines

def process_receipt(image_path: str) -> List[Tuple[str, str]]:
    """
    Process a receipt and returns product-price pairs.

    Args:
        Path to the receipt image.

    Returns:
        Pasrsed receipt line.
    """

    ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
    result = ocr.ocr(image_path, cls=True, table=True)

    # get all the boxes
    boxes: List[Tuple[str, List[List[float]], float]] = []
    for line in result:
        logging.debug("current line")
        logging.debug(line)
        for obj in line:
            text: str = obj[1][0]
            box: List[List[float]] = obj[0]
            top_y: float = min(point[1] for point in box)
            boxes.append((text, box, top_y))

    # group boxes into lines
    lines: List[List[Tuple[str, List[List[float]], float]]] = group_into_lines(boxes)
    product_prices: List[Tuple[str, str]] = []

    for _, line in enumerate(lines, start=1):
        sorted_line = sorted(line, key=lambda x: min(p[0] for p in x[1]))

        logging.debug(sorted_line)

        texts: List[str] = [item[0] for item in sorted_line]

        # get all price candidates
        price_candidates: List[Tuple[int, str]] = [
            (i, text) for i, text in enumerate(texts) if is_price(text)
        ]
        logging.debug(f"Price candidates: {price_candidates}")

        if price_candidates:
            price_idx, price = max(price_candidates, key=lambda x: x[0])

            product_components: List[str] = [
                text for i, text in enumerate(texts[:price_idx]) if not is_price(text)
            ]

            product: str = ' '.join(product_components).strip()
            if product:
                product_prices.append((product, price))

    return product_prices