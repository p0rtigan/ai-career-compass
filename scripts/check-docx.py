import zipfile

def test_docx(file_path):
    try:
        with zipfile.ZipFile(file_path, 'r') as docx:
            print("This is a valid .docx file!")
            docx.testzip()  # Check for internal integrity
    except zipfile.BadZipFile:
        print("This is not a valid .docx file!")
    except Exception as e:
        print(f"An error occurred: {e}")

test_docx("../data/sample_resumes/chris_resume.docx")
