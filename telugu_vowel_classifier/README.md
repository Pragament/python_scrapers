# Telugu Vowel Classifier

A Convolutional Neural Network (CNN) model trained to classify **6 Telugu vowels** using TensorFlow/Keras.

## 📂 Dataset
- Source: [Telugu 6 Vowel Dataset](https://www.kaggle.com/datasets/syamkakarla/telugu-6-vowel-dataset)
- Classes: `A`, `Aa`, `Ai`, `E`, `Ee`, `U`
- Each class contains **40 validation samples**.

## 🧠 Model
- Framework: **TensorFlow / Keras**
- Architecture: Convolutional Neural Network (CNN)
- Loss: `categorical_crossentropy`
- Optimizer: `adam`
- Metrics: `accuracy`

## 📊 Results
- **Training Accuracy:** 92.97%
- **Validation Accuracy:** 95%

### Classification Report
| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| A     | 0.84      | 0.93   | 0.88     | 40      |
| Aa    | 0.97      | 0.82   | 0.89     | 40      |
| Ai    | 1.00      | 1.00   | 1.00     | 40      |
| E     | 0.95      | 1.00   | 0.98     | 40      |
| Ee    | 0.97      | 0.97   | 0.97     | 40      |
| U     | 0.97      | 0.97   | 0.97     | 40      |

**Overall Accuracy:** 95%  
**Macro Avg F1-Score:** 0.95  

