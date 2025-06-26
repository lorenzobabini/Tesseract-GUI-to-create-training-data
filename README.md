
## Summary

Due to the laborious and manually intensive process involved in fine-tuning a Tesseract model, this GUI has been developed to easily and quickly create new traning data (Ground Truth) for Tesseract 5 by identifying OCR'd lines, manually correcting any errors, and automatically producing data to be used for training.

ATTENTION: despite the original project I forked, this new version does not cover the entire traninig process (which has to be completed in a Linux environmente following Tesstrain indications) but its sole purpose is to create couple of labeled data (.gt.text and .tif files) as as now prescribed by Tesstrain.

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


## Different Languages

This documentation has covered the fine-tuning of the English-language Tesseract model. To fine-tune a Tesseract model of a different language, simply append `--language <language code>` to **all** Python arguments, including the initial line-box step where no additional arguments need to be provided. `<language code>` **must** match the language code used in the Tesseract traineddata file, e.g. `chi_sim` for simplified Chinese, `chi_tra` for traditional Chinese, `jpn` for Japanese, and so on. For instance, to run the pipeline for the French language, commands can be run like:

`python pipeline.py --language fra`
`python pipeline.py -b --language fra`
`python pipeline.py -p --language fra`

On the file system, all line-box files, post-processing files, models, and so on will be stored in a subdirectory with the language code used in the Python commands. By default, all operations are done on the English model, so corresponding files are stored in the `eng` subdirectory.

## Frequently Asked Questions / Troubleshooting

As this is the initial launch of the Tesseract retraining pipeline, there have not yet been many frequently asked questions or common issues encountered. This section will be updated as time goes on and more use cases or workarounds are needed.

* **What if the page I want to retrain is oriented upside-down or on its side?**

Currently, you will have to manually reorient the page prior to loading it in the line-box file generator. There is a plan to do this automatically in the future, however.

## To Do

* Fully integrate support for the tesserocr library. Currently, support for tesserocr is limited, and as such, `USE_TESSEROCR` is set to `False` by default.
* Add support for auto-orienting pages.
