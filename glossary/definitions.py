# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.23.3",
#     "pandas>=3.0.5",
# ]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    import marimo as mo
    import pandas as pd
    from pathlib import Path

    return Path, json, mo


@app.cell(hide_code=True)
def _(Path, json, mo):
    JSON_FILE = Path(__file__).resolve().parent / "definitions.json"
    MD_FILE = Path(__file__).resolve().parent.parent / "content/glossary.md"

    if JSON_FILE.exists():
        initial_data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    else:
        initial_data = [
            {
                "term": "Signal",
                "lexical_category": "Noun",
                "definition": "A function that conveys information, typically representing how a quantity varies over time or space.",
            }
        ]
        JSON_FILE.parent.mkdir(parents=True, exist_ok=True)
        JSON_FILE.touch(exist_ok=True)
        JSON_FILE.write_text(json.dumps(initial_data, indent=2), encoding="utf-8")

    get_rows, _set_rows = mo.state(initial_data)

    if not MD_FILE.exists():
        MD_FILE.parent.mkdir(parents=True, exist_ok=True)
        MD_FILE.touch(exist_ok=True)

    # Create a single global helper that updates the state AND the file at the exact same time
    # def save_data(new_list):
    #     sorted_list = sorted(new_list, key=lambda x: x["term"].lower())
    #     JSON_FILE.write_text(json.dumps(sorted_list, indent=2), encoding="utf-8")
        # _set_rows(new_list

    def save_data(new_list):
        sorted_list = sorted(new_list, key=lambda x: x["term"].lower())
    
        JSON_FILE.write_text(json.dumps(sorted_list, indent=2), encoding="utf-8")
    
        md_body = "\n\n".join(
            f'<u>**{r["term"]}**</u>  \n{r["definition"]}' 
            for r in sorted_list
        )
        md_content = f"---\ntitle: Glossary\n---\n{md_body}\n"
        MD_FILE.write_text(md_content, encoding="utf-8")
    
        _set_rows(sorted_list)

    rows = get_rows()

    mo.vstack([
        mo.md(f'''
            <u>**{r["term"]}**</u> *{r["lexical_category"]}*  
            {r["definition"]}  
        ''')
        for r in rows
    ])
    return MD_FILE, get_rows, save_data


@app.cell
def _(MD_FILE):
    MD_FILE
    return


@app.cell(hide_code=True)
def _(get_rows, mo, save_data):
    # jb: eval=false
    form_fields = {
        "term": mo.ui.text(placeholder="Ex. Consciousness"),
        "lexical_category": mo.ui.dropdown(
            [
                "Noun",
                "Verb",
                "Adjective",
                "Adverb",
                "Preposition",
                "Conjunction",
                "Determiner",
                "Pronoun",
                "Interjection",
            ],
            value="Noun",
        ),
        "definition": mo.ui.text_area(
            placeholder="Ex. The existence of qualia."
        ),
    }

    def validate_inputs(form_value):
        if not form_value["term"].strip() or not form_value["definition"].strip():
            #comment for testing
            return "⚠️ Error: Term and Definition fields cannot be empty!"

        return None  # Returning None means the data is valid

    def append_definition(new_data):
        if new_data is not None:
            save_data(get_rows() + [new_data])

    form = mo.ui.form(
        element=mo.ui.dictionary(form_fields),
        submit_button_label="Add Definition",
        validate=validate_inputs,
        on_change=append_definition,
        clear_on_submit=True,
    )

    form
    return


@app.cell(hide_code=True)
def _(get_rows, mo):
    mo.md(f"""
    ```md
    {
        "\n\n".join(
            [
                f'<u>**{r["term"]}**</u>\n{r["definition"]}'
                for r in get_rows()
            ])
    }
    ```
    """)
    return


@app.cell(hide_code=True)
def _(get_rows, mo):
    # jb: eval=false
    table = mo.ui.table(
        data=get_rows(),
        selection="single",
        label="Select row to Edit or Delete:",
    )
    return (table,)


@app.cell(hide_code=True)
def _(get_rows, mo, save_data, table):
    # jb: eval=false
    edit_section = ""
    delete_button = ""

    # table.value returns a list of selected rows when selection="single"
    if len(table.value) > 0:
        # 1. Isolate the row data to a local variable inside this cell block
        active_row = table.value[0]

        # 2. Build the Edit Form Fields
        edit_fields = {
            "term": mo.ui.text(value=active_row["term"], label="Term"),
            "lexical_category": mo.ui.dropdown(
                [
                    "Noun",
                    "Verb",
                    "Adjective",
                    "Adverb",
                    "Preposition",
                    "Conjunction",
                    "Determiner",
                    "Pronoun",
                    "Interjection",
                ],
                value=active_row["lexical_category"],
                label="Category",
            ),
            "definition": mo.ui.text_area(value=active_row["definition"], label="Definition"),
        }

        # 3. Define the update callback
        def save_changes(updated_data):
            if updated_data is not None:
                current_list = list(get_rows())
                for idx, original_row in enumerate(current_list):
                    if (
                        original_row["term"] == active_row["term"]
                        and original_row["definition"] == active_row["definition"]
                    ):
                        current_list[idx] = updated_data
                        break
                save_data(current_list)
                mo.status.toast(
                    title="Updated", description=f"Saved {updated_data['term']}"
                )

        # 4. Define the delete callback
        def handle_delete(_):
            updated_list = [
                row
                for row in get_rows()
                if not (
                    row["term"] == active_row["term"]
                    and row["definition"] == active_row["definition"]
                )
            ]
            save_data(updated_list)
            mo.status.toast(
                title="Deleted", description="Row successfully removed."
            )

        # 5. Construct the UI elements
        edit_form = mo.ui.form(
            element=mo.ui.dictionary(edit_fields),
            submit_button_label="Save Changes",
            on_change=save_changes,
        )

        delete_button = mo.ui.button(
            label=f'🗑️ Delete "{active_row["term"]}"', kind="danger", on_click=handle_delete
        )

        # 6. Assign layout structures to our containers
        edit_section = mo.vstack([mo.md(f'Edit "{active_row["term"]}"'), edit_form])


    # Render the actions side-by-side or stacked cleanly
    mo.vstack([table, delete_button, edit_section], gap=1)
    return


if __name__ == "__main__":
    app.run()
