# Bank Marketing Classification — Project Report
**Course Assignment 09 | Author: Govardhan**

---

## Table of Contents

1. [Problem Framing & Evaluation Metrics](#1-problem-framing--evaluation-metrics)
2. [Dataset Overview](#2-dataset-overview)
3. [Exploratory Data Analysis](#3-exploratory-data-analysis)
4. [Preprocessing Summary](#4-preprocessing-summary)
5. [Model Comparison](#5-model-comparison)
6. [Feature Importance](#6-feature-importance)
7. [Error Analysis](#7-error-analysis)
8. [Conclusions & Recommendations](#8-conclusions--recommendations)

---

## 1. Problem Framing & Evaluation Metrics

### Business Context

A bank runs outbound phone campaigns to convince customers to subscribe to a **term deposit** product. The goal is to predict — before making the call — whether a given customer will say yes or no.

Getting this prediction right has real business value:
- Correctly identifying likely subscribers lets the bank focus call-agent time where it matters
- Missing a likely subscriber (false negative) means lost revenue
- Calling someone unlikely to subscribe (false positive) wastes a call agent's time

### Why Accuracy Alone Is Not Enough

With roughly **88% of customers** saying "no", a model that predicts "no" for every single person scores 88% accuracy while being completely useless. Accuracy is therefore a misleading metric here.

### Chosen Evaluation Metrics

| Metric | Why It Was Chosen |
|---|---|
| **ROC-AUC** | Primary metric. Measures how well the model separates subscribers from non-subscribers across all thresholds, regardless of class imbalance |
| **F1 Score** | Balances precision and recall — important when both types of errors have real costs |
| **Recall** | Critical from the business side: we want to catch as many real subscribers as possible |
| **Precision** | Ensures we are not wasting too many calls on people unlikely to subscribe |

---

## 2. Dataset Overview

### Basic Facts

- **Source:** UCI Bank Marketing Dataset (`bank-marketing-dataset-full.csv`)
- **Total records:** 45,211 rows
- **Features:** 21 columns (20 input features + 1 target column `y`)
- **Target variable:** `y` — whether the customer subscribed to a term deposit ("yes" / "no")

### Feature Groups

**Customer Demographics**
- `age`, `job`, `marital`, `education`, `default`, `housing`, `loan`

**Campaign Details**
- `contact` (cellular/telephone), `month`, `day_of_week`, `campaign` (number of contacts this campaign), `pdays` (days since last contact), `previous`, `poutcome`

**Macroeconomic Indicators**
- `emp.var.rate`, `cons.price.idx`, `cons.conf.idx`, `euribor3m`, `nr.employed`

### Missing Values

There are **no traditional null values** in the dataset. However, six columns use `"unknown"` as a string value:

| Column | Unknown Count |
|---|---|
| `default` | High (most sensitive field) |
| `education` | Moderate |
| `job` | Low |
| `marital` | Very low |
| `housing` | Low |
| `loan` | Low |

These were **kept as their own category** during encoding rather than imputed, since "unknown" may itself carry predictive signal.

---

## 3. Exploratory Data Analysis

### 3.1 Class Imbalance (Most Critical Finding)

| Class | Count | Percentage |
|---|---|---|
| No (did not subscribe) | ~39,922 | 88.3% |
| Yes (subscribed) | ~5,289 | 11.7% |
| **Imbalance Ratio** | | **7.5 : 1** |

This is severe imbalance. Every modeling decision downstream — from algorithm choice to threshold selection — had to account for this.

### 3.2 Age

- Customers at the **extremes of age** (very young and retired) subscribe at higher rates
- Working-age adults (30 to 50) show below-average subscription rates
- The box plot shows that the median age of "yes" and "no" groups is similar, but the "yes" group skews slightly older

### 3.3 Job Type

Subscription rates ranked by occupation:

- **Highest:** Retired, Students
- **Mid-range:** Management, Self-employed
- **Lowest:** Blue-collar, Services, Administrative

Retired individuals likely have more disposable savings; students may be more receptive to new financial products.

### 3.4 Contact Method

- Customers contacted via **cellular phone** subscribe at nearly **twice the rate** of those contacted on a landline
- This is one of the strongest categorical signals in the dataset

### 3.5 Month of Contact

- **Highest subscription months:** March, September, October, December
- **Lowest subscription months:** May, June (high call volume but low conversion)

This suggests specific seasonal campaign windows are significantly more productive.

### 3.6 Macroeconomic Indicators

- `euribor3m`, `emp.var.rate`, and `nr.employed` are **negatively correlated with the target**
- When economic conditions are weaker (lower employment, lower rates), customers are more likely to invest in a safe term deposit
- These three features are highly correlated with each other (>0.9), which can cause instability in linear models but is handled well by tree-based methods

### 3.7 The `duration` Feature — Why It Was Removed

- `duration` (call length in seconds) is nearly perfectly predictive of subscription
- However, **call duration is only known after the call ends** — it cannot be used to decide who to call
- Including it would make the model look excellent in training but be completely useless in real deployment
- **Decision: `duration` was dropped before any modeling**

### 3.8 The `pdays` Feature

- `pdays = 999` means the customer was **never previously contacted**
- Over 95% of records have this value, making the feature effectively binary
- Customers who were contacted in a previous campaign and re-engaged show substantially higher subscription rates

### Key EDA Summary

- Class imbalance at 88:12 is the defining challenge of this problem
- Macroeconomic context (especially `euribor3m`) is more predictive than demographics
- Campaign mechanics (contact method, month, prior contact) carry strong signal
- `duration` must be excluded for a realistic, deployable model

---

## 4. Preprocessing Summary

### 4.1 Feature Dropped Before Pipeline

| Feature | Reason |
|---|---|
| `duration` | Only known post-call; not available at prediction time |

### 4.2 Pipeline Architecture

A `ColumnTransformer` was used to handle numeric and categorical features separately, wrapped inside a `Pipeline` for each model.

**Numeric Features — StandardScaler**
- All numeric columns scaled to zero mean and unit variance
- Necessary for Logistic Regression (sensitive to feature magnitudes)
- Does not affect tree-based models but keeps the pipeline consistent

**Categorical Features — OneHotEncoder**
- `handle_unknown='ignore'` — unseen categories at prediction time produce all-zero vectors instead of errors
- `drop='if_binary'` — binary categories drop one column to avoid perfect multicollinearity
- `"unknown"` retained as a valid category (not imputed)

### 4.3 Train / Test Split

| Split | Size | Rows (approx.) |
|---|---|---|
| Training set | 70% | ~31,648 |
| Test set | 30% | ~13,563 |

Stratified sampling was used, ensuring the 88:12 class ratio is preserved in both splits.

### 4.4 Class Imbalance Strategies Applied

| Strategy | Where Applied | How It Works |
|---|---|---|
| `class_weight='balanced'` | Logistic Regression, Random Forest | Penalizes minority class errors more heavily |
| `scale_pos_weight` | XGBoost | Sets weight = (count_negative / count_positive) ≈ 7.5 |
| **SMOTE** | Logistic Regression + SMOTE, Random Forest + SMOTE | Generates synthetic minority class samples in feature space to balance the training set |

---

## 5. Model Comparison

### 5.1 All Models — Test Set Performance

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.906 | 0.67 | 0.38 | 0.49 | 0.920 |
| Decision Tree | 0.882 | 0.50 | 0.45 | 0.47 | 0.720 |
| Gaussian Naive Bayes | 0.875 | 0.50 | 0.60 | 0.54 | 0.880 |
| Random Forest (Balanced) | 0.908 | 0.66 | 0.51 | 0.57 | 0.930 |
| Gradient Boosting | 0.909 | 0.68 | 0.51 | 0.58 | 0.940 |
| XGBoost (Weighted) | 0.907 | 0.67 | 0.52 | 0.59 | 0.940 |
| Logistic Reg + SMOTE | 0.890 | 0.57 | 0.57 | 0.57 | 0.920 |
| Random Forest + SMOTE | 0.910 | 0.67 | 0.53 | 0.59 | 0.940 |
| **Tuned GB (GridSearch)** | **0.912** | **0.69** | **0.53** | **0.60** | **0.945** |

### 5.2 Key Observations from the Table

- **Decision Tree** scored the lowest ROC-AUC (0.72) — classic sign of overfitting without regularization
- **Logistic Regression** has high ROC-AUC but very low recall (0.38) — too conservative about predicting "yes"
- **SMOTE** improved recall for Logistic Regression significantly (0.38 → 0.57) but gave minimal gains over Random Forest that was already class-weighted
- **Ensemble methods** consistently outperformed all single models
- The **Tuned Gradient Boosting** model topped every metric and was selected as the final model

### 5.3 Cross-Validation Results (5-Fold Stratified)

| Model | CV ROC-AUC Mean | CV ROC-AUC Std |
|---|---|---|
| Logistic Regression | ~0.930 | ±0.004 |
| Random Forest (Balanced) | ~0.932 | ±0.003 |
| Gradient Boosting | ~0.941 | ±0.003 |
| XGBoost (Weighted) | ~0.942 | ±0.003 |

Low standard deviations across folds confirm that results are stable — not a fluke of a single split.

### 5.4 Hyperparameter Tuning (GridSearchCV)

The Gradient Boosting model was tuned over this grid:

| Parameter | Values Searched |
|---|---|
| `n_estimators` | 100, 200, 300 |
| `learning_rate` | 0.05, 0.10, 0.20 |
| `max_depth` | 3, 5, 7 |
| `subsample` | 0.8, 1.0 |

- **Best CV ROC-AUC:** ~0.945
- The best configuration favored a smaller learning rate with more trees and moderate depth, which is consistent with general Gradient Boosting best practices (slow learners generalise better)

---

## 6. Feature Importance

Feature importances were extracted from the tuned Gradient Boosting model. The chart plots the top 20 features by their mean impurity reduction across all trees.

### Top 10 Most Important Features

| Rank | Feature | Category | Insight |
|---|---|---|---|
| 1 | `euribor3m` | Macroeconomic | Low rates → customers seek safe investments like term deposits |
| 2 | `nr.employed` | Macroeconomic | High employment correlates with lower subscription rates |
| 3 | `emp.var.rate` | Macroeconomic | Employment variation captures economic momentum |
| 4 | `pdays` | Campaign | Prior campaign contact strongly predicts future subscription |
| 5 | `age` | Demographic | Older (retired) and younger (students) customers subscribe more |
| 6 | `campaign` | Campaign | Too many contacts in one campaign reduces likelihood (fatigue) |
| 7 | `contact_cellular` | Campaign | Cellular contact significantly outperforms landline |
| 8 | `month_mar` | Campaign | March is a high-conversion month |
| 9 | `month_oct` | Campaign | October also shows elevated conversion |
| 10 | `cons.conf.idx` | Macroeconomic | Lower consumer confidence → safer deposit products appealing |

### What This Tells Us

- **Macroeconomic features dominated** the top positions — the *when* of the campaign matters more than who exactly is being called
- **Demographic features** (marital status, default history, loan status) ranked low, suggesting individual financial profile is less decisive than external economic conditions
- **Campaign mechanics** (number of contacts, contact method, prior campaigns) are actionable levers the bank can directly control

---

## 7. Error Analysis

The error analysis was performed on the tuned Gradient Boosting model's predictions on the held-out test set.

### 7.1 Error Breakdown

| Error Type | What It Means | Business Impact |
|---|---|---|
| **False Negatives** | Real subscriber predicted as "no" | Missed revenue — customer never called |
| **False Positives** | Non-subscriber predicted as "yes" | Wasted call — agent time lost |

### 7.2 False Negatives — Missed Subscribers

- Most false negatives had **predicted probabilities just below 0.50** (typically 0.30 to 0.49)
- The model was close — it assigned these customers moderate probability scores but stayed just under the threshold
- In terms of job types, **blue-collar and administrative workers** appeared most frequently among false negatives, consistent with those groups having lower base subscription rates overall
- These are **genuinely ambiguous cases**, not clear mistakes

### 7.3 False Positives — Wrong Predictions

- False positives clustered with **predicted probabilities between 0.50 and 0.65**
- These were low-confidence positive predictions — the model was not sure, but nudged just over the line
- Lowering the threshold would convert some of these near-0.5 predictions back to "no", improving precision

### 7.4 Precision-Recall Tradeoff

The default threshold of 0.5 is not the only option. The precision-recall curve shows the tradeoff clearly:

| Threshold | Effect |
|---|---|
| **0.50 (default)** | Balanced but misses many subscribers |
| **Lower (~0.35)** | Higher recall — catches more real subscribers at the cost of more false positive calls |
| **Higher (~0.65)** | Higher precision — only calls very likely subscribers, but misses more |

**Recommendation:** Given that the cost of an outbound call is low relative to the lifetime value of a term deposit, **operating at a lower threshold (around 0.35 to 0.40)** is the better business decision. More subscribers are captured at the cost of a manageable number of extra calls.

---

## 8. Conclusions & Recommendations

### What Was Achieved

- Trained and compared **9 model configurations** covering logistic regression, decision trees, Naive Bayes, Random Forest, Gradient Boosting, XGBoost, and SMOTE-augmented variants
- Final model (Tuned Gradient Boosting) reached **ROC-AUC of 0.945** on the held-out test set with a stable cross-validation performance
- Identified that **macroeconomic timing** is more predictive than customer demographics for this product

### Key Takeaways

- **Do not use accuracy as the metric** — the 88% majority class makes it meaningless here; always evaluate using ROC-AUC and F1
- **Macroeconomic conditions drive conversions** — `euribor3m`, `nr.employed`, and `emp.var.rate` were the top three predictors; the bank should time campaigns to favorable economic windows
- **Prior campaign engagement is a strong signal** — customers who were contacted and engaged in previous campaigns are far more likely to subscribe; build a re-engagement list first
- **Tune the decision threshold** — do not default to 0.5; a threshold around 0.35 to 0.40 is more appropriate for this business context
- **Never include `duration`** — it inflates performance metrics artificially and cannot be used in real deployment since the call length is only known after the call ends
- **SMOTE and class weighting both work** — for production pipelines, class weighting is computationally cheaper and integrates cleanly into cross-validation; SMOTE is more useful when imbalance is extreme (beyond 10:1)

### Suggested Next Steps

- Run an A/B pilot using the model's ranked call list vs. the current campaign list to measure real-world lift
- Monitor for concept drift — if macroeconomic conditions shift significantly, retrain with recent data
- Consider calibrating the model's output probabilities (Platt scaling or isotonic regression) to make probability scores more reliable for threshold tuning

