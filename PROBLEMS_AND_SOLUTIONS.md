# Problems and Solutions: Streamlit E-Commerce App

This document details the main problems encountered during the development and integration of the Streamlit-based e-commerce automation system, and the solutions applied. Each section describes the issue, its cause, and the implemented fix, with technical details and code snippets where relevant.

---

## 1. Playwright NotImplementedError in Streamlit on Windows

**Problem:**
- When running the app with Playwright for scraping, a `NotImplementedError` was raised (from `asyncio` subprocesses) on Windows, especially inside Streamlit.
- This prevented any scraping from working in the Streamlit UI, even though it worked in the console.

**Solution:**
- Refactored all scraping logic to use Selenium (with Chrome WebDriver) instead of Playwright.
- Selenium is fully compatible with Streamlit and Windows.
- Example code for headless Chrome with Selenium:
  ```python
  from selenium import webdriver
  from selenium.webdriver.chrome.options import Options
  options = Options()
  options.add_argument('--headless=new')
  driver = webdriver.Chrome(options=options)
  driver.get(url)
  # ...scraping logic...
  driver.quit()
  ```

---

## 2. Google Drive Authentication Repeatedly Prompting

**Problem:**
- The app asked for Google Drive authentication every time the user interacted with the Streamlit UI (because Streamlit reruns the script on every widget interaction).

**Solution:**
- Used `st.session_state` to store the authenticated Google Drive object and parent folder ID.
- Authentication now only happens once per session:
  ```python
  if 'drive' not in st.session_state:
      st.session_state['drive'] = authenticate_drive()
      st.session_state['parent_folder_id'] = GOOGLE_DRIVE_PARENT_FOLDER_ID
  drive = st.session_state['drive']
  parent_folder_id = st.session_state['parent_folder_id']
  ```

---

## 3. Excel File Not Downloadable from Streamlit

**Problem:**
- The download button for Excel files was not working. The error was due to passing the result of `df.to_excel(index=False, engine='openpyxl')` directly to the `data` argument, which returns `None` if not given a file path or buffer.

**Solution:**
- Used an in-memory buffer (`io.BytesIO`) for the download button:
  ```python
  import io
  excel_buffer = io.BytesIO()
  df.to_excel(excel_buffer, index=False, engine='openpyxl')
  excel_buffer.seek(0)
  st.download_button(
      label="Download Excel",
      data=excel_buffer,
      file_name="product_listing.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  )
  ```

---

## 4. Excel File Not Being Created on Disk

**Problem:**
- Even after fixing the download, the Excel file was not being saved to the `data/` folder as expected.

**Solution:**
- Explicitly wrote the DataFrame to disk after scraping, in all relevant modes:
  ```python
  os.makedirs("data", exist_ok=True)
  df.to_excel("data/product_listing.xlsx", index=False)
  ```
- This ensures the file is always saved to disk, regardless of the download button.

---

## 5. Image/Caption Mismatch in Streamlit

**Problem:**
- When displaying multiple images, Streamlit raised an error if the number of captions did not match the number of images.

**Solution:**
- Added logic to only provide captions if the number matches the images:
  ```python
  if saved_images:
      if len(saved_images) == 1:
          st.image(saved_images[0], caption="Product Image", width=200)
      else:
          captions = [f"Image {i+1}" for i in range(len(saved_images))]
          st.image(saved_images, caption=captions, width=200)
  ```

---

## 6. General Debugging and DataFrame Checks

**Problem:**
- At times, the DataFrame was empty or not being written due to errors earlier in the pipeline.

**Solution:**
- Added debug statements to check DataFrame shape and contents before writing to disk or offering download.
- Used try/except blocks to catch and display errors in Streamlit.

---

## 7. Package Installation Issues

**Problem:**
- Errors like `ModuleNotFoundError: No module named 'selenium'`, `No module named 'together'`, etc.

**Solution:**
- Installed missing packages using pip:
  ```sh
  pip install selenium together pydrive2 playwright openpyxl Pillow
  ```
- Ensured all dependencies are listed in `requirements.txt`.

---

## 8. Windows File Permissions and Working Directory

**Problem:**
- Sometimes, files were not being written due to permissions or unexpected working directory.

**Solution:**
- Used `os.makedirs("data", exist_ok=True)` to ensure the directory exists.
- Added debug output for `os.getcwd()` if needed.

---

## 9. Streamlit Rerun and State Management

**Problem:**
- Streamlit reruns the script from the top on every widget interaction, causing repeated authentication and re-initialization.

**Solution:**
- Used `st.session_state` for all persistent objects (like Google Drive auth, parent folder ID, etc.).

---

## 10. User Input Mode Confusion

**Problem:**
- Users sometimes pasted a product URL in the product name field, causing scraping to fail.

**Solution:**
- Added clear UI separation for modes and provided guidance in the UI for what input is expected in each mode.

---

## Summary

By addressing these issues, the app is now robust, user-friendly, and works reliably on Windows with Streamlit. All major backend and frontend integration issues have been resolved. 