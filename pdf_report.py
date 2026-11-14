"""Small dependency-free PDF writer for line-oriented production reports."""

from __future__ import annotations


def build_pdf(lines: list[str]) -> bytes:
    """Render plain text lines into a paginated, searchable PDF."""
    lines_per_page = 48
    pages = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)]
    if not pages:
        pages = [[]]

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>",
    ]
    page_ids = [4 + 2 * i for i in range(len(pages))]
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("ascii")

    for page_number, page_lines in enumerate(pages, start=1):
        content = bytearray()
        content.extend(b"BT /F1 15 Tf 42 754 Td <50726F64756374696F6E205265706F7274> Tj ET\n")
        content.extend(
            f"BT /F1 9 Tf 520 754 Td <{f'{page_number} / {len(pages)}'.encode('ascii').hex().upper()}> Tj ET\n".encode("ascii")
        )
        for line_number, line in enumerate(page_lines):
            y = 728 - line_number * 14
            encoded = line.encode("cp1252", errors="replace").hex().upper()
            content.extend(
                f"BT /F1 9 Tf 42 {y} Td <{encoded}> Tj ET\n".encode("ascii")
            )

        page_id = page_ids[page_number - 1]
        content_id = page_id + 1
        objects.extend([
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii"),
            (
                f"<< /Length {len(content)} >>\nstream\n".encode("ascii")
                + content
                + b"endstream"
            ),
        ])

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_number} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)
