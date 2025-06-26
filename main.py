import glob
import os
import subprocess
import sys
import argparse
import tkinter as tk
from tkinter.filedialog import askopenfilename
from multiprocessing import freeze_support, set_start_method
from difflib import SequenceMatcher
import pandas as pd
import pytesseract
import tesserocr
from tesserocr import RIL, PSM, OEM, iterate_level
from PIL import Image, ImageDraw, ImageTk
from functools import partial
from time import time
import random

STANDARD_DPI = 500     # This DPI is now largely for OCR interpretation internally, not image conversion
SCALED_DOWN_DPI = 100  # Still used for GUI display scaling

SCALE_FACTOR = STANDARD_DPI / SCALED_DOWN_DPI

GT_OUTPUT_DIR = 'my_gt_files'  # folder to save .gt.txt e .tif files (lines training data)

RUNTIME_ID = str(int(time())) + str(random.randint(-sys.maxsize - 1, sys.maxsize))

TESSDATA_FOLDER = 'tessdata'   #specify where is your tessdata folder, with the OCR model inside

USE_TESSEROCR = True    # I prefer Tesserocr to Pytesseract if installed

USE_MSER_TO_FIND_LEFTOVER_REGIONS = True
LEFTOVER_OCR_REGION_PADDING = 10

pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 500)

GLOBAL_LINE_DATA = []  # CGlobal variables for data passing between Tkinter classes into dictionaries { 'image': PIL_Image, 'text': 'string', 'bbox': {...}, 'line_num': int }


def save_gt_files(line_data, base_filename, output_dir=GT_OUTPUT_DIR):
    """
    It saves the images of the cropped lines (.tif) and the texts (.gt.txt)
    Args:
        line_data (list): list of dictionaries containing 'image', 'text', 'bbox', 'line_num'.
        base_filename (str): base name of the original file (es. "documento").
        output_dir (str): directory to save files in.
    """
    full_output_path = os.path.join(os.getcwd(), output_dir)
    os.makedirs(full_output_path, exist_ok=True)

    print(f"Saving .gt.txt and .tif files to: {full_output_path}")

    for data in line_data:
        line_image = data['image']
        line_text = data['text']
        line_num = data['line_num']

        # Naming convention per Tesseract: basename_linenum.tif / .gt.txt (pagina rimossa)
        gt_filename_base = f"{base_filename}_l{line_num:03d}"
        tif_path = os.path.join(full_output_path, f"{gt_filename_base}.tif")
        gt_txt_path = os.path.join(full_output_path, f"{gt_filename_base}.gt.txt")

        try:
            line_image.save(tif_path, format="TIFF")
            with open(gt_txt_path, 'w', encoding='utf-8') as f:
                f.write(line_text + '\n')  # Add newline at the end as required by Tesseract
        except Exception as e:
            print(f"Error saving files for line {line_num}: {e}")


# --- Tkinter GUI Classes ---

