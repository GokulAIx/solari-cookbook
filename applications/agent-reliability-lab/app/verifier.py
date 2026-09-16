"""Independent checks of the demo application's resulting state."""

from patchright.async_api import Page

from .models import VerificationResult


async def verify_cart(page: Page, expected_product: str, expected_quantity: int) -> VerificationResult:
    store = page.locator("#store")
    product = await store.get_attribute("data-cart-product") or ""
    raw_quantity = await store.get_attribute("data-cart-quantity") or "0"
    try:
        quantity = int(raw_quantity)
    except ValueError:
        return VerificationResult(
            False,
            expected_product,
            0,
            "cart quantity was not a valid integer",
        )
    passed = product == expected_product and quantity == expected_quantity
    reason = "cart state matched expected result" if passed else "cart state did not match expected result"
    return VerificationResult(passed, expected_product, quantity, reason)