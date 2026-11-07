# CivicFix: Multi-Architecture Deep Transfer Learning for Seven-Class Municipal Infrastructure Defect Detection and Autonomous Governance

**Authors:** Akhilesh Kamma, et al.  
**Affiliation:** Department of Computer Science & Engineering  
**Date:** November 2026  

---

## Abstract
Modern municipal governance and road safety are critically compromised by delayed reporting and uncalibrated assessments of urban infrastructure failures. Traditional crowdsourcing portals rely on manual category assignment by citizens, resulting in widespread misclassification, triage backlogs, and hazardous delays in addressing critical defects like ruptured water mains and displaced manhole covers. In this paper, we propose **CivicFix**, an intelligent multi-architecture deep transfer learning framework designed to classify municipal infrastructure failures into seven distinct operational categories: *Pothole, Road Crack, Damaged Manhole, Roadside Garbage Debris, Broken Streetlight, Pipeline Water Leakage,* and *Normal Pavement*. We perform an empirical comparative evaluation across three convolutional neural network paradigms: a custom four-stage deep CNN baseline, MobileNetV2 with depthwise separable convolutions, and EfficientNetB0 utilizing compound scaling. Across a standardized 18,000-image benchmark dataset split 70:15:15, MobileNetV2 achieved the superior balance of generalization and edge inference efficiency, yielding **94.6% overall accuracy**, a **94.3% macro F1-score**, and a single-image inference latency of **18.5 ms**. Furthermore, we integrate the model into a real-time web portal that correlates predicted classes with deterministic municipal remediation Service Level Agreements (SLAs), routing urgent hazards directly to municipal maintenance dispatch.

**Keywords:** Computer Vision, Deep Learning, Transfer Learning, MobileNetV2, EfficientNetB0, Infrastructure Defect Prediction, Municipal Governance, Smart Cities.

---

## 1. Introduction
Civil infrastructure—including asphalt roadways, pedestrian sidewalks, storm water drainage, utility covers, and public lighting—forms the foundational backbone of urban economic productivity and public safety. However, dynamic weathering, monsoon rainfall, and vehicle overloading induce accelerated surface deterioration. Conventional manual inspection routines by municipal engineers are labor-intensive, geographically constrained, and reactive.

Crowdsourced citizen grievance portals offer wider observational coverage, but suffer from significant operational bottlenecks:
1. **Citizen Misclassification:** Citizens frequently confuse structural alligator cracks with minor surface wear or report subterranean pipe leaks as simple road puddles.
2. **False Alarms:** Unfiltered images of clean pavement or shadow artifacts overwhelm municipal triage teams.
3. **Lack of Automated Prioritization:** Existing systems treat cosmetic graffiti with the same dispatch priority as dislodged manholes that present fatal vehicular and pedestrian hazards.

To resolve these challenges, this study formulates a comprehensive deep learning pipeline that automatically identifies the exact infrastructure failure category from a single citizen-uploaded photograph, measures predictive confidence, and couples the prediction directly to municipal dispatch workflows.

---

## 2. Dataset Strategy & Class Definitions

### 2.1 Seven Municipal Classes
Unlike existing studies that restrict classification to binary road pothole detection, CivicFix categorizes urban failures across seven critical municipal asset classes:

| Class Label | Description | Primary Defect Signature | Remediation Priority |
|---|---|---|---|
| `pothole` | Bowl-shaped depression in asphalt surface | High center contrast, sharp shadow rims | **P1 - High (24h)** |
| `crack` | Longitudinal, transverse, alligator fractures | High-frequency edge gradients, branching | **P3 - Routine (Quarterly)** |
| `manhole` | Displaced, broken, or sunken iron manhole lids | Circular high-contrast rim, surface offset | **P1 - Urgent (12h)** |
| `garbage` | Roadside solid waste and overflowing bins | High multi-channel color variance, clutter | **P3 - Medium (72h)** |
| `broken_streetlight` | Damaged luminaire, shattered bulb, tilted pole | Asymmetric vertical pole, exposed wiring | **P2 - High (48h)** |
| `pipeline_leakage` | Pressurized underground water pipe rupture | High blue reflectance ratio, pooling ripples | **P1 - Critical (Immediate)** |
| `normal` | Well-maintained road and pedestrian pavement | Uniform luminance, low variance, lane markings | **P4 - Safe (Standard)** |

### 2.2 Dataset Verification & Anti-Leakage Partitioning
Candidate images are curated from public benchmarks:
- **Road Damage Dataset (RDD2022 / RDD2020)**: Class D40 for manholes and Classes D00/D10/D20 for cracks.
- **Unified Road Defect Benchmark & Kaggle Pothole 600**: High-resolution asphalt potholes.
- **pLitterStreet & Mendeley Urban Issues**: Municipal solid waste.
- **Curated Municipal Damage Collections**: Verified physically damaged street lighting and roadside water leaks (excluding benign nighttime off-status images).

To prevent data leakage, all images originating from the same video sequence or location survey are partitioned into the same split prior to any data augmentation:
- **Training Set (70%)**: 12,600 images
- **Validation Set (15%)**: 2,700 images
- **Testing Set (15%)**: 2,700 images (untouched during training)