class TkDrawBorders(tk.Toplevel):
    """
    GUI to draw and verify bounding boxes for lines on an image.
    """

    def __init__(self, image_path, **kwargs):
        super().__init__(**kwargs)
        self.title("Draw Borders (Line-based)")
        self.geometry("1200x800")
        self.file_path = image_path  # Now it's an image path

        self.original_image = None  # Stores the original high-res image
        self.display_image = None  # Stores the scaled-down image for display
        self.photo_image = None  # Stores the Tkinter PhotoImage

        self.start_x = None
        self.start_y = None
        self.current_rectangle = None

        self.line_data_for_gt = []  # Will store extracted line data for GT

        self.canvas = tk.Canvas(self, bg="white", cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side="bottom", fill="x")

        self.finish_button = tk.Button(self.button_frame, text="Finish Image", command=self.finish)
        self.finish_button.pack(side="right", padx=5, pady=5)

        self.bind("<Escape>", self.on_escape_key)

        self.load_image_and_ocr()

    def load_image_and_ocr(self):
        print(f"Processing image: {os.path.basename(self.file_path)}")
        try:
            self.original_image = Image.open(self.file_path).convert("RGB")
        except Exception as e:
            print(f"Error opening image {self.file_path}: {e}")
            self.destroy()
            return

        # Calculate display_image and its scale factor
        self.display_image = self.original_image.copy()
        maxsize = (1000, 700)
        self.display_image.thumbnail(maxsize, Image.LANCZOS)

        # This is the ratio of the size of the original image to the size of the displayed image
        # Make sure you don't divide by zero if the image is too small or empty
        if self.display_image.width > 0 and self.display_image.height > 0:
            self.scale_factor_x = self.original_image.width / self.display_image.width
            self.scale_factor_y = self.original_image.height / self.display_image.height
        else:
            self.scale_factor_x = 1.0
            self.scale_factor_y = 1.0
            print("WARNING: Display image has zero dimensions, scaling might be incorrect.")

        self.photo_image = ImageTk.PhotoImage(self.display_image)
        self.canvas.create_image(0, 0, image=self.photo_image, anchor="nw")
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        # Perform OCR to get initial line data
        self.line_data_for_gt = self.ocr_extraction(self.original_image)
        self.draw_bounding_boxes()
        
 def ocr_extraction(self, image_pil):
        """
        Extracts line-level OCR data.
        """
        extracted_lines = []

        global USE_TESSEROCR  # Allows modification if tesserocr fails

        if USE_TESSEROCR:
            try:
                with tesserocr.PyTessBaseAPI(path=TESSDATA_FOLDER, lang=args["language"]) as api:
                    api.SetImage(image_pil)

                    for i, (line_img, line_bbox, _, _) in enumerate(api.GetComponentImages(RIL.TEXTLINE, True)):
                        api.SetRectangle(line_bbox['x'], line_bbox['y'], line_bbox['w'], line_bbox['h'])
                        text = api.GetUTF8Text().strip()

                        if text:
                            extracted_lines.append({
                                'image': line_img,
                                'text': text,
                                'bbox': line_bbox,
                                'line_num': len(extracted_lines)
                            })
            except Exception as e:
                print(f"tesserocr OCR extraction failed: {e}")
                print("Falling back to pytesseract...")
                USE_TESSEROCR = False

        if not USE_TESSEROCR:  # Fallback to pytesseract
            try:
                data = pytesseract.image_to_data(image_pil, lang=args["language"], output_type=pytesseract.Output.DICT)

                for i in range(len(data['level'])):
                    if data['level'][i] == 4:  # Level 4 is for TEXTLINE
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        line_text = data['text'][i].strip()

                        if line_text:
                            cropped_line_img = image_pil.crop((x, y, x + w, y + h))
                            extracted_lines.append({
                                'image': cropped_line_img,
                                'text': line_text,
                                'bbox': {'x': x, 'y': y, 'w': w, 'h': h},
                                'line_num': len(extracted_lines)
                            })
            except Exception as e:
                print(f"pytesseract OCR extraction failed: {e}")
                print("OCR extraction failed completely. No lines will be processed.")
                extracted_lines = []

        return extracted_lines


    def draw_bounding_boxes(self):
        self.canvas.delete("line_box")
        for data in self.line_data_for_gt:
            bbox = data['bbox']
            # Le coordinate in bbox sono già quelle dell'original_image
            # Le scali per la visualizzazione:
            scaled_x1 = bbox['x'] / self.scale_factor_x  # Usa i nuovi fattori
            scaled_y1 = bbox['y'] / self.scale_factor_y  # Usa i nuovi fattori
            scaled_x2 = (bbox['x'] + bbox['w']) / self.scale_factor_x
            scaled_y2 = (bbox['y'] + bbox['h']) / self.scale_factor_y

            self.canvas.create_rectangle(scaled_x1, scaled_y1, scaled_x2, scaled_y2,
                                         outline="blue", tags="line_box")
            self.canvas.create_text(scaled_x1, scaled_y1 - 5, anchor="sw", text=data['text'][:30], fill="red",
                                    tags="line_box")

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_rectangle = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                              outline="red", tags="drawn_box")

    def on_mouse_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.current_rectangle, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        def on_button_release(self, event):
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)

            # Applica i fattori di scala separatamente per X e Y
            orig_x1 = int(min(self.start_x, end_x) * self.scale_factor_x)
            orig_y1 = int(min(self.start_y, end_y) * self.scale_factor_y)
            orig_x2 = int(max(self.start_x, end_x) * self.scale_factor_x)
            orig_y2 = int(max(self.start_y, end_y) * self.scale_factor_y)

            orig_w = orig_x2 - orig_x1
            orig_h = orig_y2 - orig_y1

            print(f"DEBUG: Drawn box (display): {self.start_x},{self.start_y} to {end_x},{end_y}")
            print(f"DEBUG: Drawn box (original scaled): {orig_x1},{orig_y1} w={orig_w} h={orig_h}")

            if orig_w > 0 and orig_h > 0:
                cropped_img = self.original_image.crop((orig_x1, orig_y1, orig_x1 + orig_w, orig_y1 + orig_h))
            ocr_text = ""
            global USE_TESSEROCR
            if USE_TESSEROCR:
                try:
                    with tesserocr.PyTessBaseAPI(path=TESSDATA_FOLDER, lang=args["language"]) as api:
                        api.SetImage(cropped_img)
                        ocr_text = api.GetUTF8Text().strip()
                except Exception:
                    ocr_text = pytesseract.image_to_string(cropped_img, lang=args["language"]).strip()
            else:
                ocr_text = pytesseract.image_to_string(cropped_img, lang=args["language"]).strip()

            new_line_data = {
                'image': cropped_img,
                'text': ocr_text,
                'bbox': {'x': orig_x1, 'y': orig_y1, 'w': orig_w, 'h': orig_h},
                'line_num': len(self.line_data_for_gt)
            }
            self.line_data_for_gt.append(new_line_data)
            self.draw_bounding_boxes()

    def on_escape_key(self, event):
        self.destroy()

    def finish(self):
        global GLOBAL_LINE_DATA
        GLOBAL_LINE_DATA = self.line_data_for_gt
        self.destroy()


