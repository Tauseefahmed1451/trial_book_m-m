"""Tight-scope Streamlit UI for the workflow system."""

from __future__ import annotations

import requests
import streamlit as st

from app.core.config import get_settings


settings = get_settings()
API_BASE_URL = settings.api_base_url.rstrip("/")

st.set_page_config(page_title="Book Generation System", layout="wide")
st.title("Book Generation System")

tab_dashboard, tab_import, tab_create, tab_review = st.tabs(
    ["Dashboard", "Import Excel", "Create Book", "Review Center"]
)


def _get(path: str) -> requests.Response:
    return requests.get(f"{API_BASE_URL}{path}", timeout=600)


def _post(path: str, **kwargs: object) -> requests.Response:
    return requests.post(f"{API_BASE_URL}{path}", timeout=600, **kwargs)


with tab_dashboard:
    st.subheader("Books")
    response = _get("/books")
    if response.ok:
        books = response.json()
        st.dataframe(books, use_container_width=True)
    else:
        st.error(response.text)

with tab_import:
    st.subheader("Upload Excel")
    uploaded = st.file_uploader("Excel workbook", type=["xlsx"])
    if uploaded is not None and st.button("Import workbook"):
        response = _post(
            "/imports/excel",
            files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
        )
        if response.ok:
            st.success("Import complete")
            st.json(response.json())
        else:
            st.error(response.text)

with tab_create:
    st.subheader("Create a single book")
    with st.form("create-book"):
        title = st.text_input("Title", value="Remote Work for Small Teams: A Practical Guide")
        notes = st.text_area(
            "Notes on outline before",
            value=(
                "Target audience: founders and managers of small teams. Tone: practical and concise. "
                "Include chapters on hiring, communication, productivity, and culture. Keep the book 5 chapters max."
            ),
            height=140,
        )
        audience = st.text_input("Audience", value="Founders and managers of small teams")
        tone = st.text_input("Tone", value="Practical and concise")
        submitted = st.form_submit_button("Create book")
    if submitted:
        payload = {
            "title": title,
            "notes_on_outline_before": notes,
            "audience": audience,
            "tone": tone,
            "language": "English",
            "research_mode": "lightweight",
        }
        response = _post("/books", json=payload)
        if response.ok:
            st.success("Book created")
            st.json(response.json())
        else:
            st.error(response.text)

with tab_review:
    st.subheader("Review workflow")
    books_response = _get("/books")
    if not books_response.ok:
        st.error(books_response.text)
    else:
        books = books_response.json()
        options = {f"{item['title']} ({item['id']})": item["id"] for item in books}
        if not options:
            st.info("No books available yet.")
        else:
            selected_label = st.selectbox("Select book", list(options.keys()))
            book_id = options[selected_label]
            detail_response = _get(f"/books/{book_id}")
            if detail_response.ok:
                detail = detail_response.json()
                st.write({"stage": detail["current_stage"], "status": detail["current_status"]})
                if detail.get("latest_outline"):
                    st.markdown("### Latest outline")
                    st.text_area("Outline", detail["latest_outline"]["content_text"], height=220)
                    with st.form("outline-review"):
                        outline_status = st.selectbox(
                            "Outline decision",
                            ["no_notes_needed", "yes", "no"],
                            key="outline_status",
                        )
                        outline_notes = st.text_area("Outline notes", key="outline_notes")
                        outline_submit = st.form_submit_button("Submit outline review")
                    if outline_submit:
                        response = _post(
                            f"/books/{book_id}/outline/review",
                            json={"review_status": outline_status, "editor_notes": outline_notes or None},
                        )
                        if response.ok:
                            st.success("Outline review submitted")
                            st.rerun()
                        else:
                            st.error(response.text)

                st.markdown("### Chapters")
                for chapter in detail["chapters"]:
                    st.markdown(f"#### Chapter {chapter['chapter_number']}: {chapter['chapter_title']}")
                    latest_version = chapter.get("latest_version")
                    if latest_version:
                        st.text_area(
                            f"Chapter draft {chapter['chapter_number']}",
                            latest_version["content_text"],
                            height=240,
                            key=f"draft-{chapter['id']}",
                        )
                        st.caption(latest_version["summary_text"])
                        with st.form(f"chapter-review-{chapter['id']}"):
                            chapter_status = st.selectbox(
                                "Chapter decision",
                                ["no_notes_needed", "yes", "no"],
                                key=f"status-{chapter['id']}",
                            )
                            chapter_notes = st.text_area("Chapter notes", key=f"notes-{chapter['id']}")
                            chapter_submit = st.form_submit_button("Submit chapter review")
                        if chapter_submit:
                            response = _post(
                                f"/chapters/{chapter['id']}/review",
                                json={"review_status": chapter_status, "editor_notes": chapter_notes or None},
                            )
                            if response.ok:
                                st.success("Chapter review submitted")
                                st.rerun()
                            else:
                                st.error(response.text)
                    else:
                        st.info("Chapter draft has not been generated yet.")

                if detail["current_stage"] == "final_review":
                    if st.button("Compile final draft"):
                        response = _post(f"/books/{book_id}/compile")
                        if response.ok:
                            st.success("Compilation completed")
                            st.json(response.json())
                            st.rerun()
                        else:
                            st.error(response.text)

                if detail["artifacts"]:
                    st.markdown("### Artifacts")
                    for artifact in detail["artifacts"]:
                        st.markdown(
                            f"- [{artifact['file_name']}]({API_BASE_URL}/artifacts/{artifact['id']}/download)"
                        )

                if detail["notifications"]:
                    st.markdown("### Notifications")
                    st.dataframe(detail["notifications"], use_container_width=True)

                if detail["events"]:
                    st.markdown("### Workflow events")
                    st.dataframe(detail["events"], use_container_width=True)
            else:
                st.error(detail_response.text)
