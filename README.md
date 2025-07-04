
## A GUI to easily create a Ground Truth for Tesseract models

This project is a **modified fork** of the "[Tesseract Retraining Pipeline](https://github.com/dshea89/tesseract-retraining-pipeline)" by Daniel Shea. I have changed the code to adapt it to Tesseract 5 and latest training instructions.

Due to the laborious and manually intensive process involved in fine-tuning a Tesseract model, this GUI has been developed to easily and quickly create new traning data (Ground Truth) for Tesseract 5 by identifying OCR'd lines, manually correcting any errors, and automatically producing data to be used for training.

Despite the original project I forked, this new version does not cover the entire traninig process (which has to be completed in a Linux environmente following ![Tesstrain](https://github.com/tesseract-ocr/tesstrain/) indications) but its sole purpose is to create couple of labeled data (.gt.text and .tif files).

Another difference is that this code accepts image files as input and not pdf files.

## Requirements

`requirements.txt` contains the Python dependencies needed to run the script.

Installing Tesserocr library could be problematic, because it requires Tesseracr and Leptonica.
For macOS I suggest typing in the terminal theese commands:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

```
```
brew install tesseract
```

For Windows I suggest the instructions of the [Pypi page of Tesserocr](https://pypi.org/project/tesserocr/), in particular the 'pip' option


## How to easily create Ground Truth data with this GUI

The Tesseract model file that needs to be retrained or fine tuned can be found in your `tessdata` folder where Tesseract is installed, and has the filename format `<lang>.traineddata`

For Windows, this is often `C:\Program Files (x86)\Tesseract-OCR\tessdata`

Copy this file into this repository's `tessdata` directory. For instance, if you want to retrain the Latin-language Tesseract model, then you should copy `lat.traineddata` from the Tesseract installation's `tessdata` folder to the `tessdata` folder in this repository.


### Selecting image

When the script first launches, a dialog will appear asking you to select an image file (.jpg or .png), from which extracting training data.


### Drawing Bounding Boxes

![draw_border_line](https://github.com/user-attachments/assets/b590cfb4-e110-46a9-af63-51292044077a)


When Tesseract has finished reading the image, a window will launch showing bounding boxes drawn around each line that Tesseract identified. In this preview you will see the trascription of each line that you will correst in the next step. You can just click "Finished" and move onto the next step.


### Line Corrections


![verify_line_text](https://github.com/user-attachments/assets/3c0cf9da-3b64-4065-a32a-549da1cd4c84)


The next window is a list of every line that was captured by a bounding box. Each entry contains the cropped subimage from the bounding box along with what Tesseract thinks that subimage says and the text of the image.

You can correct the transcription of the line and move from one line to another by the "Previous" and "Next" button. Only at the end of all corrections you have to click "Save & Finish Image" to create the training data for all the image lines.


### Ground Truth files

All the training data will be saved in "my_gt_files" folder in couple of .gt.txt and .tif with the same name.

![screen-gt](https://github.com/user-attachments/assets/13fa7efa-795f-4f92-a608-1c2fce6c4f99)


## License

This codebase is released under the permissive MIT License. You may use, modify, and distribute the software - including for commercial purposes, provided you retain the copyright and license notice in any copy of the source or substantial portions of it.

## Citation

If you use this software in your work, please cite the original work by Daniel Shea and, if your modifications are relevant to your application, also this modified version. Full citation details are available in the `CITATION.cff` file in this repository; or click to "Cite this repository" button to copy the format you need.