class TkVerifyWords(tk.Toplevel):
    """
    GUI to verify and correct extracted line text.
    """

    def __init__(self, line_data, **kwargs):
        super().__init__(**kwargs)
        self.title("Verify Line Text")
        self.geometry("1000x800")

        self.line_data = line_data
        self.current_line_index = 0

        self.canvas = tk.Canvas(self, bg="lightgray")
        self.canvas.pack(side="top", fill="both", expand=True)

        self.text_frame = tk.Frame(self)
        self.text_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        tk.Label(self.text_frame, text="Corrected Text:").pack(side="left")
        self.text_entry = tk.Entry(self.text_frame, width=80)
        self.text_entry.pack(side="left", fill="x", expand=True, padx=5)

        self.nav_frame = tk.Frame(self)
        self.nav_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        self.prev_button = tk.Button(self.nav_frame, text="Previous", command=self.show_previous_line)
        self.prev_button.pack(side="left", padx=5)

        self.next_button = tk.Button(self.nav_frame, text="Next", command=self.show_next_line)
        self.next_button.pack(side="left", padx=5)

        self.save_button = tk.Button(self.nav_frame, text="Save & Finish Image", command=self.finish)
        self.save_button.pack(side="right", padx=5)

        self.display_line()

    def display_line(self):
        if not self.line_data:
            self.canvas.delete(tk.ALL)
            self.text_entry.delete(0, tk.END)
            self.text_entry.insert(0, "No lines to display.")
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")
            self.save_button.config(state="disabled")
            return

        current_line = self.line_data[self.current_line_index]
        cropped_img = current_line['image']

        maxsize = (self.canvas.winfo_width(), self.canvas.winfo_height() - 50)
        if maxsize[0] == 1 and maxsize[1] == 1:
            maxsize = (800, 200)

        display_img = cropped_img.copy()
        display_img.thumbnail(maxsize, Image.LANCZOS)

        self.photo_image = ImageTk.PhotoImage(display_img)
        self.canvas.delete(tk.ALL)
        self.canvas.create_image(self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2, image=self.photo_image,
                                 anchor="center")

        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, current_line['text'])

        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_button.config(state="normal" if self.current_line_index > 0 else "disabled")
        self.next_button.config(state="normal" if self.current_line_index < len(self.line_data) - 1 else "disabled")

    def save_current_line_text(self):
    if self.line_data:
        self.line_data[self.current_line_index]['text'] = self.text_entry.get()

    def show_previous_line(self):
        self.save_current_line_text()
        if self.current_line_index > 0:
            self.current_line_index -= 1
            self.display_line()

    def show_next_line(self):
        self.save_current_line_text()
        if self.current_line_index < len(self.line_data) - 1:
            self.current_line_index += 1
            self.display_line()

    def finish(self):
        self.save_current_line_text()
        global GLOBAL_LINE_DATA
        GLOBAL_LINE_DATA = self.line_data
        self.destroy()


# --- Main Execution Logic ---

