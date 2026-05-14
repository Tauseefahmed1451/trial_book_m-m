"""Generate a sample Excel workbook for the demo scenario."""

from openpyxl import Workbook


def main() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "books"
    sheet.append(["title", "notes_on_outline_before", "audience", "tone", "research_mode"])
    sheet.append(
        [
            "Remote Work for Small Teams: A Practical Guide",
            "Target audience: founders and managers of small teams. Tone: practical and concise. Include chapters on hiring, communication, productivity, and culture. Keep the book 5 chapters max.",
            "Founders and managers of small teams",
            "Practical and concise",
            "lightweight",
        ]
    )
    sheet.append(["Incomplete Example", "", "", "", "lightweight"])
    workbook.save("sample_input.xlsx")


if __name__ == "__main__":
    main()
