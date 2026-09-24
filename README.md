# 🌿 LeafCare AI: crop disease detection for SDG 2

LeafCare AI is a web app that diagnoses crop diseases from a photo of a leaf. Upload a picture (or take one with
your camera) and the app shows:

- the **crop** and **disease** (or *healthy*), with a colour-coded severity status
- the model's **confidence** and its **top-3** predictions
- a **Grad-CAM heatmap** showing which part of the leaf the model based its decision on
- short, sourced **symptoms / treatment / prevention** advice
- a **Listen** button that reads the diagnosis and treatment aloud in the chosen language (using the browser's built-in voices)
- **Share on WhatsApp** and **Download report** (a one-page HTML report with the photo, heatmap and advice that prints to PDF)
- for visitors in India, the free **Kisan Call Centre** helpline (1800-180-1551) as a tap-to-call card

The interface and advice are available in **9 languages**: English, Hindi, Bengali, Marathi, Telugu, Tamil, Spanish, French and German (`app/locales/`, `data/i18n/`). The translations are machine-generated, and the app says so next to the advice.

It is built with TensorFlow/Keras (EfficientNetB0, transfer learning) and Streamlit.

---

## Problem statement

Plant pests and diseases destroy an estimated **20–40% of global crop production every year**, and plant
diseases alone cost the world economy around **US$220 billion** annually
([FAO](https://www.fao.org/newsroom/detail/New-standards-to-curb-the-global-spread-of-plant-pests-and-diseases/en)).
Smallholder farmers are hit hardest: they often can't get an expert opinion quickly, so diseases are noticed
late, and are often treated with the wrong chemical or too much of it.

## Link to the Sustainable Development Goals

| Goal | How LeafCare AI contributes |
|------|-----------------------------|
| **SDG 2: Zero Hunger**, target **2.4** (sustainable, resilient food production) | Earlier detection means smaller yield losses and more resilient farms. |
| **SDG 12: Responsible Consumption and Production** | Knowing *which* disease is present supports targeted, prevention-first treatment instead of blanket pesticide use. |

## Dataset

**PlantVillage** ([Hughes & Salathé, 2015](https://arxiv.org/abs/1511.08060)), colour images downloaded by the
notebook from the authors' repository ([spMohanty/PlantVillage-Dataset](https://github.com/spMohanty/PlantVillage-Dataset)):
about 54,000 leaf images in **38 classes** covering **14 crops** (apple, blueberry, cherry, corn,
grape, orange, peach, bell pepper, potato, raspberry, soybean, squash, strawberry, tomato), including healthy classes.

- Stratified **80 / 10 / 10** train / validation / test split, random seed 42.
- The class order is saved to `models/class_names.json`.

## Method

| Step | Details |
|------|---------|
| Preprocessing | Resize to 224×224, pixel values kept in 0–255 (EfficientNet rescales internally). One shared function, used by both training and the app, with a test that fails if the two copies differ. |
| Augmentation | Random flip, rotation, zoom, brightness, contrast and a slight random crop. |
| Model | EfficientNetB0 (ImageNet weights) → Global average pooling → Dropout 0.3 → Dense(38, softmax), built as a single flat functional model so Grad-CAM can use the `top_conv` layer. |
| Phase 1 | Backbone frozen, Adam lr 1e-3, ~5 epochs. |
| Phase 2 | Top 30% of the backbone unfrozen (BatchNorm kept frozen), lr 1e-5, ~10 epochs. |
| Regularisation | Early stopping (patience 3, best weights restored), checkpoint on best validation accuracy. |
| Explainability | Grad-CAM on the last convolutional layer. |
| Leaf check | Before diagnosing, the photo's feature vector (the `avg_pool` layer) is compared with the average feature vector of each class's leaves (`models/leaf_centroids.npy`). Below a cosine similarity of 0.35 the app says the photo doesn't look like a leaf (the user can still analyse it). No retraining needed. |
| Knowledge base | `data/diseases.json`: description, symptoms, cause, organic and chemical treatment, prevention and a source (UC IPM, university extension services, Penn State PlantVillage) for all 38 classes. |

## Results

From `notebooks/train_model.ipynb` (also shown on the app's *About the Model* page, from `models/metrics.json`):

| Metric (test set) | Value |
|-------------------|-------|
| Accuracy | 98.0% |
| Macro F1 | 0.974 |
| Test images | 5,431 |

Hardest classes (lowest F1): corn Cercospora / grey leaf spot (0.84), tomato early blight (0.89) and tomato
target spot (0.90). See `reports/figures/confusion_matrix.png` for which classes they are confused with.

Figures saved by the notebook in `reports/figures/`: `training_curves.png`, `confusion_matrix.png`,
`sample_predictions.png`, `gradcam_examples.png`, and `classification_report.csv`. The Grad-CAM figure can also be
redrawn from the trained model alone, without re-running the notebook:

```bash
python scripts/make_gradcam_figure.py       # uses models/leaf_model.keras + app/assets/sample_images/
```

## Screenshots

> Add screenshots after training, e.g. in `docs/screenshots/`, and link them here:
>
> `![Diagnose page](docs/screenshots/diagnose.png)`
> `![Scan history](docs/screenshots/history.png)`
> `![About the model](docs/screenshots/about.png)`

## Limitations

- **Lab-style training photos.** PlantVillage images show single leaves on plain backgrounds, so accuracy on
  real field photos (clutter, multiple leaves, shadows, blur) is lower than the test score.
- **Closed set of classes.** Only the 14 crops and 38 conditions in the dataset are recognised, and the
  classifier itself always picks one of them. It can be confidently wrong on unrelated photos: a selfie was
  diagnosed as tomato late blight at 82%, so a high confidence score alone doesn't prove the photo is a leaf.
  The leaf check catches this. On the images used to set its 0.35 cut-off, it flagged all 31 non-leaf
  photos (faces, animals, objects, a flower) and 0% of PlantVillage leaves, but also 5% of real field photos
  from PlantDoc (flagged photos can still be analysed). With only 31 non-leaf photos tested, other kinds of
  photo could still get past it. The app also warns when confidence is below 60%.
- **Informational only.** Advice is general and is no substitute for an agronomist or local agricultural officer.

---

## Project structure

```
leafcare-ai/
├── app/
│   ├── Home.py                  # entry point: navigation + Diagnose page
│   ├── views/                   # Scan History, About the Model, SDG Impact, Feedback
│   ├── utils/                   # preprocessing, predict, gradcam, ui components
│   └── assets/                  # styles.css, logo.svg, sample_images/
├── .streamlit/config.toml       # theme
├── data/diseases.json           # knowledge base (38 classes)
├── models/                      # leaf_model.keras, class_names.json, metrics.json, leaf_centroids.npy
├── notebooks/train_model.ipynb  # Colab training + evaluation + export
├── reports/figures/             # evaluation figures from the notebook
├── scripts/                     # make_placeholder_model.py, validate_knowledge_base.py, build_leaf_centroids.py,
│                                #   make_gradcam_figure.py
├── tests/                       # pytest tests
└── requirements.txt
```

## Run locally

Requires **Python 3.10–3.12** (TensorFlow doesn't support 3.13+ yet).

```bash
cd leafcare-ai
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/make_placeholder_model.py    # only if models/leaf_model.keras is missing
streamlit run app/Home.py
```

Until the real model is added, the app runs in **demo mode** with an untrained placeholder model (results are
random, and a banner says so).

Checks:

```bash
pytest                                        # preprocessing, prediction, Grad-CAM, knowledge base, app pages
python scripts/validate_knowledge_base.py     # every class has a complete advice entry
```

## Train the model (Google Colab)

1. Open `notebooks/train_model.ipynb` in [Google Colab](https://colab.research.google.com/)
   (*File → Upload notebook*).
2. *Runtime → Change runtime type → T4 GPU*, then *Runtime → Run all*. The first cell installs the pinned
   TensorFlow/Keras versions and restarts once; then *Run all* again. Checkpoints go to Google Drive, so if
   Colab disconnects, *Run all* resumes training.
3. The notebook downloads `leafcare_export.zip`. Delete `app/assets/sample_images/placeholder_*.jpg`, then
   unzip the archive into the project root. It fills `models/`, `reports/figures/` and
   `app/assets/sample_images/`.
4. Run `pytest` and restart the app. The demo-mode banner disappears.

TensorFlow and Keras are pinned to the same versions in `requirements.txt` and in the notebook, so the model
saved in Colab loads locally without version errors.

## Deploy to Streamlit Community Cloud

1. Push the project to a public GitHub repository, **including** `models/leaf_model.keras` (~40 MB),
   `models/class_names.json`, `models/metrics.json`, `models/leaf_centroids.npy` and `reports/figures/`.
2. Go to [share.streamlit.io](https://share.streamlit.io), click **Create app**, and choose the repository.
3. Set **Main file path** to `app/Home.py`. Under *Advanced settings*, choose **Python 3.11**.
4. Click **Deploy**. The first build takes a few minutes because TensorFlow is large.

## Credits

- Dataset: Hughes, D. P., & Salathé, M. (2015). *An open access repository of images on plant health to enable
  the development of mobile disease diagnostics.* arXiv:1511.08060.
- Model: Tan, M., & Le, Q. (2019). *EfficientNet: Rethinking model scaling for convolutional neural networks.*
- Grad-CAM: Selvaraju, R. R. et al. (2017). *Grad-CAM: Visual explanations from deep networks via
  gradient-based localization.*
- Disease information: UC Statewide IPM Program, Ohio State University Extension (Ohioline), NC State Extension,
  Washington State University Tree Fruit, University of Florida IFAS (EDIS), Crop Protection Network, and
  Penn State PlantVillage. Each entry in `data/diseases.json` links to its source.