def main(args, lang="eng"):
    freeze_support()
    # set_start_method('spawn', force=True) # Commented out, often not needed for macOS/Linux and can cause issues

    input_handler = UserInputHandler()
    input_handler.get_user_input()  # This now prompts for an image file

    if input_handler.kill:
        print("Exiting.")
        sys.exit(0)

    # The file is now an image path
    image_file = os.path.abspath(input_handler.out_dict['file'])

    # Get base filename for GT output naming (no page number in this case)
    base_filename = os.path.splitext(os.path.basename(image_file))[0]

    # --- Workflow based on args ---

    run_gui_workflow = False
    if args["linebox"] or not (args["postprocessing"] or args["unicharset"] or args["lstmf"] or args["retrain"]):
        run_gui_workflow = True

    if run_gui_workflow:
        print("Running GUI for line-based ground truth generation...")

        # Pass image_file directly
        tkgui_draw = TkDrawBorders(image_file)
        tkgui_draw.wait_window()

        if GLOBAL_LINE_DATA:
            tkgui_verify = TkVerifyWords(line_data=GLOBAL_LINE_DATA)
            tkgui_verify.wait_window()

            if GLOBAL_LINE_DATA:
                save_gt_files(GLOBAL_LINE_DATA, base_filename)
                print("Line-based ground truth files (.gt.txt and .tif) generated successfully.")
            else:
                print("No line data available after verification for saving GT files.")
        else:
            print("No line data generated during drawing phase. Skipping verification and GT file saving.")

    if args["unicharset"]:
        print("Generating unicharset file...")
        unicharset_output_path = os.path.join(os.getcwd(), TESSDATA_FOLDER, f"{lang}.unicharset")
        gt_files_pattern = os.path.join(os.getcwd(), GT_OUTPUT_DIR, "*.gt.txt")

        unicharset_extractor_cmd = [
            'unicharset_extractor',
            '--output_unicharset', unicharset_output_path
        ]
        for gt_file in glob.glob(gt_files_pattern):
            unicharset_extractor_cmd.append(gt_file)

        try:
            print(f"Running: {' '.join(unicharset_extractor_cmd)}")
            subprocess.run(unicharset_extractor_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Unicharset generated: {unicharset_output_path}")
        except FileNotFoundError:
            print(
                "Error: 'unicharset_extractor' command not found. Please ensure Tesseract training tools are installed and in your PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error generating unicharset: {e.stderr.decode()}")

    if args["lstmf"]:
        print("Generating LSTMF training and evaluation files...")
        lstmf_output_folder = os.path.join(os.getcwd(), LSTMF_FOLDER)
        os.makedirs(lstmf_output_folder, exist_ok=True)

        gt_tifs = sorted(glob.glob(os.path.join(os.getcwd(), GT_OUTPUT_DIR, "*.tif")))

        list_file_path = os.path.join(lstmf_output_folder, "all_gt_files.txt")
        with open(list_file_path, "w") as f:
            for tif_file in gt_tifs:
                base = os.path.splitext(tif_file)[0]
                gt_txt = base + ".gt.txt"
                if os.path.exists(gt_txt):
                    f.write(f"{base}\n")

        print("LSTMF generation is a complex step usually handled by tesstrain.sh's 'make training'.")
        print(f"Ensure your .gt.txt and .tif files in '{GT_OUTPUT_DIR}' are ready for tesstrain.")

    if args["retrain"]:
        print("Retraining Tesseract model...")
        print("Retraining is a very complex step. This script provides the data preparation.")
        print("You will need to use Tesseract's `lstmtraining` utility or `tesstrain.sh` for actual retraining.")
        print(f"Look for unicharset in '{TESSDATA_FOLDER}' and LSTMF files in '{LSTMF_FOLDER}' if generated.")

    print("Pipeline execution finished.")


class UserInputHandler:
    """Handles image file selection."""

    def __init__(self):
        self.out_dict = {'file': None}  # No 'page' needed now
        self.kill = False

    def get_user_input(self):
        root = tk.Tk()
        root.withdraw()

        file_path = askopenfilename(
            title="Select Image File for OCR",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]  # Accept images
        )

        if not file_path:
            print("No file selected. Exiting.")
            self.kill = True
            return

        self.out_dict['file'] = file_path

        root.destroy()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("-l", "--language", type=str, default="lat_xvi_century15",
                    help="The Tesseract label of the language of the model to retrain")
    ap.add_argument("-b", "--linebox", action="store_true",
                    help="Run the GUI to generate line-based ground truth (.gt.txt and .tif files)")
    ap.add_argument("-p", "--postprocessing", action="store_true", help="Only run the post-processing script suite")
    ap.add_argument("-n", "--unicharset", action="store_true", help="Only run unicharset file generation")
    ap.add_argument("-f", "--lstmf", action="store_true",
                    help="Only generate LSTMF training and evaluation files from the .gt.txt files")
    ap.add_argument("-r", "--retrain", action="store_true",
                    help="Only retrain the Tesseract model from the LSTMF files")
    ap.add_argument("-h", "--help", action="store_true", help="Display detailed help message.")

    args_parsed = ap.parse_args()

    if args_parsed.help:
        ap.print_help()
        print("\nThis script is now modified to accept image files (JPG/PNG) directly as input.")
        print("Use -b to run the GUI to create line-based ground truth (.gt.txt and .tif files).")
        print("Subsequent steps (--unicharset, --lstmf, --retrain) assume these .gt.txt/.tif files as input.")
        sys.exit(0)

    args = vars(args_parsed)

    main(args, lang=args["language"])