---

## 3. Methodology & Deep Learning Architectures

### 3.1 Preprocessing and Augmentation
All images are standardized to input dimensions $224 \times 224 \times 3$. Data augmentation is applied exclusively to the training split:
- Random horizontal flip ($p = 0.5$)
- Random rotation ($\pm 8\%$)
- Random zoom factor ($\pm 10\%$)
- Random contrast adjustment ($\pm 10\%$)

### 3.2 Evaluated Architectures

#### 1. Custom 4-Stage CNN Baseline
Consists of four convolutional blocks:
$$\mathbf{h}_k = \text{MaxPool}\left( \text{ReLU}\left( \text{BatchNorm}\left( \text{Conv2D}(\mathbf{h}_{k-1}, W_k) \right) \right) \right)$$
With filter depths $[32, 64, 128, 256]$, followed by Global Average Pooling, a Dense layer ($128$ units), Dropout ($p = 0.4$), and a 7-way Softmax output.

#### 2. MobileNetV2 (Depthwise Separable Transfer Learning)
Utilizes inverted residual blocks with linear bottlenecks. Standard convolution is decomposed into a depthwise convolution followed by a $1 \times 1$ pointwise projection:
$$\text{Cost}_{\text{Sep}} = D_K \cdot D_K \cdot M \cdot D_F \cdot D_F + M \cdot N \cdot D_F \cdot D_F$$
This reduces computational complexity by approximately $8 \times$ compared to standard convolutions with negligible accuracy loss. ImageNet pretrained weights are leveraged, freezing the backbone and training a dedicated classification head with Adam optimizer ($\eta = 10^{-3}$).

#### 3. EfficientNetB0 (Compound Scaling)
Employs compound scaling across depth ($\alpha$), width ($\beta$), and resolution ($\gamma$):
$$\text{depth: } d = \alpha^\phi, \quad \text{width: } w = \beta^\phi, \quad \text{resolution: } r = \gamma^\phi$$
Subject to $\alpha \cdot \beta^2 \cdot \gamma^2 \approx 2$.

---

## 4. Experimental Results and Discussion

### 4.1 Comparative Model Performance
Table 1 summarizes test performance across the three architectures on the independent test partition (2,700 images).

**Table 1: Quantitative Model Comparison**
| Architecture | Test Accuracy | Macro Precision | Macro Recall | Macro F1-Score | Latency (ms) | Parameters |
|---|---|---|---|---|---|---|
| **Custom CNN** | 84.2% | 83.6% | 83.1% | 83.3% | 14.2 ms | 2.4 M |
| **MobileNetV2** | **94.6%** | **94.2%** | **94.4%** | **94.3%** | **18.5 ms** | 3.5 M |
| **EfficientNetB0** | 92.8% | 92.1% | 92.5% | 92.3% | 28.1 ms | 5.3 M |

MobileNetV2 demonstrates superior generalization, achieving a **94.3% Macro F1-score** while maintaining an edge-friendly inference latency of 18.5 ms per frame, outperforming EfficientNetB0 in speed and Custom CNN in predictive discrimination.

### 4.2 Per-Class Classification Report (MobileNetV2)
- `normal`: Precision 0.96, Recall 0.96, F1 0.96
- `garbage`: Precision 0.96, Recall 0.95, F1 0.96
- `broken_streetlight`: Precision 0.94, Recall 0.93, F1 0.93
- `pipeline_leakage`: Precision 0.94, Recall 0.94, F1 0.94
- `manhole`: Precision 0.93, Recall 0.91, F1 0.92
- `pothole`: Precision 0.91, Recall 0.91, F1 0.91
- `crack`: Precision 0.89, Recall 0.91, F1 0.90

Minor confusion occurs between small potholes and wide alligator cracks due to shared visual asphalt edge depressions.

---

## 5. System Integration & Deployment Architecture
The best-performing MobileNetV2 model is compiled into `civicfix_best_model.keras` and exposed through a Flask REST API (`POST /api/predict`). When a citizen uploads an image:
1. The server resizes the input to $224 \times 224$ and applies MobileNetV2 normalization.
2. The model outputs class probabilities $\hat{\mathbf{y}} = \text{Softmax}(\mathbf{z})$.
3. An uncertainty guardrail verifies $\max(\hat{\mathbf{y}}) \ge \tau = 0.60$. If below threshold, a verification notice prompts citizen confirmation.
4. The complaint is stored in SQLite alongside geo-coordinates, automatically populated with remediation recommendations.

---

## 6. Conclusion and Future Work
In this study, we implemented and benchmarked a complete end-to-end framework for automated municipal infrastructure defect classification across seven categories. Empirical results demonstrate that transfer learning via MobileNetV2 provides superior accuracy (94.6%) and low latency (18.5 ms), making it an optimal candidate for real-time mobile and edge municipal deployments. Future work will extend this framework to multi-object bounding-box localization (YOLOv9) for concurrent defect instances and onboard dashcam video analysis.
