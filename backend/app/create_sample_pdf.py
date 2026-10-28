from pathlib import Path

def create_sample_pdf(output_path: Path):
    """
    Creates a valid 2-page PDF file with text for testing RAG extraction,
    concept explanation, milestones, and page citations.
    """
    # Simple minimal valid PDF structure with 2 pages
    content_page_1 = (
        "BT\n"
        "/F1 16 Tf\n"
        "50 720 Td\n"
        "(NOVA AI: Data Structures & Neural Systems - Page 1) Tj\n"
        "/F1 12 Tf\n"
        "0 -40 Td\n"
        "(Overview of Linked Lists and Algorithmic Complexity) Tj\n"
        "0 -25 Td\n"
        "(A Singly Linked List consists of sequential nodes where each node contains data) Tj\n"
        "0 -20 Td\n"
        "(and a reference pointer to the subsequent node. Access time is O(n).) Tj\n"
        "0 -25 Td\n"
        "(Historical Milestone: In October 2026, autonomous multi-agent systems reached) Tj\n"
        "0 -20 Td\n"
        "(human-parity in structured task planning and execution workflows.) Tj\n"
        "ET"
    )

    content_page_2 = (
        "BT\n"
        "/F1 16 Tf\n"
        "50 720 Td\n"
        "(NOVA AI: Machine Learning Architecture - Page 2) Tj\n"
        "/F1 12 Tf\n"
        "0 -40 Td\n"
        "(Retrieval-Augmented Generation RAG and Vector Embeddings) Tj\n"
        "0 -25 Td\n"
        "(RAG systems partition extensive documents into semantic chunks and compute) Tj\n"
        "0 -20 Td\n"
        "(cosine similarity between query vectors and stored chunk representations.) Tj\n"
        "0 -25 Td\n"
        "(Exam Question 1: Explain the difference between array indexing and linked list traversals.) Tj\n"
        "0 -20 Td\n"
        "(Milestone: Spring Semester Exam scheduled for November 15, 2026 at 10:00 AM.) Tj\n"
        "ET"
    )

    stream1 = content_page_1.encode("latin1")
    stream2 = content_page_2.encode("latin1")

    pdf_template = (
        "%PDF-1.4\n"
        "1 0 obj\n"
        "<< /Type /Catalog /Pages 2 0 R >>\n"
        "endobj\n"
        "2 0 obj\n"
        "<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>\n"
        "endobj\n"
        "3 0 obj\n"
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R /Resources << /Font << /F1 7 0 R >> >> >>\n"
        "endobj\n"
        "4 0 obj\n"
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 6 0 R /Resources << /Font << /F1 7 0 R >> >> >>\n"
        "endobj\n"
        "5 0 obj\n"
        f"<< /Length {len(stream1)} >>\n"
        "stream\n"
        + content_page_1 + "\n"
        "endstream\n"
        "endobj\n"
        "6 0 obj\n"
        f"<< /Length {len(stream2)} >>\n"
        "stream\n"
        + content_page_2 + "\n"
        "endstream\n"
        "endobj\n"
        "7 0 obj\n"
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
        "endobj\n"
        "xref\n"
        "0 8\n"
        "0000000000 65535 f \n"
        "0000000010 00000 n \n"
        "0000000060 00000 n \n"
        "0000000120 00000 n \n"
        "0000000235 00000 n \n"
        "0000000350 00000 n \n"
        "0000000500 00000 n \n"
        "0000000650 00000 n \n"
        "trailer\n"
        "<< /Size 8 /Root 1 0 R >>\n"
        "startxref\n"
        "720\n"
        "%%EOF\n"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf_template.encode("latin1"))

if __name__ == "__main__":
    out = Path("data/uploads/sample_study_material.pdf")
    create_sample_pdf(out)
    print(f"Sample PDF created at {out}")

