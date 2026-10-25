"""Vector SVG icons based on Heroicons (Tailwind CSS official icon set).

All icons are rendered inline with ``stroke='currentColor'`` and ``fill='none'``
so they adapt dynamically to the active text color and Streamlit theme.
"""

_PATH = {
    "check_circle": ("M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"),
    "x_circle": (
        "m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
    ),
    "exclamation_triangle": (
        "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 "
        "0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 "
        "16.126ZM12 15.75h.007v.008H12v-.008Z"
    ),
    "information_circle": (
        "m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 "
        "0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
    ),
    "scale": (
        "M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75"
        "M18.75 4.97A48.416 48.416 0 0 0 12 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 "
        "2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 0 "
        "1-2.031.352 5.988 5.988 0 0 1-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 "
        "4.971Zm-16.5.52c.99-.203 1.99-.377 3-.52m0 0l2.62 10.726c.122.499-.106 1.028-.589 "
        "1.202a5.989 5.989 0 0 1-2.031.352 5.989 5.989 0 0 1-2.031-.352c-.483-.174-.711-.703"
        "-.59-1.202L5.25 4.971Z"
    ),
    "chart_bar": (
        "M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 "
        "1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 "
        "19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 "
        "1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 "
        "1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 "
        "3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 "
        "1-1.125-1.125V4.125Z"
    ),
    "arrow_down_tray": (
        "M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.5V16.5M16.5 "
        "12 12 16.5m0 0L7.5 12m4.5 4.5V3"
    ),
    "adjustments": (
        "M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 "
        "0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 "
        "1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75"
    ),
}


def svg(nombre: str, tamano: int = 18, clase: str = "ec-svg") -> str:
    """Return an inline SVG string for the requested Heroicon."""
    path_d = _PATH.get(nombre)
    if not path_d:
        return ""
    return (
        f'<svg class="{clase}" width="{tamano}" height="{tamano}" fill="none" '
        f'viewBox="0 0 24 24" stroke-width="1.75" stroke="currentColor" '
        f'style="display:inline-block;vertical-align:-0.18em;">'
        f'<path stroke-linecap="round" stroke-linejoin="round" d="{path_d}" />'
        f"</svg>"
    )
