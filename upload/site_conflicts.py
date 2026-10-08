"""Detect mismatches between a chosen site_id and the depth entered on upload.

Each site_id covers one location at one depth (Kwawi 13.1 is 5 m, 13.2 is 10 m),
so a depth that doesn't fit the chosen site means the wrong site_id was picked.
The upload page mirrors these rules in JS; keep both in sync.
"""
from collections.abc import Callable
from decimal import Decimal, InvalidOperation

from .models import DiveSite

# Free-entry depths within this many metres of the site's depth still match.
DEPTH_TOLERANCE_M = Decimal('1')

DEPTH_CATEGORY_MATCHERS: dict[str, Callable[[Decimal], bool]] = {
    '0_5m': lambda depth: depth <= 5,
    '5m': lambda depth: depth == 5,
    '10m': lambda depth: depth == 10,
    'gt_10m': lambda depth: depth > 10,
}


def find_depth_conflict(site: DiveSite, category: str, custom: str) -> str | None:
    """Return a message explaining the conflict and how to fix it, or None if none."""
    if depth_matches(site.depth, category, custom):
        return None
    message = (
        f'{site.name} is at {format_depth(site.depth)} m, '
        "which doesn't match the depth you entered."
    )
    suggestions = [s.name for s in sibling_sites(site) if
                   depth_matches(s.depth, category, custom)]
    if suggestions:
        return f'{message} Did you mean {" or ".join(suggestions)}?'
    return (f'{message} No registered site matches this depth: '
            'create a new site id from your profile page.')


def depth_matches(site_depth: Decimal | None, category: str, custom: str) -> bool:
    """Whether the entered depth fits the site; unknown depths never conflict."""
    if site_depth is None or not category:
        return True
    if category != 'custom':
        matcher = DEPTH_CATEGORY_MATCHERS.get(category)
        return matcher is None or matcher(site_depth)
    entered = parse_depth(custom)
    return entered is None or abs(entered - site_depth) <= DEPTH_TOLERANCE_M


def sibling_sites(site: DiveSite) -> list[DiveSite]:
    """Other site_ids at the same physical site, e.g. 13.2 for 13.1."""
    if not site.site_id:
        return []
    siblings = DiveSite.objects.filter(
        site_id__startswith=f'{site.site_group}.'
    ).exclude(pk=site.pk)
    return sorted(siblings, key=site_id_sort_key)


def site_id_sort_key(site: DiveSite) -> tuple[int, ...]:
    """Sort '4.2' before '4.10' by comparing site_id parts numerically."""
    return tuple(int(part) for part in site.site_id.split('.'))


def parse_depth(raw: str) -> Decimal | None:
    """Parse a free-entry depth, None if blank or not a number."""
    try:
        return Decimal(raw) if raw else None
    except InvalidOperation:
        return None


def format_depth(depth: Decimal) -> str:
    """Render 5.00 as '5' and 18.50 as '18.5'."""
    return f'{float(depth):g}'
